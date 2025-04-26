import React, { useState } from "react";
import axios, { AxiosError } from "axios";
import { getBackendUrl } from "../utils/shared/environment";
import { useRouter } from "next/navigation";
import Image from "next/image";

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes

interface UploadResponse {
  document_id: string;
  title: string;
  language: string;
  analysis: any;
  audio_filename?: string;
  extracted_text: string;
}

interface UploadFormProps {
  onResponse?: (response: UploadResponse | { error: string }) => void;
}

interface ErrorResponse {
  detail: string;
}

const UploadForm: React.FC<UploadFormProps> = ({ onResponse }) => {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [fileName, setFileName] = useState<string>("");
  const [isAgreed, setIsAgreed] = useState<boolean>(false);
  const [language, setLanguage] = useState<string>("en");
  const [error, setError] = useState<string>("");
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    if (selectedFile) {
      if (!validateFileType(selectedFile)) {
        setError("Invalid file type. Please upload a supported document or image.");
        return;
      }
      if (selectedFile.size > MAX_FILE_SIZE) {
        setError("File size exceeds 10MB limit.");
        return;
      }
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setError("");
    }
  };

  const validateFileType = (file: File): boolean => {
    const allowedTypes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'image/jpeg',
      'image/png',
      'image/tiff',
      'image/bmp',
      'image/gif'
    ];
    return allowedTypes.includes(file.type);
  };

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    
    if (!file || !isAgreed) {
      setError("Please select a file and agree to the terms.");
      return;
    }

    if (!validateFileType(file)) {
      setError("Invalid file type. Please upload a supported document or image.");
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setError("File size exceeds 10MB limit.");
      return;
    }

    try {
      setUploading(true);
      setUploadProgress(0);
      
      const backendUrl = getBackendUrl(true);
      const formData = new FormData();
      formData.append("file", file);
      formData.append("language", language);

      const response = await axios.post(`${backendUrl}/upload`, formData, {
        headers: { 
          "Content-Type": "multipart/form-data",
          'Accept': 'application/json'
        },
        onUploadProgress: (progressEvent) => {
          const total = progressEvent.total || 0;
          if (total > 0) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / total);
            setUploadProgress(percentCompleted);
          }
        }
      });

      if (response.data && response.data.document_id) {
        console.log('Upload successful, document ID:', response.data.document_id);
        // Call onResponse callback if provided
        if (onResponse) {
          onResponse(response.data);
        }
        // Use the router to navigate to results page
        router.push(`/results?id=${response.data.document_id}`);
      } else {
        console.error('No document ID in response:', response.data);
        throw new Error("No document ID received from server");
      }
      
    } catch (err: unknown) {
      console.error("Upload failed:", err);
      const axiosError = err as AxiosError<ErrorResponse>;
      const errorMessage = axiosError.response?.data?.detail || (err as Error).message || "An unexpected error occurred";
      setError(errorMessage);
      if (onResponse) {
        onResponse({ error: errorMessage });
      }
    } finally {
      setUploading(false);
    }
  };

  return (
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

      {/* Progress bar */}
      {uploading && (
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
            style={{ width: `${uploadProgress}%` }}
          />
        </div>
      )}

      <div className="w-full">
        <label htmlFor="language-select" className="block text-sm font-medium text-gray-700 mb-2">
          Select Output Language
        </label>
        <select
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          disabled={uploading}
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

      <div className="flex items-start mt-2">
        <div className="flex items-center h-5">
          <input
            id="terms"
            type="checkbox"
            checked={isAgreed}
            onChange={() => setIsAgreed(!isAgreed)}
            className="w-4 h-4 border border-gray-300 rounded"
            disabled={uploading}
            required
          />
        </div>
        <div className="ml-3 text-sm">
          <label htmlFor="terms" className="text-gray-600">
            I agree that this document will be processed according to the privacy policy
          </label>
        </div>
      </div>
      
      <button
        type="submit"
        disabled={!file || !isAgreed || uploading}
        className={`mt-4 py-3 px-6 font-medium border-0 rounded-md transition-colors
          ${(!file || !isAgreed || uploading) 
            ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-700 text-white'}`}
      >
        {uploading ? `Uploading... ${uploadProgress}%` : "Upload & Translate"}
      </button>
    </form>
  );
};

export default UploadForm;
