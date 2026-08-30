'use client';

import React from 'react';
import Link from 'next/link';

interface Fact {
  id: string;
  category: string;
  fact: string;
  source: string;
  created_at: string;
}

interface Vocab {
  id: string;
  word: string;
  translation: string;
  part_of_speech: string;
  status: string;
  seen_count: number;
  topic: string;
  last_seen_at: string;
}

interface WeakTopic {
  topic: string;
  mastery: number;
  attempts: number;
  correct: number;
}

interface RecentSession {
  raw_input: string;
  topics: string[];
  started_at: string | null;
}

export default function MemoryPage() {
  const [facts, setFacts] = React.useState<Fact[]>([]);
  const [vocab, setVocab] = React.useState<Vocab[]>([]);
  const [weak, setWeak] = React.useState<WeakTopic[]>([]);
  const [recent, setRecent] = React.useState<RecentSession[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [newFact, setNewFact] = React.useState('');
  const [newCategory, setNewCategory] = React.useState('fact');
  const [newWord, setNewWord] = React.useState('');
  const [adding, setAdding] = React.useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/memory/snapshot');
      if (res.ok) {
        const d = await res.json();
        setFacts(d.facts);
        setVocab(d.vocabulary);
        setWeak(d.weak_topics);
        setRecent(d.recent_sessions);
      }
    } catch (e) {
      console.error('Failed to load memory', e);
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    load();
  }, []);

  const addFact = async () => {
    if (!newFact.trim()) return;
    setAdding(true);
    try {
      const res = await fetch('/api/v1/memory/facts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fact: newFact, category: newCategory, source: 'manual' }),
      });
      if (res.ok) {
        setNewFact('');
        await load();
      }
    } finally {
      setAdding(false);
    }
  };

  const addWord = async () => {
    if (!newWord.trim()) return;
    setAdding(true);
    try {
      const res = await fetch('/api/v1/memory/vocabulary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ word: newWord }),
      });
      if (res.ok) {
        setNewWord('');
        await load();
      }
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">🧠 Long-Term Memory</h1>
            <p className="text-xs text-gray-500 mt-1">
              What the app remembers about you across sessions.
            </p>
          </div>
          <Link href="/review" className="text-sm text-gray-400 hover:text-white">
            ← Review
          </Link>
        </div>

        {loading ? (
          <p className="text-gray-500">Loading memory…</p>
        ) : (
          <>
            {/* Long-term facts */}
            <section>
              <h2 className="text-lg font-semibold text-white mb-3">
                Long-term facts <span className="text-xs text-gray-500">({facts.length})</span>
              </h2>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-3">
                <div className="flex gap-2">
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="bg-gray-900 border border-gray-700 rounded px-2 py-1.5 text-xs text-gray-300"
                  >
                    <option value="fact">fact</option>
                    <option value="preference">preference</option>
                    <option value="goal">goal</option>
                  </select>
                  <input
                    value={newFact}
                    onChange={(e) => setNewFact(e.target.value)}
                    placeholder='e.g. "I am preparing for the IELTS Academic test in 3 months"'
                    className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={addFact}
                    disabled={adding || !newFact.trim()}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              </div>
              {facts.length === 0 ? (
                <p className="text-sm text-gray-500 italic">No facts remembered yet.</p>
              ) : (
                <ul className="space-y-2">
                  {facts.map((f) => (
                    <li
                      key={f.id}
                      className="bg-gray-800 border border-gray-700 rounded p-3 text-sm"
                    >
                      <span className="text-[10px] text-blue-300 mr-2">[{f.category}]</span>
                      <span className="text-gray-100">{f.fact}</span>
                      <span className="text-[10px] text-gray-600 ml-2">
                        ({f.source} · {new Date(f.created_at).toLocaleDateString()})
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Vocabulary */}
            <section>
              <h2 className="text-lg font-semibold text-white mb-3">
                Vocabulary <span className="text-xs text-gray-500">({vocab.length})</span>
              </h2>
              <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-3">
                <div className="flex gap-2">
                  <input
                    value={newWord}
                    onChange={(e) => setNewWord(e.target.value)}
                    placeholder="Add a word to track…"
                    className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                  />
                  <button
                    onClick={addWord}
                    disabled={adding || !newWord.trim()}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded text-xs font-medium disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              </div>
              {vocab.length === 0 ? (
                <p className="text-sm text-gray-500 italic">No vocabulary tracked yet.</p>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {vocab.map((v) => (
                    <div
                      key={v.id}
                      className="bg-gray-800 border border-gray-700 rounded p-2 text-xs"
                    >
                      <span className="text-emerald-300 font-medium">{v.word}</span>
                      {v.translation && (
                        <span className="text-gray-400 ml-1">→ {v.translation}</span>
                      )}
                      <div className="text-[10px] text-gray-500 mt-1">
                        {v.topic} · seen {v.seen_count}×
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Weak topics */}
            <section>
              <h2 className="text-lg font-semibold text-white mb-3">
                Weak topics{' '}
                <span className="text-xs text-gray-500">({weak.length})</span>
              </h2>
              {weak.length === 0 ? (
                <p className="text-sm text-gray-500 italic">
                  No weak topics. Take a quiz from a study session to build your mastery profile.
                </p>
              ) : (
                <ul className="space-y-2">
                  {weak.map((w) => {
                    const pct = Math.round(w.mastery * 100);
                    const bar =
                      pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
                    return (
                      <li
                        key={w.topic}
                        className="bg-gray-800 border border-gray-700 rounded p-3"
                      >
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-white">{w.topic}</span>
                          <span className="text-xs text-gray-400">
                            {w.correct}/{w.attempts} · {pct}%
                          </span>
                        </div>
                        <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div className={`h-full ${bar}`} style={{ width: `${pct}%` }} />
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </section>

            {/* Recent sessions */}
            <section>
              <h2 className="text-lg font-semibold text-white mb-3">Recent study sessions</h2>
              {recent.length === 0 ? (
                <p className="text-sm text-gray-500 italic">No study sessions yet.</p>
              ) : (
                <ul className="space-y-2">
                  {recent.map((s, i) => (
                    <li
                      key={i}
                      className="bg-gray-800 border border-gray-700 rounded p-3 text-sm"
                    >
                      <p className="text-gray-200">&quot;{s.raw_input}&quot;</p>
                      {s.topics.length > 0 && (
                        <p className="text-[10px] text-gray-500 mt-1">
                          topics: {s.topics.join(', ')}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}