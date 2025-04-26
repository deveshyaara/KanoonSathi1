import React, { useEffect, useState } from 'react';
import { getBackendUrl } from '../utils/shared/environment';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const MongoDBDemo = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    async function fetchData() {
      try {
        setIsLoading(true);
        setError(null);
        
        const backendUrl = getBackendUrl(false);
        const response = await axios.get(`${backendUrl}/documents`, {
          params: {
            limit: 10 // Fetch more documents
          },
          headers: {
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        setData(response.data);
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load documents');
      } finally {
        setIsLoading(false);
      }
    }

    fetchData();
  }, []);

  const getLanguageDisplay = (langCode) => {
    const languages = {
      'en': 'English',
      'hi': 'Hindi',
      'bn': 'Bengali',
      'te': 'Telugu',
      'mr': 'Marathi',
      'ta': 'Tamil',
      'ur': 'Urdu',
      'gu': 'Gujarati',
      'kn': 'Kannada',
      'ml': 'Malayalam',
      'or': 'Odia',
      'pa': 'Punjabi',
      'as': 'Assamese',
      'mai': 'Maithili',
      'sat': 'Santali',
      'ks': 'Kashmiri',
      'ne': 'Nepali',
      'sd': 'Sindhi',
      'kok': 'Konkani',
      'doi': 'Dogri',
      'mni': 'Manipuri',
      'sa': 'Sanskrit',
      'bo': 'Bodo/Tibetan'
    };
    return languages[langCode] || langCode;
  };

  const handleDocumentClick = (docId) => {
    navigate(`/results?id=${docId}`);
  };

  return (
    <div className="glossy-card p-6 my-6 w-full max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6">Recent Documents</h2>
      
      {isLoading && (
        <div className="flex justify-center items-center my-8">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 text-red-700 p-4 my-4 rounded-r-lg" role="alert">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      )}

      {data && data.length > 0 && (
        <div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {data.map((doc) => (
              <div 
                key={doc._id} 
                onClick={() => handleDocumentClick(doc._id)}
                className="bg-white p-6 rounded-xl shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer border border-gray-100"
              >
                <h3 className="font-semibold text-xl text-gray-800 mb-3">{doc.title}</h3>
                <div className="space-y-2">
                  <div className="flex items-center text-sm text-gray-600">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                    </svg>
                    <span>Language: {getLanguageDisplay(doc.language)}</span>
                  </div>
                  
                  <div className="flex items-center text-sm text-gray-600">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>{new Date(doc.created_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}</span>
                  </div>

                  {doc.analysis && (
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <p className="font-medium text-gray-700 mb-2">Summary:</p>
                      <p className="text-gray-600 text-sm line-clamp-3">{doc.analysis.summary}</p>
                      {doc.analysis.translated_text && doc.language !== 'en' && (
                        <p className="text-gray-600 text-sm mt-2 line-clamp-3">
                          {doc.analysis.translated_text}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!isLoading && !error && (!data || data.length === 0) && (
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="mt-4 text-gray-500 text-lg">No documents available. Upload one to get started!</p>
        </div>
      )}
    </div>
  );
};

export default MongoDBDemo;