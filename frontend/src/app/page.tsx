'use client';

import React from 'react';
import Link from 'next/link';

export default function Home() {
  const [status, setStatus] = React.useState<string>('Loading...');

  React.useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-900 text-gray-100">
      <h1 className="text-4xl font-bold mb-2 text-white">
        LexBook AI
      </h1>
      <p className="text-gray-400 mb-6 text-sm">
        AI-Powered Personal Agentic Learning Platform
      </p>

      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 max-w-sm w-full text-center space-y-4">
        <div>
          <span className="text-xs text-gray-500 uppercase tracking-wider font-semibold">Backend Status</span>
          <p className={`text-lg font-medium ${status === 'ok' ? 'text-green-400' : 'text-yellow-400'}`}>
            {status}
          </p>
        </div>

        <Link
          href="/library"
          className="inline-block w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          Open Smart PDF Library →
        </Link>
      </div>
    </main>
  );
}