// This is a shared util function to determine the backend URL based on the environment
// It can be used in both Next.js and Vite apps

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
 * Gets the Supabase URL with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The Supabase URL
 */
export function getSupabaseUrl(isNextJs = false) {
  if (isNextJs) {
    return process.env.NEXT_PUBLIC_SUPABASE_URL;
  } else {
    return import.meta.env.VITE_SUPABASE_URL;
  }
}

/**
 * Gets the Supabase anon key with appropriate fallback based on framework
 * @param {boolean} isNextJs - Whether this is running in Next.js environment
 * @returns {string} - The Supabase anon key
 */
export function getSupabaseAnonKey(isNextJs = false) {
  if (isNextJs) {
    return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  } else {
    return import.meta.env.VITE_SUPABASE_ANON_KEY;
  }
}