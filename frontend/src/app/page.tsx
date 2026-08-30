'use client';

import React from 'react';
import Link from 'next/link';
import RequireAuth from '@/components/RequireAuth';
import { useAuth } from '@/lib/auth';

function HomeShell() {
  const { user, logout } = useAuth();
  const [status, setStatus] = React.useState<string>('Loading...');

  React.useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => res.json())
      .then((data) => setStatus(data.status))
      .catch(() => setStatus('error'));
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 bg-gray-900 text-gray-100">
      <div className="absolute top-4 right-4 flex items-center gap-3">
        <div className="text-right">
          <p className="text-sm text-white">{user?.name || 'Guest'}</p>
          <p className="text-[10px] text-gray-500">{user?.provider} · {user?.email}</p>
        </div>
        <button
          onClick={logout}
          className="text-xs bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-300 px-3 py-1.5 rounded"
        >
          Log out
        </button>
      </div>

      <h1 className="text-4xl font-bold mb-2 text-white">LexBook AI</h1>
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

        <Link
          href="/chat"
          className="inline-block w-full bg-emerald-600 hover:bg-emerald-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          Chat with Your Books →
        </Link>

        <Link
          href="/study-sessions"
          className="inline-block w-full bg-purple-600 hover:bg-purple-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          📚 Track a Study Session →
        </Link>

        <Link
          href="/review"
          className="inline-block w-full bg-orange-600 hover:bg-orange-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          📊 Review Weak Topics →
        </Link>

        <Link
          href="/memory"
          className="inline-block w-full bg-pink-600 hover:bg-pink-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          🧠 View Memory →
        </Link>

        <Link
          href="/dashboard"
          className="inline-block w-full bg-cyan-600 hover:bg-cyan-500 text-white font-medium py-2 px-4 rounded text-sm transition-colors"
        >
          📈 Analytics Dashboard →
        </Link>
      </div>
    </main>
  );
}

export default function Home() {
  return (
    <RequireAuth>
      <HomeShell />
    </RequireAuth>
  );
}