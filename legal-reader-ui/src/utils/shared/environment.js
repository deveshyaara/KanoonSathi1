// This is the consolidated environment.js file for the Vite project
// It provides utility functions to access environment variables

/**
 * Gets the backend URL with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The backend URL
 */
export function getBackendUrl(isNextJs = false) {
  if (isNextJs) {
    return process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8001";
  } else {
    return import.meta.env.VITE_BACKEND_URL || "http://localhost:8001";
  }
}

/**
 * Gets the MongoDB URI with appropriate fallback
 * @returns {string} - The MongoDB URI
 */
export function getMongoDBUri() {
  return import.meta.env.VITE_MONGODB_URI || "mongodb://localhost:27017/kanoonsathi";
}