import './globals.css';
import { ClerkProvider, UserButton } from '@clerk/nextjs';
import Link from 'next/link';
import ErrorBoundary from '@/components/ErrorBoundary';

export const metadata = {
  title: 'KanoonSathi',
  description: 'A legal assistant application',
};

export default function RootLayout({ children }) {
  return (
    <ClerkProvider>
      <html lang="en" className="h-full">
        <body className="h-full">
          <ErrorBoundary>
            <main className="min-h-screen flex flex-col">
              <header className="flex justify-between items-center p-4 h-16 border-b bg-white">
                <nav className="flex items-center gap-4">
                  <Link href="/" className="text-xl font-bold hover:text-blue-600 transition-colors">
                    KanoonSathi
                  </Link>
                  <Link 
                    href="/upload" 
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                  >
                    Upload
                  </Link>
                  <Link 
                    href="/todos" 
                    className="text-gray-600 hover:text-blue-600 transition-colors"
                  >
                    Todos
                  </Link>
                </nav>
                <div className="flex items-center gap-4">
                  <UserButton 
                    afterSignOutUrl="/"
                    appearance={{
                      elements: {
                        avatarBox: "w-10 h-10"
                      }
                    }} 
                  />
                </div>
              </header>
              <div className="flex-grow">
                {children}
              </div>
              <footer className="py-4 px-6 border-t bg-white">
                <div className="text-center text-sm text-gray-500">
                  © {new Date().getFullYear()} KanoonSathi. All rights reserved.
                </div>
              </footer>
            </main>
          </ErrorBoundary>
        </body>
      </html>
    </ClerkProvider>
  );
}