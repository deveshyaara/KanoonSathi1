'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";
        const response = await fetch(`${backendUrl}/documents?limit=5`);
        
        if (!response.ok) {
          throw new Error('Failed to fetch documents');
        }
        
        const data = await response.json();
        setDocuments(data);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-8">KanoonSathi</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-4xl">
        <div className="bg-white shadow-lg rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Start Here</h2>
          <div className="space-y-4">
            <Link
              href="/upload"
              className="block w-full py-3 px-4 text-center bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors"
            >
              Upload Document
            </Link>
          </div>
        </div>

        <div className="bg-white shadow-lg rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">Recent Documents</h2>
          {loading ? (
            <div className="flex justify-center items-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-700"></div>
            </div>
          ) : error ? (
            <div className="text-red-600 py-4">{error}</div>
          ) : documents.length > 0 ? (
            <ul className="space-y-3">
              {documents.map((doc) => (
                <li key={doc._id} className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                  <div className="font-medium">{doc.title}</div>
                  <div className="text-sm text-gray-500">
                    {new Date(doc.created_at).toLocaleString()}
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Language: {
                      doc.language === "en" ? "English" :
                      doc.language === "hi" ? "Hindi" :
                      doc.language === "bn" ? "Bengali" :
                      doc.language === "te" ? "Telugu" :
                      doc.language === "mr" ? "Marathi" :
                      doc.language === "ta" ? "Tamil" :
                      doc.language === "ur" ? "Urdu" :
                      doc.language === "gu" ? "Gujarati" :
                      doc.language === "kn" ? "Kannada" :
                      doc.language === "ml" ? "Malayalam" :
                      doc.language === "or" ? "Odia" :
                      doc.language === "pa" ? "Punjabi" :
                      doc.language === "as" ? "Assamese" :
                      doc.language === "mai" ? "Maithili" :
                      doc.language === "sat" ? "Santali" :
                      doc.language === "ks" ? "Kashmiri" :
                      doc.language === "ne" ? "Nepali" :
                      doc.language === "sd" ? "Sindhi" :
                      doc.language === "kok" ? "Konkani" :
                      doc.language === "doi" ? "Dogri" :
                      doc.language === "mni" ? "Manipuri" :
                      doc.language === "sa" ? "Sanskrit" :
                      doc.language === "bo" ? "Bodo/Tibetan" : doc.language
                    }
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 py-4">No documents uploaded yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}