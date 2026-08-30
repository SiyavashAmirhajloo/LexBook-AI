'use client';

import React from 'react';
import Link from 'next/link';

interface DueReview {
  word: string;
  topic: string;
  bucket: number;
  interval_days: number;
  days_since_seen: number;
  reason: string;
}

interface WeakTopic {
  topic: string;
  mastery: number;
  attempts: number;
  correct: number;
}

interface Plan {
  focus_skill: string;
  focus_reason: string;
  recommended_topic: string;
  topic_reason: string;
  weak_topics: WeakTopic[];
  due_reviews: DueReview[];
  next_chapter: { document_title: string; pages: number[]; reason: string } | null;
  readiness: { ielts_band: number; toefl_score: number; weighted_mastery: number; note: string };
  recent_topics: string[];
  summary: string;
  summary_source: string;
  reasoning: string[];
  generated_at: string;
}

const SKILL_COLORS: Record<string, string> = {
  grammar: 'bg-indigo-600',
  vocabulary: 'bg-fuchsia-600',
  reading: 'bg-sky-600',
  listening: 'bg-teal-600',
  writing: 'bg-amber-600',
  speaking: 'bg-rose-600',
};

export default function PlanPage() {
  const [plan, setPlan] = React.useState<Plan | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/v1/planner/today');
        if (res.ok) {
          setPlan(await res.json());
        } else {
          const err = await res.json().catch(() => ({}));
          setError(err.detail ?? 'Failed to load plan');
        }
      } catch {
        setError('Failed to load plan');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex items-center justify-center">
        <p className="text-gray-500 text-sm">Planning your day…</p>
      </div>
    );
  }

  if (error || !plan) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col items-center justify-center gap-3">
        <p className="text-red-400 text-sm">{error || 'No plan available'}</p>
        <Link href="/" className="text-sm text-blue-400 underline">Back to home</Link>
      </div>
    );
  }

  const skillColor = SKILL_COLORS[plan.focus_skill] ?? 'bg-blue-600';

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6 lg:p-10">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">🗓️ Today&apos;s Plan</h1>
            <p className="text-xs text-gray-500 mt-1">
              Generated {new Date(plan.generated_at).toLocaleString()} ·{' '}
              {plan.summary_source === 'llm' ? 'AI-written' : 'template'} summary
            </p>
          </div>
          <Link href="/" className="text-sm text-gray-400 hover:text-white">← Home</Link>
        </div>

        {/* Summary banner */}
        <div className="bg-gradient-to-r from-blue-900/40 to-purple-900/30 border border-blue-800/50 rounded-lg p-5">
          <p className="text-sm text-gray-100 leading-relaxed">{plan.summary}</p>
        </div>

        {/* Focus skill + topic */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
            <span className={`${skillColor} text-[10px] text-white px-2 py-0.5 rounded uppercase tracking-wider font-semibold`}>
              {plan.focus_skill}
            </span>
            <p className="text-lg font-semibold text-white mt-2">Today&apos;s focus</p>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              <span className="text-gray-500">Why: </span>{plan.focus_reason}
            </p>
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
            <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold">Recommended topic</p>
            <p className="text-lg font-semibold text-white mt-1">{plan.recommended_topic}</p>
            <p className="text-xs text-gray-400 mt-2 leading-relaxed">
              <span className="text-gray-500">Why: </span>{plan.topic_reason}
            </p>
          </div>
        </div>

        {/* Next chapter */}
        {plan.next_chapter && (
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
            <p className="text-[10px] uppercase tracking-wider text-gray-500 font-semibold mb-1">📖 Next chapter</p>
            <p className="text-sm text-white">
              {plan.next_chapter.document_title} — pages{' '}
              {plan.next_chapter.pages[0]}–{plan.next_chapter.pages[1]}
            </p>
            <p className="text-xs text-gray-500 mt-1">{plan.next_chapter.reason}</p>
          </div>
        )}

        {/* Due reviews + weak topics */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
            <p className="text-sm font-semibold text-white mb-3">
              🔁 Due for review <span className="text-xs text-gray-500">({plan.due_reviews.length})</span>
            </p>
            {plan.due_reviews.length === 0 ? (
              <p className="text-xs text-gray-500 italic">Nothing overdue — great streak!</p>
            ) : (
              <ul className="space-y-2">
                {plan.due_reviews.map((d) => (
                  <li key={d.word} className="text-xs bg-gray-900/60 border border-gray-700/60 rounded p-2">
                    <span className="text-emerald-300 font-medium">{d.word}</span>
                    <span className="text-gray-500"> · {d.topic}</span>
                    <p className="text-gray-600 mt-0.5">{d.reason}</p>
                  </li>
                ))}
              </ul>
            )}
          </div>
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
            <p className="text-sm font-semibold text-white mb-3">
              ⚠️ Weak topics <span className="text-xs text-gray-500">({plan.weak_topics.length})</span>
            </p>
            {plan.weak_topics.length === 0 ? (
              <p className="text-xs text-gray-500 italic">Nothing below 50% mastery.</p>
            ) : (
              <ul className="space-y-2">
                {plan.weak_topics.map((w) => (
                  <li key={w.topic} className="text-xs bg-gray-900/60 border border-gray-700/60 rounded p-2">
                    <div className="flex justify-between">
                      <span className="text-red-300 font-medium">{w.topic}</span>
                      <span className="text-gray-500">{w.correct}/{w.attempts} · {Math.round(w.mastery * 100)}%</span>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Readiness */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <p className="text-sm font-semibold text-white mb-2">🎯 Readiness</p>
          <div className="flex gap-6 items-center">
            <div>
              <p className="text-3xl font-bold text-blue-400">{plan.readiness.ielts_band}</p>
              <p className="text-[10px] text-gray-500">IELTS band</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-emerald-400">{plan.readiness.toefl_score}</p>
              <p className="text-[10px] text-gray-500">TOEFL score</p>
            </div>
            <p className="text-[10px] text-gray-600 flex-1">{plan.readiness.note}</p>
          </div>
        </div>

        {/* Reasoning — inspectable */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <p className="text-sm font-semibold text-white mb-2">🧠 Why this plan? (reasoning trace)</p>
          <ol className="space-y-2">
            {plan.reasoning.map((r, i) => (
              <li key={i} className="text-xs text-gray-400 flex gap-2">
                <span className="text-gray-600 shrink-0">{i + 1}.</span>
                <span>{r}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>
    </div>
  );
}