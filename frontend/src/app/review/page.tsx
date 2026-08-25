'use client';

import React from 'react';
import Link from 'next/link';

interface WeakTopic {
  topic: string;
  attempts: number;
  correct: number;
  mastery: number;
  last_seen_at: string;
}

export default function ReviewPage() {
  const [topics, setTopics] = React.useState<WeakTopic[]>([]);
  const [recommendation, setRecommendation] = React.useState<string>('');
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const load = async () => {
      try {
        const [wRes, rRes] = await Promise.all([
          fetch('/api/v1/weak-topics?limit=8'),
          fetch('/api/v1/recommendation'),
        ]);
        if (wRes.ok) setTopics(await wRes.json());
        if (rRes.ok) setRecommendation((await rRes.json()).recommendation);
      } catch (e) {
        console.error('Failed to load review data', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <h1 className="text-2xl font-bold text-white">📊 Review &amp; Recommendations</h1>
          <Link href="/study-sessions" className="text-sm text-gray-400 hover:text-white">
            ← Sessions
          </Link>
        </div>

        {recommendation && (
          <div className="bg-emerald-900/20 border border-emerald-800/50 rounded-lg p-5">
            <p className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
              Recommended next
            </p>
            <p className="text-sm text-emerald-200">{recommendation}</p>
          </div>
        )}

        {loading ? (
          <p className="text-gray-500">Loading progress…</p>
        ) : topics.length === 0 ? (
          <p className="text-gray-500">
            No quiz attempts yet. Take a quiz from a practice session to build your mastery
            profile.
          </p>
        ) : (
          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-white">Weakest topics</h2>
            {topics.map((t) => {
              const pct = Math.round(t.mastery * 100);
              const barColor =
                pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-yellow-500' : 'bg-red-500';
              return (
                <div
                  key={t.topic}
                  className="bg-gray-800 border border-gray-700 rounded-lg p-4"
                >
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-white">{t.topic}</span>
                    <span className="text-xs text-gray-400">
                      {t.correct}/{t.attempts} correct · {pct}%
                    </span>
                  </div>
                  <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${barColor}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                  <p className="mt-1 text-[10px] text-gray-600">
                    last practiced {new Date(t.last_seen_at).toLocaleString()}
                  </p>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}