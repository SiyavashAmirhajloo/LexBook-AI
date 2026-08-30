'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

type Mode = 'login' | 'register';

export default function LoginPage() {
  const router = useRouter();
  const { user, loading, login, register, loginAsGuest } = useAuth();
  const [mode, setMode] = React.useState<Mode>('login');
  const [email, setEmail] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [name, setName] = React.useState('');
  const [error, setError] = React.useState('');
  const [busy, setBusy] = React.useState(false);

  React.useEffect(() => {
    if (!loading && user) router.replace('/');
  }, [user, loading, router]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'login') {
        await login(email, password);
      } else {
        await register(email, password, name);
      }
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setBusy(false);
    }
  };

  const guest = async () => {
    setError('');
    setBusy(true);
    try {
      await loginAsGuest();
      router.replace('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Guest login failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-white">LexBook AI</h1>
          <p className="text-xs text-gray-500 mt-1">Your AI study companion</p>
        </div>

        {/* Mode switch */}
        <div className="flex gap-1 bg-gray-900 rounded p-1">
          {(['login', 'register'] as Mode[]).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setError('');
              }}
              className={`flex-1 py-1.5 rounded text-sm font-medium transition-colors ${
                mode === m ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {m === 'login' ? 'Sign in' : 'Register'}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="space-y-3">
          {mode === 'register' && (
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name (optional)"
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
          )}
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password (min 8 chars)"
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
          />

          {error && (
            <p className="text-xs text-red-400 bg-red-900/30 border border-red-800/50 rounded px-3 py-2">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 rounded text-sm disabled:opacity-50"
          >
            {busy ? '…' : mode === 'login' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <div className="flex items-center gap-2 text-[10px] text-gray-600">
          <div className="flex-1 h-px bg-gray-700" />or<div className="flex-1 h-px bg-gray-700" />
        </div>

        <button
          onClick={guest}
          disabled={busy}
          className="w-full bg-gray-700 hover:bg-gray-600 text-gray-200 font-medium py-2 rounded text-sm disabled:opacity-50"
        >
          👤 Continue as Guest
        </button>

        <p className="text-[10px] text-gray-600 text-center">
          Guest sessions work fully but are anonymous — register to keep your data.
        </p>
      </div>
    </div>
  );
}