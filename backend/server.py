"""
FastAPI server for handling document uploads and providing legal AI responses
"""
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import mimetypes
import logging
from pydantic import BaseModel, Field
from pymongo import MongoClient
from bson import ObjectId
import json
from datetime import datetime, UTC
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup with better error handling
try:
    MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ping')
    db = client.kanoonsathi
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Add the parent directory to the path so we can import our module
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.legal_ai import LegalAIAssistant

# Import pytesseract and PIL for OCR
from pytesseract import image_to_string
from PIL import Image

app = FastAPI(title="KanoonSathi API", 
             description="API for processing legal documents and providing insights")

# Add CORS middleware with environment-based origins and proper configuration
ALLOWED_ORIGINS = [
    os.getenv("NEXT_PUBLIC_APP_URL", "http://localhost:3001"),
    os.getenv("NEXT_PUBLIC_BACKEND_URL", "http://localhost:8001"),
    "http://localhost:5173",  # Vite dev server
    "*"  # Allow all origins in development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Initialize the Legal AI Assistant
assistant = LegalAIAssistant()

class DocumentSchema(BaseModel):
    title: str
    content: str
    language: str
    analysis: Optional[dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UploadRequest(BaseModel):
    language: str = Field(..., pattern="^(en|hi|bn|te|mr|ta|ur|gu|kn|ml|or|pa|as|mai|sat|ks|ne|sd|kok|doi|mni|sa|bo)$", description="Supported language codes")

@app.post("/test-document")
async def create_test_document():
    """
    Create a test document for development purposes
    """
    try:
        test_doc = {
            "title": "Test Legal Document",
            "content": "This is a sample legal document for testing purposes. It contains various legal terms and references that will be analyzed by our system.",
            "language": "en",
            "analysis": {
                "summary": "Sample legal document for system testing",
                "entities": [
                    {"word": "legal document", "entity": "DOCUMENT_TYPE"},
                    {"word": "testing", "entity": "PURPOSE"}
                ],
                "confidence_score": 0.95
            },
            "created_at": datetime.utcnow()
        }
        
        inserted_doc = db.documents.insert_one(test_doc)
        test_doc["_id"] = str(inserted_doc.inserted_id)
        return test_doc
    except Exception as e:
        logger.error(f"Error creating test document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    language: str = Form(..., pattern="^(en|hi|bn|te|mr|ta|ur|gu|kn|ml|or|pa|as|mai|sat|ks|ne|sd|kok|doi|mni|sa|bo)$")
):
    try:
        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)
        temp_path = os.path.join("temp", file.filename)
        
        # Read file contents
        contents = await file.read()
        with open(temp_path, "wb") as buffer:
            buffer.write(contents)
            
        # Process the uploaded file
        content = ""
        mime_type, _ = mimetypes.guess_type(temp_path)
        
        # Use OCR for image files
        if mime_type and mime_type.startswith('image/'):
            try:
                with Image.open(temp_path) as img:
                    content = image_to_string(img, lang="eng")
                logger.info(f"OCR extracted text: {content[:100]}...")
            except Exception as e:
                logger.error(f"OCR failed: {e}")
                content = f"Failed to extract text from image: {str(e)}"
        else:
            try:
                with open(temp_path, "r", errors="ignore") as text_file:
                    content = text_file.read()
            except Exception as e:
                logger.error(f"Error reading text file: {e}")
                content = f"Binary content from {file.filename}"
        
        # Process document and get analysis
        result = assistant.process_legal_query(content, language="en")
        
        # Handle translation if needed
        if language != "en":
            try:
                translated = assistant.handle_translation_request(result["summary"], target_lang=language)
                result["translated_text"] = translated["translated_text"]
                result["audio_response"] = translated["audio_response"]
            except Exception as e:
                logger.error(f"Translation failed: {e}")
                result["translated_text"] = result["summary"]
                result["translation_error"] = str(e)
        else:
            result["translated_text"] = result["summary"]

        # Store document in MongoDB
        document = {
            "title": file.filename,
            "content": content,
            "language": language,
            "analysis": result,
            "created_at": datetime.now(UTC)
        }
        
        inserted_doc = db.documents.insert_one(document)
        document_id = str(inserted_doc.inserted_id)
        
        # Include the document ID in the response
        return {
            "document_id": document_id,
            "title": file.filename,
            "language": language,
            "analysis": result,
            "audio_filename": os.path.basename(result.get("audio_response", "")),
            "extracted_text": content[:1000] + "..." if len(content) > 1000 else content
        }
        
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.error(f"Failed to remove temporary file {temp_path}: {e}")

@app.get("/documents")
async def get_documents(limit: int = 10, skip: int = 0):
    """
    Get list of processed documents
    """
    try:
        documents = list(db.documents.find({})
                        .sort("created_at", -1)
                        .skip(skip)
                        .limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document by ID
    """
    try:
        logger.info(f"Received request for document ID: {document_id}")
        
        # Validate ObjectId format
        if not ObjectId.is_valid(document_id):
            logger.error(f"Invalid document ID format: {document_id}")
            raise HTTPException(status_code=400, detail="Invalid document ID format")
            
        logger.info("Looking up document in MongoDB...")
        document = db.documents.find_one({"_id": ObjectId(document_id)})
        
        if not document:
            logger.error(f"Document not found for ID: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Convert ObjectId to string for JSON serialization
        document["_id"] = str(document["_id"])
        logger.info(f"Successfully retrieved document: {document['title']}")
        
        return document
    except Exception as e:
        logger.error(f"Error fetching document: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{filename}")
def get_audio(filename: str):
    """
    Serve audio files
    """
    audio_path = os.path.join("temp", filename)
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        path=audio_path,
        media_type="audio/wav",
        filename=filename
    )

class TodoSchema(BaseModel):
    title: str
    completed: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

@app.get("/api/todos")
async def get_todos():
    """
    Get list of todos
    """
    try:
        todos = list(db.todos.find({}).sort("created_at", -1))
        # Convert ObjectId to string for JSON serialization
        for todo in todos:
            todo["_id"] = str(todo["_id"])
        return todos
    except Exception as e:
        logger.error(f"Error fetching todos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/todos")
async def create_todo(todo: TodoSchema):
    """
    Create a new todo
    """
    try:
        result = db.todos.insert_one(todo.dict())
        created_todo = db.todos.find_one({"_id": result.inserted_id})
        created_todo["_id"] = str(created_todo["_id"])
        return created_todo
    except Exception as e:
        logger.error(f"Error creating todo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)