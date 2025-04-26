// This file provides type definitions for environment variables

declare namespace NodeJS {
  interface ProcessEnv {
    // Application settings
    NEXT_PUBLIC_APP_URL: string;
    NEXT_PUBLIC_BACKEND_URL: string;
    NODE_ENV: 'development' | 'production' | 'test';
    
    // MongoDB configuration
    MONGODB_URI: string;
    
    // Redis configuration (optional)
    REDIS_URL?: string;
    BACKEND_PORT?: string;
  }
}
