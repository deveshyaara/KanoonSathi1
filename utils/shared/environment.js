// This is a shared util function for environment variables
// It can be used in both Next.js and Vite apps

/**
 * Gets the backend URL with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The backend URL
 */
export function getBackendUrl(isNextJs = false) {
  if (isNextJs) {
    const url = process.env.NEXT_PUBLIC_BACKEND_URL;
    if (!url && process.env.NODE_ENV === 'production') {
      console.warn('NEXT_PUBLIC_BACKEND_URL is not defined in production environment');
    }
    return url || "http://localhost:8001";
  } else {
    const url = import.meta.env?.VITE_BACKEND_URL;
    if (!url && import.meta.env?.PROD) {
      console.warn('VITE_BACKEND_URL is not defined in production environment');
    }
    return url || "http://localhost:8001";
  }
}

/**
 * Gets the MongoDB URI with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The MongoDB URI
 */
export function getMongoDBUri(isNextJs = false) {
  if (isNextJs) {
    const uri = process.env.MONGODB_URI;
    if (!uri && process.env.NODE_ENV === 'production') {
      console.warn('MONGODB_URI is not defined in production environment');
    }
    return uri || "mongodb://localhost:27017/kanoonsathi";
  } else {
    const uri = import.meta.env?.VITE_MONGODB_URI;
    if (!uri && import.meta.env?.PROD) {
      console.warn('VITE_MONGODB_URI is not defined in production environment');
    }
    return uri || "mongodb://localhost:27017/kanoonsathi";
  }
}

/**
 * Gets the application URL with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The application URL
 */
export function getAppUrl(isNextJs = false) {
  if (isNextJs) {
    const url = process.env.NEXT_PUBLIC_APP_URL;
    if (!url && process.env.NODE_ENV === 'production') {
      console.warn('NEXT_PUBLIC_APP_URL is not defined in production environment');
    }
    return url || "http://localhost:3000";
  } else {
    const url = import.meta.env?.VITE_APP_URL;
    if (!url && import.meta.env?.PROD) {
      console.warn('VITE_APP_URL is not defined in production environment');
    }
    return url || "http://localhost:5173";
  }
}