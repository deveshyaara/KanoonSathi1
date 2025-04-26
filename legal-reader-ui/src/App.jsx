import React, { useState } from "react";
import { Routes, Route, Link, Navigate } from "react-router-dom";
import { SignedIn, SignedOut, RedirectToSignIn, UserButton } from "@clerk/clerk-react";
import UploadForm from "./components/uploadForm"; 
import MongoDBDemo from "./components/MongoDBDemo";
import { getBackendUrl } from "./utils/shared/environment";

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="flex items-center p-4 h-16 border-b">
        <div className="flex-1">
          <nav className="flex items-center gap-4">
            <Link to="/" className="boxy-button py-2 px-4 font-medium bg-gradient-to-r from-blue-500 to-blue-600 text-white hover:from-blue-600 hover:to-blue-700">
              Home
            </Link>
            <Link to="/documents" className="py-2 px-4 font-medium text-gray-600 hover:text-blue-600 transition-colors">
              Documents
            </Link>
          </nav>
        </div>
        
        <div className="flex-1 flex justify-center">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-500 to-blue-500 bg-clip-text text-transparent hover:from-purple-600 hover:to-blue-600 transition-all duration-300 py-2 px-4 rounded-lg shadow-md bg-gray-50">
            KanoonSathi
          </h1>
        </div>
        
        <div className="flex-1 flex justify-end items-center gap-4">
          <SignedIn>
            <UserButton afterSignOutUrl="/"/>
          </SignedIn>
          <SignedOut>
            <Link to="/sign-in" className="text-blue-600 hover:text-blue-800">Sign In</Link>
          </SignedOut>
        </div>
      </header>
      <main className="flex-grow">
        {children}
      </main>
      <footer className="bg-gray-100 p-6 border-t">
        <div className="max-w-7xl mx-auto">
          <div className="text-center">
            <h3 className="text-lg font-semibold mb-2">About KanoonSathi</h3>
            <p className="text-gray-600">
              KanoonSathi is your AI-powered legal companion, designed to help you understand legal documents, 
              provide summaries, and make legal information more accessible in multiple languages.
            </p>
            <p className="text-gray-500 mt-4 text-sm">
              © {new Date().getFullYear()} KanoonSathi. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Home() {
  const [result, setResult] = useState(null);
  const [redirectToResults, setRedirectToResults] = useState(null);

  const handleResponse = (data) => {
    setResult(data);
    if (data && data.document_id) {
      setRedirectToResults(data.document_id);
    }
  };

  if (redirectToResults) {
    return <Navigate to={`/results?id=${redirectToResults}`} replace />;
  }

  return (
    <div className="min-h-full flex flex-col items-center justify-center p-8">
      <div className="glossy-card p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold mb-8 text-center">Upload Legal Document</h1>
        <UploadForm onResponse={handleResponse} />
      </div>

      <MongoDBDemo />

      {result && !redirectToResults && (
        <div className="mt-6 glossy-card p-6 w-full max-w-md">
          <h2 className="text-lg font-semibold mb-2">Original Summary (EN):</h2>
          <p className="mb-4">{result.summary}</p>
        </div>
      )}
    </div>
  );
}

function ResultsPage() {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Get ID from URL
  const urlParams = new URLSearchParams(window.location.search);
  const documentId = urlParams.get('id');
  
  React.useEffect(() => {
    async function fetchDocument() {
      if (!documentId) {
        setError("No document ID provided");
        setLoading(false);
        return;
      }
      
      try {
        setLoading(true);
        const backendUrl = getBackendUrl(false);
        const response = await fetch(`${backendUrl}/documents/${documentId}`);
        
        if (!response.ok) {
          throw new Error(`Error fetching document: ${response.status}`);
        }
        
        const data = await response.json();
        setDocument(data);
      } catch (err) {
        console.error("Error fetching document:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    
    fetchDocument();
  }, [documentId]);
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-full p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-8">
        <div className="glossy-card p-6 w-full max-w-lg mx-auto">
          <h2 className="text-xl font-bold text-red-600 mb-4">Error</h2>
          <p className="text-gray-700">{error}</p>
          <Link to="/" className="text-blue-600 hover:text-blue-800 mt-4 inline-block">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }
  
  if (!document) {
    return (
      <div className="p-8">
        <div className="glossy-card p-6 w-full max-w-lg mx-auto">
          <h2 className="text-xl font-bold mb-4">No Document Found</h2>
          <p className="text-gray-700">The requested document could not be found.</p>
          <Link to="/" className="text-blue-600 hover:text-blue-800 mt-4 inline-block">
            ← Back to Home
          </Link>
        </div>
      </div>
    );
  }
  
  return (
    <div className="p-8">
      <div className="glossy-card p-6 w-full max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Document Analysis</h1>
        <h2 className="text-xl font-semibold mb-2">{document.title}</h2>
        
        {document.analysis && (
          <>
            <div className="mt-4">
              <h3 className="font-medium text-lg mb-2">Summary:</h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-700">{document.analysis.summary}</p>
              </div>
            </div>
            
            {document.analysis.translated_text && document.language !== 'en' && (
              <div className="mt-4">
                <h3 className="font-medium text-lg mb-2">Translated Version:</h3>
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-gray-700">{document.analysis.translated_text}</p>
                </div>
              </div>
            )}
          </>
        )}
        
        <div className="mt-6">
          <Link to="/" className="text-blue-600 hover:text-blue-800">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}

function SignInPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-full p-8">
      <div className="glossy-card p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold mb-8 text-center">Sign In</h1>
        <p className="text-center text-gray-600 mb-6">
          Sign in to access KanoonSathi and manage your legal documents.
        </p>
        <RedirectToSignIn />
      </div>
    </div>
  );
}

function Documents() {
  return (
    <div className="p-8">
      <MongoDBDemo />
    </div>
  );
}

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route
          path="/"
          element={
            <>
              <SignedIn>
                <Home />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          }
        />
        <Route
          path="/results"
          element={
            <>
              <SignedIn>
                <ResultsPage />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          }
        />
        <Route
          path="/documents"
          element={
            <>
              <SignedIn>
                <Documents />
              </SignedIn>
              <SignedOut>
                <RedirectToSignIn />
              </SignedOut>
            </>
          }
        />
        <Route path="/sign-in" element={<SignInPage />} />
      </Routes>
    </Layout>
  );
}
