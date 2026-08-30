'use client';

import React from 'react';
import Link from 'next/link';
import {
  BarChart,
  Donut,
  KnowledgeGraph,
  LineChart,
  LinePoint,
  Sparkline,
} from '@/components/charts';

interface AnalyticsTotals {
  books_uploaded: number;
  pages_studied: number;
  sessions_count: number;
  sessions_finished: number;
  vocabulary_count: number;
  facts_count: number;
  quiz_attempts: number;
  quizzes_correct: number;
  weak_topic_count: number;
  minutes_studied: number;
}

interface Estimate {
  label: string;
  value: number;
  scale: string;
  method: string;
  inputs: Record<string, number>;
}

interface GrammarTopicRow {
  topic: string;
  mastery: number;
  attempts: number;
  correct: number;
}

interface Analytics {
  totals: AnalyticsTotals;
  study_time: LinePoint[];
  vocabulary_growth: LinePoint[];
  learning_curve: LinePoint[];
  grammar_topics: GrammarTopicRow[];
  mistakes: GrammarTopicRow[];
  knowledge_graph: {
    nodes: { id: string; label: string; weight: number }[];
    edges: { source: string; target: string; weight: number }[];
  };
  timeline: {
    id: string;
    started_at: string;
    finished_at: string | null;
    raw_input: string;
    topics: string[];
  }[];
  estimated_ielts: Estimate;
  estimated_toefl: Estimate;
  scoring_method: string;
}

