import React from 'react';
import './globals.css';

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
      <body>{children}</body>
    </html>
  );
}