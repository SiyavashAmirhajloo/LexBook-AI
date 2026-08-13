'use client';

import React, { useState, useEffect } from 'react';

interface Document {
  id: string;
  title: string;
  page_count: number;
  upload_date: string;
}

interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_title: string;
  page_number: number;
  text: string;
  score: number;
}

export default function LibraryPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [searchDocId, setSearchDocId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  const fetchDocuments = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data);
      }
    } catch (e) {
      console.error('Failed to load documents', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        await fetchDocuments();
      } else {
        alert('Upload failed');
      }
    } catch (e) {
      alert('Upload error');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      const res = await fetch(`/api/v1/documents/${id}`, { method: 'DELETE' });
      if (res.ok) {
        setDocuments(documents.filter((doc) => doc.id !== id));
        if (searchDocId === id) setSearchDocId(null);
      }
    } catch (e) {
      alert('Delete error');
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchDocId || !searchQuery.trim()) return;

    setSearching(true);
    try {
      const res = await fetch(`/api/v1/documents/${searchDocId}/search?query=${encodeURIComponent(searchQuery)}&top_k=5`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results);
      }
    } catch (e) {
      console.error('Search failed', e);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="flex justify-between items-center border-b border-gray-800 pb-4">
          <h1 className="text-2xl font-bold text-white">Smart PDF Library</h1>
          <a href="/" className="text-sm text-gray-400 hover:text-white">← Back to Home</a>
        </div>

        {/* Upload card */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-lg font-semibold mb-2">Upload Study Book (PDF)</h2>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            disabled={uploading}
            className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-500 cursor-pointer disabled:opacity-50"
          />
          {uploading && <p className="mt-2 text-sm text-blue-400">Processing, extracting text & generating embeddings...</p>}
        </div>

        {/* Library Grid */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Your Books</h2>
          {loading ? (
            <p className="text-gray-500">Loading library...</p>
          ) : documents.length === 0 ? (
            <p className="text-gray-500">No documents uploaded yet.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map((doc) => (
                <div key={doc.id} className="bg-gray-800 border border-gray-700 rounded-lg p-4 flex flex-col justify-between">
                  <div>
                    <h3 className="font-semibold text-lg text-white mb-1 truncate">{doc.title}</h3>
                    <p className="text-sm text-gray-400">{doc.page_count} pages</p>
                    <p className="text-xs text-gray-500 mt-1">
                      Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="mt-4 flex space-x-2">
                    <button
                      onClick={() => setSearchDocId(doc.id)}
                      className={`flex-1 text-xs py-1.5 px-3 rounded font-medium ${
                        searchDocId === doc.id ? 'bg-blue-600 text-white' : 'bg-gray-700 hover:bg-gray-600 text-gray-200'
                      }`}
                    >
                      {searchDocId === doc.id ? 'Selected for Search' : 'Search Book'}
                    </button>
                    <button
                      onClick={() => handleDelete(doc.id)}
                      className="text-xs bg-red-900/40 hover:bg-red-800/60 text-red-300 py-1.5 px-3 rounded font-medium border border-red-800/50"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Vector Search Box */}
        {searchDocId && (
          <div className="bg-gray-800 rounded-lg p-6 border border-blue-900/50">
            <h2 className="text-lg font-semibold mb-4 text-blue-300">
              Vector Search: {documents.find((d) => d.id === searchDocId)?.title}
            </h2>
            <form onSubmit={handleSearch} className="flex gap-2 mb-6">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="e.g. Relative clauses, Passive voice, Vocabulary..."
                className="flex-1 bg-gray-900 border border-gray-700 rounded px-4 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
              />
              <button
                type="submit"
                disabled={searching}
                className="bg-blue-600 hover:bg-blue-500 text-white font-medium px-4 py-2 rounded text-sm disabled:opacity-50"
              >
                {searching ? 'Searching...' : 'Search'}
              </button>
            </form>

            {/* Results */}
            {searchResults.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-400">Top Semantic Matches</h3>
                {searchResults.map((res, i) => (
                  <div key={res.chunk_id} className="bg-gray-900 p-4 rounded border border-gray-700/60 text-sm">
                    <div className="flex justify-between text-xs text-gray-400 mb-2">
                      <span>Page {res.page_number}</span>
                      <span>Similarity Score: {(res.score * 100).toFixed(1)}%</span>
                    </div>
                    <p className="text-gray-300 whitespace-pre-wrap">{res.text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}