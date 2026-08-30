'use client';

/**
 * Auth context (V9): stores JWT pair in localStorage, exposes login /
 * register / guest / logout, and a fetch wrapper that attaches the
 * bearer token and auto-refreshes on 401.
 */
import React from 'react';

const LS_ACCESS = 'lexbook.access';
const LS_REFRESH = 'lexbook.refresh';

export interface AuthUser {
  id: string;
  email: string;
  name: string;
  provider: string;
  is_active: boolean;
}

interface Tokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

interface AuthState {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
  authedFetch: (url: string, init?: RequestInit) => Promise<Response>;
}

const AuthContext = React.createContext<AuthState | null>(null);

async function refreshTokens(): Promise<boolean> {
  const refresh = localStorage.getItem(LS_REFRESH);
  if (!refresh) return false;
  try {
    const res = await fetch('/api/v1/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const tokens: Tokens = await res.json();
    localStorage.setItem(LS_ACCESS, tokens.access_token);
    localStorage.setItem(LS_REFRESH, tokens.refresh_token);
    return true;
  } catch {
    return false;
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthUser | null>(null);
  const [loading, setLoading] = React.useState(true);

  // Restore session on first mount
  React.useEffect(() => {
    (async () => {
      if (localStorage.getItem(LS_ACCESS)) {
        try {
          const res = await fetch('/api/v1/auth/me', {
            headers: { Authorization: `Bearer ${localStorage.getItem(LS_ACCESS)}` },
          });
          if (res.ok) {
            setUser(await res.json());
          } else if (await refreshTokens()) {
            const retry = await fetch('/api/v1/auth/me', {
              headers: { Authorization: `Bearer ${localStorage.getItem(LS_ACCESS)}` },
            });
            if (retry.ok) setUser(await retry.json());
          }
        } catch {
          /* stay logged out */
        }
      }
      setLoading(false);
    })();
  }, []);

  const applyAuth = (u: AuthUser, tokens: Tokens) => {
    localStorage.setItem(LS_ACCESS, tokens.access_token);
    localStorage.setItem(LS_REFRESH, tokens.refresh_token);
    setUser(u);
  };

  const login = async (email: string, password: string) => {
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? 'Login failed');
    }
    const data = await res.json();
    applyAuth(data.user, data.tokens);
  };

  const register = async (email: string, password: string, name: string) => {
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? 'Registration failed');
    }
    const data = await res.json();
    applyAuth(data.user, data.tokens);
  };

  const loginAsGuest = async () => {
    const res = await fetch('/api/v1/auth/guest', { method: 'POST' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail ?? 'Guest login failed');
    }
    const data = await res.json();
    applyAuth(data.user, data.tokens);
  };

  const logout = () => {
    const refresh = localStorage.getItem(LS_REFRESH);
    if (refresh) {
      // Best-effort revoke; ignore failures.
      void fetch('/api/v1/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refresh }),
      });
    }
    localStorage.removeItem(LS_ACCESS);
    localStorage.removeItem(LS_REFRESH);
    setUser(null);
  };

  const authedFetch = async (url: string, init: RequestInit = {}): Promise<Response> => {
    const headers = new Headers(init.headers);
    const access = localStorage.getItem(LS_ACCESS);
    if (access) headers.set('Authorization', `Bearer ${access}`);

    let res = await fetch(url, { ...init, headers });
    if (res.status === 401 && (await refreshTokens())) {
      headers.set('Authorization', `Bearer ${localStorage.getItem(LS_ACCESS)}`);
      res = await fetch(url, { ...init, headers });
    }
    return res;
  };

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, loginAsGuest, logout, authedFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}