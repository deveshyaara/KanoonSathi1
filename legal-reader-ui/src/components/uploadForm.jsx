import React, { useState } from "react";
import axios from "axios";
import { getBackendUrl } from "../utils/shared/environment";

const UploadForm = ({ onResponse }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [fileName, setFileName] = useState("");
  const [isAgreed, setIsAgreed] = useState(false);
  const [language, setLanguage] = useState("en"); // Default language is English
  const [errorMessage, setErrorMessage] = useState("");

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFileName(selectedFile.name);
      setErrorMessage(""); // Clear any previous errors
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file || !isAgreed) {
      alert("Please select a file and agree to the terms.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language); // Send language preference to backend

    try {
      setUploading(true);
      setErrorMessage("");
      
      // Get backend URL using our shared utility (false = Vite environment)
      const backendUrl = getBackendUrl(false);
      const res = await axios.post(`${backendUrl}/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      onResponse(res.data); // Pass data back to parent
      console.log("Upload successful:", res.data);
    } catch (err) {
      console.error("Upload failed:", err);
      setErrorMessage(err.response?.data?.detail || err.message || "Upload failed");
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
            <img 
              src="/icons/upload-icon.png" 
              alt="Upload" 
              className="h-10 w-10 mb-3" 
            />
            <span className="font-medium text-gray-600">{fileName || "Click to upload document or image"}</span>
            <span className="text-xs text-gray-500 mt-1">PDF, DOC, DOCX, TXT, JPG, PNG, etc. up to 10MB</span>
          </div>
        </label>
      </div>

      {/* Language selection dropdown */}
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

      {/* Error message display */}
      {errorMessage && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{errorMessage}</p>
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
        className={`boxy-button mt-4 py-3 px-6 mx-auto w-3/5 font-medium border-0 
        ${(!file || !isAgreed || uploading) 
          ? 'bg-gray-400 text-gray-200 cursor-not-allowed' 
          : 'upload-button bg-gradient-to-r from-blue-500 to-blue-700 text-white hover:from-blue-600 hover:to-blue-800'}`}
      >
        {uploading ? "Uploading..." : "Upload & Translate"}
      </button>
    </form>
  );
};

export default UploadForm;