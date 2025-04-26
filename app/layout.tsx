import { ClerkProvider } from '@clerk/nextjs';
import { Inter, Poppins } from 'next/font/google';
import { Metadata } from 'next';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const poppins = Poppins({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-poppins',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'KanoonSathi - Legal Assistance Platform',
  description: 'A modern platform providing legal assistance and resources',
  keywords: ['legal', 'law', 'assistance', 'documents', 'advice'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" className={`${inter.variable} ${poppins.variable}`}>
        <body className="min-h-screen bg-gray-50 font-sans">
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
