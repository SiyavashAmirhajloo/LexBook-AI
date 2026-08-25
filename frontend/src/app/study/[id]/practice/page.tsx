'use client';

import React from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

interface Flashcard {
  id: string;
  front: string;
  back: string;
  kind: string;
  source_topic: string;
}

interface PracticePrompt {
  id: string;
  kind: string;
  prompt_text: string;
  source_topic: string;
}

interface QuizQuestion {
  id: string;
  question: string;
  choices: string[];
  source_topic: string;
}

interface AttemptResult {
  attempt_id: string;
  is_correct: boolean;
  correct_index: number;
  explanation: string;
  topic_mastery: number;
  topic_attempts: number;
}

type Tab = 'flashcards' | 'quiz' | 'prompts';

const PROMPT_COLORS: Record<string, string> = {
  speaking: 'text-rose-300 border-rose-800/60',
  writing: 'text-amber-300 border-amber-800/60',
  reading: 'text-sky-300 border-sky-800/60',
  listening: 'text-teal-300 border-teal-800/60',
};

export default function PracticePage() {
  const params = useParams<{ id: string }>();
  const sessionId = params.id;

  const [tab, setTab] = React.useState<Tab>('flashcards');
  const [cards, setCards] = React.useState<Flashcard[]>([]);
  const [flipped, setFlipped] = React.useState<Record<string, boolean>>({});
  const [prompts, setPrompts] = React.useState<PracticePrompt[]>([]);
  const [questions, setQuestions] = React.useState<QuizQuestion[]>([]);
  const [chosen, setChosen] = React.useState<Record<string, number>>({});
  const [results, setResults] = React.useState<Record<string, AttemptResult>>({});
  const [loading, setLoading] = React.useState<Record<string, boolean>>({});

  const busy = (k: string) => !!loading[k];

  const setBusy = (k: string, v: boolean) =>
    setLoading((prev) => ({ ...prev, [k]: v }));

  React.useEffect(() => {
    loadFlashcards();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  const loadFlashcards = async () => {
    setBusy('flashcards', true);
    try {
      const res = await fetch(`/api/v1/study-sessions/${sessionId}/flashcards`);
      if (res.ok) setCards((await res.json()).cards);
    } finally {
      setBusy('flashcards', false);
    }
  };

  const generateFlashcards = async () => {
    setBusy('gen-cards', true);
    try {
      const res = await fetch(`/api/v1/study-sessions/${sessionId}/flashcards`, { method: 'POST' });
      if (res.ok) setCards((await res.json()).cards);
    } finally {
      setBusy('gen-cards', false);
    }
  };

  const generateQuiz = async () => {
    setBusy('quiz', true);
    try {
      const res = await fetch(`/api/v1/study-sessions/${sessionId}/quiz`, { method: 'POST' });
      if (res.ok) {
        setQuestions((await res.json()).questions);
        setChosen({});
        setResults({});
      }
    } finally {
      setBusy('quiz', false);
    }
  };

  const submitAnswer = async (questionId: string, choiceIdx: number) => {
    if (results[questionId]) return; // already answered
    setChosen((prev) => ({ ...prev, [questionId]: choiceIdx }));
    try {
      const res = await fetch('/api/v1/quiz/attempt', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, chosen_index: choiceIdx }),
      });
      if (res.ok) {
        const data: AttemptResult = await res.json();
        setResults((prev) => ({ ...prev, [questionId]: data }));
      }
    } catch {
      /* leave unanswered on network error */
    }
  };

  const generatePrompts = async () => {
    setBusy('prompts', true);
    try {
      const res = await fetch(`/api/v1/study-sessions/${sessionId}/prompts`, { method: 'POST' });
      if (res.ok) setPrompts((await res.json()).prompts);
    } finally {
      setBusy('prompts', false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <h1 className="text-2xl font-bold text-white">Practice Session</h1>
          <Link href="/study-sessions" className="text-sm text-gray-400 hover:text-white">
            ← Sessions
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-2">
          {(
            [
              ['flashcards', '🃏 Flashcards'],
              ['quiz', '📝 Quiz'],
              ['prompts', '🎤 Prompts'],
            ] as [Tab, string][]
          ).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`px-4 py-2 rounded text-sm font-medium ${
                tab === key ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* ── Flashcards ── */}
        {tab === 'flashcards' && (
          <div className="space-y-4">
            <div className="flex gap-2">
              <button
                onClick={generateFlashcards}
                disabled={busy('gen-cards')}
                className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
              >
                {busy('gen-cards') ? 'Generating…' : cards.length ? 'Generate More' : 'Generate Flashcards'}
              </button>
              {!!cards.length && !busy('gen-cards') && (
                <span className="text-xs text-gray-500 self-center">{cards.length} cards</span>
              )}
            </div>
            {cards.map((c) => (
              <button
                key={c.id}
                onClick={() => setFlipped((p) => ({ ...p, [c.id]: !p[c.id] }))}
                className="w-full text-left bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-lg p-5 transition-colors"
              >
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    c.kind === 'grammar'
                      ? 'text-indigo-300 border-indigo-800/60'
                      : c.kind === 'vocab'
                        ? 'text-fuchsia-300 border-fuchsia-800/60'
                        : 'text-gray-300 border-gray-700'
                  }`}
                >
                  {c.kind}
                </span>
                {!flipped[c.id] ? (
                  <p className="mt-2 font-medium text-white">{c.front}</p>
                ) : (
                  <>
                    <p className="mt-2 font-medium text-white">{c.front}</p>
                    <p className="mt-2 pt-2 border-t border-gray-700 text-sm text-emerald-300">
                      {c.back}
                    </p>
                  </>
                )}
                <p className="mt-2 text-[10px] text-gray-600">
                  {flipped[c.id] ? 'click to hide answer' : 'click to reveal'} · {c.source_topic}
                </p>
              </button>
            ))}
          </div>
        )}

        {/* ── Quiz ── */}
        {tab === 'quiz' && (
          <div className="space-y-4">
            <button
              onClick={generateQuiz}
              disabled={busy('quiz')}
              className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
            >
              {busy('quiz') ? 'Writing questions…' : questions.length ? 'New Quiz' : 'Generate Quiz'}
            </button>

            {questions.map((q, qi) => {
              const result = results[q.id];
              return (
                <div key={q.id} className="bg-gray-800 border border-gray-700 rounded-lg p-5">
                  <p className="font-medium text-white mb-1">
                    {qi + 1}. {q.question}
                  </p>
                  <p className="text-[10px] text-gray-500 mb-3">topic: {q.source_topic}</p>
                  <div className="space-y-2">
                    {q.choices.map((choice, ci) => {
                      const isChosen = chosen[q.id] === ci;
                      const isCorrect = result && result.correct_index === ci;
                      const isWrongPick = result && isChosen && !result.is_correct;
                      let cls = 'border-gray-700 bg-gray-900 hover:border-gray-500';
                      if (result && isCorrect) cls = 'border-emerald-600 bg-emerald-900/30';
                      else if (isWrongPick) cls = 'border-red-600 bg-red-900/30';
                      else if (isChosen) cls = 'border-blue-500 bg-blue-900/30';
                      return (
                        <button
                          key={ci}
                          onClick={() => submitAnswer(q.id, ci)}
                          disabled={!!result}
                          className={`w-full text-left text-sm border rounded px-3 py-2 transition-colors ${cls}`}
                        >
                          {String.fromCharCode(65 + ci)}. {choice}
                          {result && isCorrect && <span className="ml-2 text-emerald-400">✓</span>}
                          {isWrongPick && <span className="ml-2 text-red-400">✗</span>}
                        </button>
                      );
                    })}
                  </div>
                  {result && (
                    <div className="mt-3 pt-3 border-t border-gray-700 text-xs text-gray-400">
                      {result.is_correct ? '✅ Correct. ' : '❌ Not quite. '}
                      {result.explanation}
                      <span className="block mt-1 text-gray-600">
                        Topic mastery: {(result.topic_mastery * 100).toFixed(0)}% over{' '}
                        {result.topic_attempts} attempts
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Prompts ── */}
        {tab === 'prompts' && (
          <div className="space-y-4">
            <button
              onClick={generatePrompts}
              disabled={busy('prompts')}
              className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded text-sm font-medium disabled:opacity-50"
            >
              {busy('prompts') ? 'Composing…' : prompts.length ? 'Generate More' : 'Generate Prompts'}
            </button>
            {prompts.map((p) => (
              <div key={p.id} className="bg-gray-800 border border-gray-700 rounded-lg p-5">
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded border ${
                    PROMPT_COLORS[p.kind] ?? 'text-gray-300 border-gray-700'
                  }`}
                >
                  {p.kind}
                </span>
                <p className="mt-2 text-sm text-gray-200 leading-relaxed">{p.prompt_text}</p>
                <p className="mt-2 text-[10px] text-gray-600">topic: {p.source_topic}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}