'use client';

import React from 'react';

export default function Home() {
  const [status, setStatus] = React.useState<string>('Loading...');

  React.useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-100 dark:bg-gray-900">
      <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-200 mb-4">
        LexBook AI
      </h1>
      <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
        Backend health: {status}
      </p>
    </main>
  );
}