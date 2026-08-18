'use client';

import React from 'react';
import Link from 'next/link';

interface StudySession {
  id: string;
  raw_input: string;
  document_id: string | null;
  document_title: string | null;
  section_label: string | null;
  page_start: number | null;
  page_end: number | null;
  topics: string[];
  keywords: string[];
  summary: string | null;
  started_at: string;
  finished_at: string | null;
}

interface Document {
  id: string;
  title: string;
}

export default function StudySessionsPage() {
  const [sessions, setSessions] = React.useState<StudySession[]>([]);
  const [documents, setDocuments] = React.useState<Document[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [starting, setStarting] = React.useState(false);
  const [input, setInput] = React.useState('');
  const [selectedBook, setSelectedBook] = React.useState<string>('');
  const [lastStarted, setLastStarted] = React.useState<StudySession | null>(null);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const [sRes, dRes] = await Promise.all([
        fetch('/api/v1/study-sessions'),
        fetch('/api/v1/documents'),
      ]);
      if (sRes.ok) {
        const data = await sRes.json();
        setSessions(data);
      }
      if (dRes.ok) {
        const data = await dRes.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error('Failed to load data', e);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchSessions();
  }, []);

  const handleStartSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setStarting(true);
    try {
      const res = await fetch('/api/v1/study-sessions/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_input: input,
          document_id: selectedBook || null,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setLastStarted(data);
        await fetchSessions();
        setInput('');
        setSelectedBook('');
      }
    } catch (e) {
      console.error('Start session failed', e);
    } finally {
      setStarting(false);
    }
  };

  const handleFinish = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/study-sessions/${id}/finish`, { method: 'POST' });
      if (res.ok) {
        await fetchSessions();
      }
    } catch (e) {
      console.error('Finish failed', e);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <h1 className="text-2xl font-bold text-white">Study Sessions</h1>
          <div className="flex space-x-3">
            <Link href="/library" className="text-sm text-gray-400 hover:text-white">← Library</Link>
            <Link href="/chat" className="text-sm text-gray-400 hover:text-white">Chat</Link>
            <Link href="/" className="text-sm text-gray-400 hover:text-white">Home</Link>
          </div>
        </div>

        {/* Start New Session Card */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-white mb-4">📚 Start a New Study Session</h2>
          <p className="text-sm text-gray-400 mb-4">
            Tell the app what you studied, e.g. &quot;I finished Unit 7&quot; or &quot;I studied Relative Clauses&quot;
          </p>
          <form onSubmit={handleStartSession} className="space-y-4">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder='e.g. "I finished Unit 7 of English Grammar in Use"'
              className="w-full bg-gray-900 border border-gray-700 rounded px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              disabled={starting}
            />
            <div className="flex items-center space-x-3">
              <select
                value={selectedBook}
                onChange={(e) => setSelectedBook(e.target.value)}
                className="flex-1 bg-gray-900 border border-gray-700 rounded px-4 py-2 text-sm text-gray-300 focus:outline-none focus:border-blue-500"
              >
                <option value="">Auto-detect from all books</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>{doc.title}</option>
                ))}
              </select>
              <button
                type="submit"
                disabled={starting || !input.trim()}
                className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded text-sm disabled:opacity-50"
              >
                {starting ? 'Saving...' : 'Start Session'}
              </button>
            </div>
          </form>
        </div>

        {/* Extraction Results from last session */}
        {lastStarted && (
          <div className="bg-gray-800 rounded-lg p-6 border border-emerald-900/50 animate-fade-in">
            <h2 className="text-lg font-semibold text-emerald-300 mb-4">✅ Session Started</h2>
            <p className="text-sm text-gray-400 mb-3">You studied: &quot;{lastStarted.raw_input}&quot;</p>
            {!!lastStarted.document_title && (
              <p className="text-sm text-gray-500 mb-4">Book: {lastStarted.document_title}</p>
            )}
            {!!lastStarted.page_start && (
              <p className="text-xs text-gray-600 mb-3">Pages {lastStarted.page_start}–{lastStarted.page_end}</p>
            )}

            {lastStarted.topics.length > 0 && (
              <div className="mb-3">
                <span className="text-xs font-semibold text-gray-400">TOPICS: </span>
                {lastStarted.topics.map((t, i) => (
                  <span key={i} className="text-xs bg-gray-700 text-blue-300 px-2 py-0.5 rounded mr-1">{t}</span>
                ))}
              </div>
            )}
            {lastStarted.keywords.length > 0 && (
              <div className="mb-3">
                <span className="text-xs font-semibold text-gray-400">KEYWORDS: </span>
                {lastStarted.keywords.map((k, i) => (
                  <span key={i} className="text-xs bg-gray-700 text-purple-300 px-2 py-0.5 rounded mr-1">{k}</span>
                ))}
              </div>
            )}
            {lastStarted.summary && (
              <p className="text-sm text-gray-300 mt-3 pt-3 border-t border-gray-700">
                {lastStarted.summary}
              </p>
            )}
          </div>
        )}

        {/* History List */}
        <div>
          <h2 className="text-xl font-semibold mb-4 text-white">History</h2>
          {loading ? (
            <p className="text-gray-500">Loading sessions...</p>
          ) : sessions.length === 0 ? (
            <p className="text-gray-500">No study sessions yet. Start one above!</p>
          ) : (
            <div className="space-y-4">
              {sessions.map((s) => (
                <div key={s.id} className="bg-gray-800 border border-gray-700 rounded-lg p-5">
                  <div className="flex justify-between items-start mb-2">
                    <p className="text-sm text-gray-100">&quot;{s.raw_input}&quot;</p>
                    {s.finished_at ? (
                      <span className="text-xs bg-gray-700 text-green-300 px-2 py-0.5 rounded">✓ Finished</span>
                    ) : (
                      <button
                        onClick={() => handleFinish(s.id)}
                        className="text-xs bg-gray-700 hover:bg-gray-600 text-yellow-300 px-2 py-0.5 rounded"
                      >
                        Mark Finished
                      </button>
                    )}
                  </div>
                  {!!s.document_title && <p className="text-sm text-gray-400 mb-1">Book: {s.document_title}</p>}
                  {!!s.section_label && <p className="text-xs text-gray-500 mb-2">Section: {s.section_label}</p>}
                  {!!s.page_start && <p className="text-xs text-gray-500 mb-2">Pages {s.page_start}–{s.page_end}</p>}
                  {s.topics.length > 0 && (
                    <div className="mb-2">
                      <span className="text-xs font-semibold text-gray-400">TOPICS:</span>
                      {s.topics.map((t, i) => (
                        <span key={i} className="text-xs bg-gray-800/50 text-blue-300 px-2 py-0.5 rounded mr-1 border border-gray-700">{t}</span>
                      ))}
                    </div>
                  )}
                  {s.keywords.length > 0 && (
                    <div className="mb-2">
                      <span className="text-xs font-semibold text-gray-400">KEYWORDS:</span>
                      {s.keywords.slice(0, 8).map((k, i) => (
                        <span key={i} className="text-xs bg-gray-800/50 text-purple-300 px-2 py-0.5 rounded mr-1 border border-gray-700">{k}</span>
                      ))}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-2">
                    {new Date(s.started_at).toLocaleString()}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}