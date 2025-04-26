'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [isAgreed, setIsAgreed] = useState(false);
  const [language, setLanguage] = useState("en");
  const [error, setError] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError("");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    setError("");
    setProcessingStatus("");
    
    if (!file || !isAgreed) {
      setError("Please select a file and agree to the terms.");
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      setProcessingStatus("Uploading file...");
      
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";
      const formData = new FormData();
      formData.append("file", file);
      formData.append("language", language);

      const response = await fetch(`${backendUrl}/upload`, {
        method: "POST",
        body: formData,
        headers: {
          'Accept': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail || 
          `Upload failed with status ${response.status}: ${response.statusText}`
        );
      }

      setProcessingStatus("Processing document...");
      const analysisResult = await response.json();
      
      if (analysisResult.error) {
        throw new Error(analysisResult.error);
      }

      // Reset form
      setFile(null);
      setFileName("");
      setUploadProgress(0);
      
      // Redirect to results page
      const resultsUrl = `/results?id=${analysisResult.document_id}`;
      window.location.href = resultsUrl;
      
    } catch (err) {
      console.error("Upload failed:", err);
      setError(err.message || "An unexpected error occurred. Please try again later.");
    } finally {
      setUploading(false);
      setProcessingStatus("");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="w-full max-w-md bg-white shadow-lg rounded-lg p-6 mb-6">
        <h1 className="text-2xl font-bold mb-6">Upload Legal Document</h1>
        
        <form onSubmit={handleUpload} className="flex flex-col gap-6">
          <div className="flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-lg p-6 bg-gray-50 hover:bg-gray-100 transition cursor-pointer">
            <input 
              type="file" 
              id="document-upload" 
              className="hidden" 
              accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png,.tiff,.bmp,.gif"
              onChange={handleFileChange}
            />
            <label htmlFor="document-upload" className="flex flex-col items-center cursor-pointer w-full">
              <div className="flex flex-col items-center justify-center">
                <Image 
                  src="/icons/upload-icon.png" 
                  alt="Upload" 
                  width={48} 
                  height={48} 
                  className="mb-3" 
                />
                <span className="font-medium text-gray-600">{fileName || "Click to upload document or image"}</span>
                <span className="text-xs text-gray-500 mt-1">PDF, DOC, DOCX, TXT, JPG, PNG, etc. up to 10MB</span>
              </div>
            </label>
          </div>

          <div className="w-full">
            <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 mb-2">
              Select Output Language
            </label>
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="en">English</option>
              <option value="hi">Hindi</option>
              <option value="bn">Bengali</option>
              <option value="te">Telugu</option>
              <option value="mr">Marathi</option>
              <option value="ta">Tamil</option>
              <option value="ur">Urdu</option>
              <option value="gu">Gujarati</option>
              <option value="kn">Kannada</option>
              <option value="ml">Malayalam</option>
              <option value="or">Odia</option>
              <option value="pa">Punjabi</option>
              <option value="as">Assamese</option>
              <option value="mai">Maithili</option>
              <option value="sat">Santali</option>
              <option value="ks">Kashmiri</option>
              <option value="ne">Nepali</option>
              <option value="sd">Sindhi</option>
              <option value="kok">Konkani</option>
              <option value="doi">Dogri</option>
              <option value="mni">Manipuri</option>
              <option value="sa">Sanskrit</option>
              <option value="bo">Bodo/Tibetan</option>
            </select>
          </div>

          <div className="flex items-start mt-2">
            <div className="flex items-center h-5">
              <input
                id="terms"
                type="checkbox"
                checked={isAgreed}
                onChange={() => setIsAgreed(!isAgreed)}
                className="w-4 h-4 border border-gray-300 rounded"
                required
              />
            </div>
            <div className="ml-3 text-sm">
              <label htmlFor="terms" className="text-gray-600">
                I agree that this document will be processed according to the privacy policy
              </label>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {processingStatus && (
            <div className="text-sm text-blue-600 animate-pulse">
              {processingStatus}
            </div>
          )}

          <button
            type="submit"
            disabled={!file || !isAgreed || uploading}
            className={`mt-4 py-3 px-6 font-medium border-0 rounded-md transition-colors
              ${(!file || !isAgreed || uploading) 
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
          >
            {uploading ? "Uploading..." : "Upload & Translate"}
          </button>

          <div className="mt-4">
            <Link href="/" className="text-blue-600 hover:text-blue-800">
              ← Back to Home
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}