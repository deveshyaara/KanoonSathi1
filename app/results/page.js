'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getBackendUrl } from '@/utils/shared/environment';
import { useSearchParams } from 'next/navigation';

// Animated letter component for the header
const AnimatedLetter = ({ letter, index }) => {
  return (
    <span 
      className="inline-block transition-all duration-300 hover:transform hover:scale-125 hover:text-purple-600"
      style={{
        animationDelay: `${index * 0.1}s`,
        animationName: 'bounce',
        animationDuration: '1s',
        animationIterationCount: 'infinite',
        animationDirection: 'alternate',
      }}
    >
      {letter}
    </span>
  );
};

export default function ResultsPage() {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const searchParams = useSearchParams();

  // Animate the app name
  const appName = "KanoonSathi";
  
  useEffect(() => {
    const fetchResult = async () => {
      try {
        const documentId = searchParams.get('id');
        
        if (!documentId) {
          throw new Error('No document ID provided');
        }

        console.log('Fetching document with ID:', documentId);
        const backendUrl = getBackendUrl(true);
        console.log('Using backend URL:', backendUrl);
        
        // Make sure we don't have trailing slashes before adding path
        const endpoint = `${backendUrl.replace(/\/+$/, '')}/documents/${documentId}`;
        console.log('Full endpoint:', endpoint);

        const response = await fetch(endpoint, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });

        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries([...response.headers.entries()]));
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to fetch results: ${response.status} ${response.statusText}`);
        }

        // Handle the response more carefully
        let data;
        try {
          const text = await response.text();
          console.log('Response text preview:', text.substring(0, 200));
          data = JSON.parse(text);
        } catch (parseError) {
          console.error('Error parsing JSON:', parseError);
          throw new Error(`Invalid response format: ${parseError.message}`);
        }
        
        console.log('Received document data:', data);
        
        if (!data) {
          throw new Error('No document data received');
        }
        
        // Add debugging for document and analysis properties
        console.log('Document properties:', Object.keys(data));
        if (data.analysis) {
          console.log('Analysis properties:', Object.keys(data.analysis));
        }
        
        setDocument(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching results:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    const documentId = searchParams.get('id');
    console.log('Document ID from URL:', documentId);
    
    if (documentId) {
      fetchResult();
    } else {
      setLoading(false);
      setError('No document ID provided in URL');
    }
  }, [searchParams]);

  // Background styles with purple and yellow gradient
  const backgroundStyle = {
    background: 'linear-gradient(135deg, #6b46c1 0%, #9f7aea 50%, #fbd38d 100%)',
    minHeight: '100vh',
  };

  if (loading) {
    return (
      <div style={backgroundStyle} className="flex flex-col items-center justify-center min-h-screen p-8">
        {/* Animated Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold text-white mb-2">
            {appName.split('').map((letter, index) => (
              <AnimatedLetter key={index} letter={letter} index={index} />
            ))}
          </h1>
          <p className="text-yellow-100 text-lg">Your Intelligent Legal Document Assistant</p>
        </div>
        
        <div className="w-full max-w-2xl">
          <div className="flex justify-center items-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-yellow-300 border-t-transparent"></div>
          </div>
          <p className="text-center text-white">Loading document analysis...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={backgroundStyle} className="flex flex-col items-center justify-center min-h-screen p-8">
        {/* Animated Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold text-white mb-2">
            {appName.split('').map((letter, index) => (
              <AnimatedLetter key={index} letter={letter} index={index} />
            ))}
          </h1>
          <p className="text-yellow-100 text-lg">Your Intelligent Legal Document Assistant</p>
        </div>
        
        <div className="w-full max-w-2xl bg-white/90 shadow-lg rounded-lg p-6 backdrop-blur-sm">
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
          <div className="mt-4">
            <Link href="/upload" className="text-blue-600 hover:text-blue-800">
              ← Back to Upload
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div style={backgroundStyle} className="flex flex-col items-center justify-center min-h-screen p-8">
        {/* Animated Header */}
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-extrabold text-white mb-2">
            {appName.split('').map((letter, index) => (
              <AnimatedLetter key={index} letter={letter} index={index} />
            ))}
          </h1>
          <p className="text-yellow-100 text-lg">Your Intelligent Legal Document Assistant</p>
        </div>
        
        <div className="w-full max-w-2xl bg-white/90 shadow-lg rounded-lg p-6 backdrop-blur-sm">
          <p className="text-center text-gray-600">No document found</p>
          <div className="mt-4 text-center">
            <Link href="/upload" className="text-blue-600 hover:text-blue-800">
              ← Back to Upload
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={backgroundStyle} className="flex flex-col items-center justify-center min-h-screen p-8">
      {/* Animated Header */}
      <div className="mb-8 text-center">
        <h1 className="text-4xl font-extrabold text-white mb-2">
          {appName.split('').map((letter, index) => (
            <AnimatedLetter key={index} letter={letter} index={index} />
          ))}
        </h1>
        <p className="text-yellow-100 text-lg">Your Intelligent Legal Document Assistant</p>
      </div>
      
      <div className="w-full max-w-2xl bg-white/90 shadow-lg rounded-lg p-6 backdrop-blur-sm mb-8">
        <h1 className="text-2xl font-bold mb-6 text-purple-800">Document Analysis Results</h1>
        
        {/* Document Title */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold text-gray-800">{document.title}</h2>
          <p className="text-sm text-gray-500">
            Uploaded on {new Date(document.created_at).toLocaleString()}
          </p>
        </div>

        {/* Original Content with Translation Hover Feature */}
        {document.content && (
          <div className="mb-6 relative">
            <h3 className="font-medium text-lg mb-2 text-purple-700">
              Original Content:
              {document.language !== 'en' && document.analysis?.translated_text && (
                <span 
                  className="ml-2 text-sm text-purple-500 cursor-pointer hover:text-purple-700"
                  onClick={() => setShowTranslation(!showTranslation)}
                >
                  {showTranslation ? "Hide Translation" : "Show Translation"}
                </span>
              )}
            </h3>
            <div 
              className={`relative transition-all duration-300 ${showTranslation ? 'transform -translate-y-2 opacity-60' : ''}`}
              onMouseEnter={() => document.language !== 'en' && document.analysis?.translated_text && setShowTranslation(true)}
              onMouseLeave={() => setShowTranslation(false)}
            >
              <div className="p-4 bg-purple-50 rounded-lg max-h-60 overflow-y-auto">
                <p className="text-sm text-gray-600 whitespace-pre-line">{document.content}</p>
              </div>
            </div>
            
            {/* Hovering Translation Box */}
            {document.language !== 'en' && document.analysis?.translated_text && (
              <div 
                className={`absolute top-0 left-0 w-full z-10 transition-all duration-300 ${
                  showTranslation 
                    ? 'opacity-100 transform translate-y-0' 
                    : 'opacity-0 pointer-events-none transform translate-y-4'
                }`}
              >
                <div className="p-4 bg-white border border-purple-200 rounded-lg shadow-lg">
                  <h4 className="font-medium text-sm mb-2 text-purple-700">Translated Content:</h4>
                  <p className="text-sm text-gray-700 whitespace-pre-line">{document.analysis.translated_text}</p>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Analysis Results */}
        {document.analysis && (
          <>
            {/* Summary */}
            <div className="mb-6">
              <h3 className="font-medium text-lg mb-2 text-purple-700">Summary:</h3>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-gray-700 whitespace-pre-line">{document.analysis.summary}</p>
              </div>
            </div>

            {/* Translated Text */}
            {document.analysis.translated_text && document.language !== 'en' && (
              <div className="mb-6">
                <h3 className="font-medium text-lg mb-2 text-purple-700">Translated Version:</h3>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <p className="text-gray-700 whitespace-pre-line">{document.analysis.translated_text}</p>
                </div>
              </div>
            )}

            {/* Rest of the content remains unchanged */}
            {/* Entities */}
            {document.analysis.entities && document.analysis.entities.length > 0 && (
              <div className="mb-6">
                <h3 className="font-medium text-lg mb-2 text-purple-700">Identified Entities:</h3>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <ul className="list-disc pl-5 space-y-1">
                    {document.analysis.entities.map((entity, index) => (
                      <li key={index} className="text-gray-700">
                        <span className="font-medium">{entity.word}</span>{' '}
                        <span className="text-gray-500">({entity.entity})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Audio Player */}
            {document.analysis.audio_response && (
              <div className="mb-6">
                <h3 className="font-medium text-lg mb-2 text-purple-700">Audio Summary:</h3>
                <div className="p-4 bg-purple-50 rounded-lg">
                  <audio controls className="w-full">
                    <source 
                      src={`${getBackendUrl(true)}/audio/${document.analysis.audio_response.split('/').pop()}`} 
                      type="audio/wav" 
                    />
                    Your browser does not support the audio element.
                  </audio>
                </div>
              </div>
            )}
          </>
        )}

        {/* Footer Info */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              <span className="mr-4">
                Language: {
                  document.language === 'en' ? 'English' :
                  document.language === 'hi' ? 'Hindi' :
                  document.language === 'bn' ? 'Bengali' :
                  document.language === 'te' ? 'Telugu' :
                  document.language === 'mr' ? 'Marathi' :
                  document.language === 'ta' ? 'Tamil' :
                  document.language === 'ur' ? 'Urdu' :
                  document.language === 'gu' ? 'Gujarati' :
                  document.language === 'kn' ? 'Kannada' :
                  document.language === 'ml' ? 'Malayalam' :
                  document.language === 'or' ? 'Odia' :
                  document.language === 'pa' ? 'Punjabi' :
                  document.language === 'as' ? 'Assamese' :
                  document.language === 'mai' ? 'Maithili' :
                  document.language === 'sat' ? 'Santali' :
                  document.language === 'ks' ? 'Kashmiri' :
                  document.language === 'ne' ? 'Nepali' :
                  document.language === 'sd' ? 'Sindhi' :
                  document.language === 'kok' ? 'Konkani' :
                  document.language === 'doi' ? 'Dogri' :
                  document.language === 'mni' ? 'Manipuri' :
                  document.language === 'sa' ? 'Sanskrit' :
                  document.language === 'bo' ? 'Bodo/Tibetan' :
                  document.language
                }
              </span>
              {document.analysis?.confidence_score && (
                <span>
                  Confidence: {(document.analysis.confidence_score * 100).toFixed(1)}%
                </span>
              )}
            </div>
            <Link href="/upload" className="text-blue-600 hover:text-blue-800">
              ← Back to Upload
            </Link>
          </div>
        </div>
      </div>
      
      {/* How it works and benefits section */}
      <div className="w-full max-w-2xl bg-white/90 shadow-lg rounded-lg p-6 backdrop-blur-sm">
        <h2 className="text-2xl font-bold mb-4 text-purple-800 text-center">How KanoonSathi Works</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-medium text-lg mb-2 text-purple-700">Upload & Process</h3>
            <p className="text-gray-700">Upload any legal document in different formats. Our AI will process and extract key information.</p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-medium text-lg mb-2 text-purple-700">Analyze & Summarize</h3>
            <p className="text-gray-700">The system analyzes the document content, identifies important legal entities, and generates a concise summary.</p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-medium text-lg mb-2 text-purple-700">Translate</h3>
            <p className="text-gray-700">Get the document translated to multiple Indian languages including Hindi, Kannada, Tamil, and more.</p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-medium text-lg mb-2 text-purple-700">Audio Support</h3>
            <p className="text-gray-700">Listen to the summary with our audio feature, making the content accessible to everyone.</p>
          </div>
        </div>
        
        <h2 className="text-2xl font-bold mb-4 text-purple-800 text-center">Benefits</h2>
        
        <ul className="list-disc pl-6 space-y-2 mb-4">
          <li className="text-gray-700"><span className="font-medium text-purple-700">Accessibility:</span> Makes legal documents understandable for everyone regardless of language barriers</li>
          <li className="text-gray-700"><span className="font-medium text-purple-700">Time-saving:</span> Quickly extract key information without reading lengthy documents</li>
          <li className="text-gray-700"><span className="font-medium text-purple-700">Accuracy:</span> AI-powered analysis identifies crucial legal entities and concepts</li>
          <li className="text-gray-700"><span className="font-medium text-purple-700">Multilingual:</span> Support for 22 Indian languages makes legal information accessible to a wider audience</li>
          <li className="text-gray-700"><span className="font-medium text-purple-700">Audio Support:</span> Listen to documents for better accessibility and on-the-go usage</li>
        </ul>
        
        <div className="text-center mt-6">
          <Link 
            href="/upload" 
            className="inline-block px-6 py-3 bg-purple-600 text-white font-medium rounded-lg shadow-md hover:bg-purple-700 transition-colors"
          >
            Try It Now
          </Link>
        </div>
      </div>
    </div>
  );
}