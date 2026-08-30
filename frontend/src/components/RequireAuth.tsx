'use client';

/**
 * Route guard: renders children only when a user is present; redirects
 * to /login otherwise. Guest sessions count as logged-in.
 */
import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!loading && !user) router.replace('/login');
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500 text-sm">{loading ? 'Loading…' : 'Redirecting to login…'}</p>
      </div>
    );
  }
  return <>{children}</>;
}