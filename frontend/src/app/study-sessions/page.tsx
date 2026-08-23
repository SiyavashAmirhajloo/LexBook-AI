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

interface StudyResource {
  id: string;
  topic: string;
  url: string;
  title: string;
  source_domain: string;
  summary: string | null;
  resource_type: string;
  is_reputable: boolean;
  practice_questions: string[];
}

const TYPE_COLORS: Record<string, string> = {
  reading: 'text-sky-300 border-sky-800/60',
  listening: 'text-teal-300 border-teal-800/60',
  writing: 'text-amber-300 border-amber-800/60',
  speaking: 'text-rose-300 border-rose-800/60',
  grammar: 'text-indigo-300 border-indigo-800/60',
  vocabulary: 'text-fuchsia-300 border-fuchsia-800/60',
  general: 'text-gray-300 border-gray-700',
};

export default function StudySessionsPage() {
  const [sessions, setSessions] = React.useState<StudySession[]>([]);
  const [documents, setDocuments] = React.useState<Document[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [starting, setStarting] = React.useState(false);
  const [input, setInput] = React.useState('');
  const [selectedBook, setSelectedBook] = React.useState<string>('');
  const [lastStarted, setLastStarted] = React.useState<StudySession | null>(null);
  const [resources, setResources] = React.useState<Record<string, StudyResource[]>>({});
  const [findingFor, setFindingFor] = React.useState<string | null>(null);

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

  const loadResources = async (id: string) => {
    try {
      const res = await fetch(`/api/v1/study-sessions/${id}/resources`);
      if (res.ok) {
        const data = await res.json();
        setResources((prev) => ({ ...prev, [id]: data.resources }));
      }
    } catch (e) {
      console.error('Load resources failed', e);
    }
  };

  const handleFindResources = async (id: string) => {
    setFindingFor(id);
    try {
      const res = await fetch(`/api/v1/study-sessions/${id}/resources`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setResources((prev) => ({ ...prev, [id]: data.resources }));
      } else {
        const err = await res.json().catch(() => ({ detail: 'Search failed' }));
        alert(err.detail ?? 'Search failed');
      }
    } catch (e) {
      console.error('Find resources failed', e);
    } finally {
      setFindingFor(null);
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

                  {/* V5: Internet Intelligence */}
                  <div className="mt-4 pt-3 border-t border-gray-700/70">
                    {s.topics.length > 0 ? (
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleFindResources(s.id)}
                          disabled={findingFor === s.id}
                          className="text-xs bg-emerald-700 hover:bg-emerald-600 text-white px-3 py-1 rounded font-medium disabled:opacity-50"
                        >
                          {findingFor === s.id ? 'Searching the web…' : '🌐 Find Web Resources'}
                        </button>
                        {!resources[s.id] && (
                          <button
                            onClick={() => loadResources(s.id)}
                            className="text-xs text-gray-400 hover:text-white underline"
                          >
                            show saved
                          </button>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-600">
                        No topics extracted — cannot search for resources.
                      </p>
                    )}

                    {resources[s.id]?.length === 0 && (
                      <p className="text-xs text-gray-500 mt-2">No resources saved yet.</p>
                    )}

                    {!!resources[s.id]?.length && (
                      <div className="mt-3 space-y-3">
                        {resources[s.id].map((r) => (
                          <div
                            key={r.id}
                            className="bg-gray-900/70 border border-gray-700/60 rounded p-3"
                          >
                            <div className="flex items-start justify-between gap-2">
                              <a
                                href={r.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-emerald-300 hover:text-emerald-200 underline decoration-emerald-700/60"
                              >
                                {r.title}
                              </a>
                              {r.is_reputable && (
                                <span className="shrink-0 text-[10px] bg-emerald-900/40 text-emerald-300 border border-emerald-800/60 px-1.5 py-0.5 rounded">
                                  reputable
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] text-gray-500">{r.source_domain}</span>
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded border ${
                                  TYPE_COLORS[r.resource_type] ?? TYPE_COLORS.general
                                }`}
                              >
                                {r.resource_type}
                              </span>
                              <span className="text-[10px] text-gray-600">· {r.topic}</span>
                            </div>

                            {r.summary && (
                              <p className="text-xs text-gray-400 mt-2 leading-relaxed">
                                {r.summary}
                              </p>
                            )}

                            {r.practice_questions.length > 0 && (
                              <div className="mt-3 pt-2 border-t border-gray-800">
                                <p className="text-[10px] font-semibold text-gray-500 mb-1">
                                  ORIGINAL PRACTICE QUESTIONS (AI-generated, not copied)
                                </p>
                                <ul className="list-disc list-inside space-y-1">
                                  {r.practice_questions.map((q, qi) => (
                                    <li key={qi} className="text-xs text-gray-300">
                                      {q}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}