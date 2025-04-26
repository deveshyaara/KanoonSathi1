'use client';

import { useEffect } from 'react';
import { createClient } from '@/utils/supabase/browser';
import { useRouter } from 'next/navigation';

export default function AuthCallback() {
  const router = useRouter();

  useEffect(() => {
    const handleAuthCallback = async () => {
      const supabase = createClient();
      
      // Check if there's a code in the URL (from the email signup)
      const {
        data: { session },
      } = await supabase.auth.getSession();

      // If session exists, redirect to the home page
      if (session) {
        router.push('/');
      } else {
        // If no session, redirect to sign-in
        router.push('/sign-in');
      }
    };

    handleAuthCallback();
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-4">Authenticating...</h2>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    </div>
  );
}