export default function DashboardPage() {
  const [data, setData] = React.useState<Analytics | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/v1/analytics');
        if (res.ok) {
          setData(await res.json());
        }
      } catch (e) {
        console.error('Failed to load analytics', e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 p-8 flex items-center justify-center">
        <p className="text-gray-500">Loading dashboard…</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-900 text-gray-100 p-8 text-center text-gray-500">
        <p>Failed to load analytics.</p>
        <Link href="/" className="text-sm text-blue-400 underline">
          Back to home
        </Link>
      </div>
    );
  }

  const t = data.totals;
  const accuracy =
    t.quiz_attempts > 0
      ? Math.round((t.quizzes_correct / t.quiz_attempts) * 100)
      : 0;

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6 lg:p-10">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <div>
            <h1 className="text-2xl font-bold text-white">📈 Analytics Dashboard</h1>
            <p className="text-xs text-gray-500 mt-1">
              Built from the V2–V7 data you already have — no separate tracking.
            </p>
          </div>
          <Link href="/memory" className="text-sm text-gray-400 hover:text-white">
            Memory →
          </Link>
        </div>

        {/* KPI tiles */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <KPI label="Books uploaded" value={t.books_uploaded} />
          <KPI label="Pages studied" value={t.pages_studied} />
          <KPI label="Sessions" value={`${t.sessions_finished}/${t.sessions_count}`} sub="finished/total" />
          <KPI
            label="Vocab tracked"
            value={t.vocabulary_count}
            spark={data.vocabulary_growth.map((p) => p.value)}
          />
          <KPI label="Facts remembered" value={t.facts_count} />
        </div>

        {/* Estimated scores row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ScoreCard
            title="Estimated IELTS band"
            value={data.estimated_ielts.value}
            sub={data.estimated_ielts.scale}
            inputs={data.estimated_ielts.inputs}
            color="#60a5fa"
          />
          <ScoreCard
            title="Estimated TOEFL score"
            value={data.estimated_toefl.value}
            sub={data.estimated_toefl.scale}
            inputs={data.estimated_toefl.inputs}
            color="#34d399"
          />
        </div>

        {/* Charts row 1 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="📅 Study time (sessions per day)">
            <LineChart points={data.study_time} color="#60a5fa" yLabel="sessions" />
          </Card>
          <Card title="🌱 Vocabulary growth (running total)">
            <LineChart points={data.vocabulary_growth} color="#34d399" yLabel="words" />
          </Card>
        </div>

        {/* Learning curve + accuracy donut */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card title="📈 Learning curve (daily quiz accuracy)">
            <LineChart
              points={data.learning_curve}
              color="#f59e0b"
              yLabel="%"
              yMax={1}
              formatY={(v) => `${Math.round(v * 100)}%`}
            />
          </Card>
          <Card title="🎯 Overall accuracy">
            <div className="flex items-center gap-4">
              <Donut value={accuracy} max={100} label={`${t.quizzes_correct}/${t.quiz_attempts} correct`} />
              <div className="text-xs text-gray-400 space-y-1">
                <p>Quiz attempts: <b className="text-white">{t.quiz_attempts}</b></p>
                <p>Correct: <b className="text-white">{t.quizzes_correct}</b></p>
                <p>Weak topics: <b className="text-white">{t.weak_topic_count}</b></p>
                <p>Minutes studied: <b className="text-white">{t.minutes_studied}</b></p>
              </div>
            </div>
          </Card>
          <Card title="🧠 Grammar topics mastery">
            <BarChart
              items={[...data.grammar_topics]
                .sort((a, b) => b.mastery - a.mastery)
                .map((g) => ({
                  label: g.topic,
                  value: g.mastery,
                  meta: { attempts: g.attempts },
                  color:
                    g.mastery >= 0.8
                      ? '#34d399'
                      : g.mastery >= 0.5
                        ? '#f59e0b'
                        : '#f87171',
                }))}
              formatValue={(v) => `${Math.round(v * 100)}%`}
            />
          </Card>
        </div>

        {/* Mistakes + Knowledge graph */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card title="❌ Mistakes (mastery < 50%)">
            <BarChart
              items={data.mistakes.map((m) => ({
                label: m.topic,
                value: 1 - m.mastery,
                meta: { attempts: m.attempts },
                color: '#f87171',
              }))}
              formatValue={(v) => `${Math.round(v * 100)}% gap`}
            />
          </Card>
          <Card title="🕸️ Knowledge graph (topic co-occurrence)">
            <KnowledgeGraph
              nodes={data.knowledge_graph.nodes}
              edges={data.knowledge_graph.edges}
            />
          </Card>
        </div>

        {/* Timeline */}
        <Card title="🕒 Recent study sessions">
          {data.timeline.length === 0 ? (
            <p className="text-xs text-gray-500 italic">No sessions yet.</p>
          ) : (
            <ul className="space-y-3">
              {data.timeline.map((s) => (
                <li
                  key={s.id}
                  className="border-l-2 border-blue-700 pl-3 text-sm"
                >
                  <p className="text-gray-200">&quot;{s.raw_input}&quot;</p>
                  {s.topics.length > 0 && (
                    <p className="text-[10px] text-gray-500 mt-0.5">
                      topics: {s.topics.join(', ')}
                    </p>
                  )}
                  <p className="text-[10px] text-gray-600 mt-0.5">
                    {new Date(s.started_at).toLocaleString()}
                    {s.finished_at && ' · finished'}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Scoring formula */}
        <Card title="🧮 Scoring method (transparent)">
          <pre className="text-xs text-gray-400 whitespace-pre-wrap font-mono">
            {data.scoring_method}
          </pre>
        </Card>
      </div>
    </div>
  );
}

// ── Reusable bits ──────────────────────────────────────────────

function KPI({
  label,
  value,
  sub,
  spark,
}: {
  label: string;
  value: number | string;
  sub?: string;
  spark?: number[];
}) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-3">
      <p className="text-[10px] uppercase tracking-wider text-gray-500">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">
        {value}
        {sub && <span className="text-xs text-gray-500 ml-1.5">{sub}</span>}
      </p>
      {spark && (
        <div className="mt-2">
          <Sparkline values={spark} color="#60a5fa" />
        </div>
      )}
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
      <h2 className="text-sm font-semibold text-gray-200 mb-3">{title}</h2>
      {children}
    </div>
  );
}

function ScoreCard({
  title,
  value,
  sub,
  inputs,
  color,
}: {
  title: string;
  value: number;
  sub: string;
  inputs: Record<string, number>;
  color: string;
}) {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-sm font-semibold text-gray-200">{title}</h2>
          <p className="text-3xl font-bold mt-1" style={{ color }}>
            {value}
          </p>
          <p className="text-[10px] text-gray-500">{sub}</p>
        </div>
        <Donut value={value} max={title.includes('IELTS') ? 9 : 120} label="predicted" color={color} />
      </div>
      <div className="mt-3 pt-3 border-t border-gray-700 grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px]">
        {Object.entries(inputs).map(([k, v]) => (
          <div key={k} className="text-gray-400">
            <span className="text-gray-600">{k}: </span>
            <span className="text-white">{v.toFixed(2)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}