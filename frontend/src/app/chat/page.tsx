'use client';

import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';

interface Citation {
  index: number;
  chunk_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  excerpt: string;
  score: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  streaming?: boolean;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [expandedCitation, setExpandedCitation] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  async function send() {
    if (!input.trim() || streaming) return;
    const userMessage = input.trim();
    setInput('');

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userMessage,
    };
    const aiMsg: Message = {
      id: `ai-${Date.now()}`,
      role: 'assistant',
      content: '',
      citations: [],
      streaming: true,
    };
    setMessages((prev) => [...prev, userMsg, aiMsg]);
    setStreaming(true);

    try {
      const res = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';
      let finalCitations: Citation[] = [];

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const ev of events) {
          const line = ev.trim();
          if (!line.startsWith('data:')) continue;
          const payload = line.slice(5).trim();
          try {
            const json = JSON.parse(payload);
            if (json.type === 'token') {
              accumulated += json.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsg.id ? { ...m, content: accumulated } : m
                )
              );
            } else if (json.type === 'citations') {
              finalCitations = json.citations || [];
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsg.id ? { ...m, citations: finalCitations } : m
                )
              );
            } else if (json.type === 'done' || json.type === 'error') {
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMsg.id ? { ...m, streaming: false } : m
                )
              );
            }
          } catch {
            // ignore malformed lines
          }
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMsg.id
            ? { ...m, content: m.content || `Error: ${msg}`, streaming: false }
            : m
        )
      );
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="flex justify-between items-center px-6 py-4 border-b border-gray-800 bg-gray-900/95 backdrop-blur">
        <h1 className="text-xl font-bold text-white">📚 LexBook AI Chat</h1>
        <Link href="/" className="text-sm text-gray-400 hover:text-white">
          ← Back to Home
        </Link>
      </header>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <p className="text-lg mb-2">Ask anything about your study books.</p>
            <p className="text-sm">e.g. &quot;Explain relative clauses with examples&quot;</p>
          </div>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`max-w-3xl mx-auto flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`rounded-lg px-4 py-3 max-w-[85%] ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 border border-gray-700 text-gray-100'
              }`}
            >
              <div className="whitespace-pre-wrap">{msg.content || (msg.streaming ? '...' : '')}</div>

              {/* Citations */}
              {msg.citations && msg.citations.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700 space-y-2">
                  <div className="text-xs text-gray-400 font-semibold uppercase tracking-wide">
                    Sources
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {msg.citations.map((c) => (
                      <button
                        key={c.chunk_id}
                        onClick={() =>
                          setExpandedCitation(
                            expandedCitation === c.chunk_id ? null : c.chunk_id
                          )
                        }
                        className="text-xs bg-gray-700 hover:bg-gray-600 text-gray-200 px-2 py-1 rounded border border-gray-600"
                      >
                        [{c.index}] {c.document_title} · p. {c.page_number}
                        <span className="ml-1 text-gray-400">
                          ({(c.score * 100).toFixed(0)}%)
                        </span>
                      </button>
                    ))}
                  </div>

                  {/* Expanded excerpts */}
                  {msg.citations.map((c) =>
                    expandedCitation === c.chunk_id ? (
                      <div
                        key={`excerpt-${c.chunk_id}`}
                        className="mt-2 p-3 bg-gray-900 rounded border border-gray-700 text-xs text-gray-300 whitespace-pre-wrap"
                      >
                        <div className="font-semibold mb-1 text-gray-200">
                          [{c.index}] {c.document_title}, p. {c.page_number}
                        </div>
                        {c.excerpt}
                      </div>
                    ) : null
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 bg-gray-900/95 backdrop-blur px-4 py-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
            placeholder="Ask about your books..."
            disabled={streaming}
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          <button
            onClick={send}
            disabled={streaming || !input.trim()}
            className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-5 py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {streaming ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}