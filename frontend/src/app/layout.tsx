import React from 'react';
import './globals.css';
import { AuthProvider } from '@/lib/auth';

export const metadata = {
  title: 'LexBook AI',
  description: 'AI-powered learning platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}