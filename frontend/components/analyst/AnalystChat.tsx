'use client';

import { useState } from 'react';
import { Send, Bot, AlertCircle } from 'lucide-react';
import { askAnalyst } from '@/lib/api';
import { AnalystResponse } from '@/types';

export function AnalystChat() {
  const [question, setQuestion] = useState('');
  const [response, setResponse] = useState<AnalystResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await askAnalyst(question);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to query analyst');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-surface">
      {/* Header */}
      <div className="p-4 border-b border-border bg-surfaceHighlight">
        <div className="flex items-center gap-3">
          <Bot className="w-6 h-6 text-primary" />
          <div>
            <h2 className="text-lg font-semibold text-text">AI Analyst</h2>
            <p className="text-xs text-textMuted">
              Retrieval-based analysis with citations
            </p>
          </div>
        </div>
      </div>

      {/* Response Area */}
      <div className="flex-1 overflow-y-auto p-4">
        {!response && !loading && !error && (
          <div className="flex items-center justify-center h-full text-textMuted">
            <div className="text-center max-w-md">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">
                Ask questions about entities, anomalies, and system events.
                All answers are grounded in retrieved evidence with citations.
              </p>
              <div className="mt-4 space-y-2 text-xs">
                <p className="text-textMuted">Example questions:</p>
                <p className="text-text">• "Show me all high-severity anomalies"</p>
                <p className="text-text">• "What vessels are near the port?"</p>
                <p className="text-text">• "Are there any cyber outages affecting sensors?"</p>
              </div>
            </div>
          </div>
        )}

        {loading && (
          <div className="flex items-center justify-center h-full">
            <div className="animate-pulse text-textMuted">Analyzing...</div>
          </div>
        )}

        {error && (
          <div className="flex items-start gap-3 p-4 bg-danger/10 border border-danger/30 rounded-lg">
            <AlertCircle className="w-5 h-5 text-danger flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm text-danger">Error</p>
              <p className="text-xs text-textMuted">{error}</p>
            </div>
          </div>
        )}

        {response && (
          <div className="space-y-4">
            {/* Answer */}
            <div className="p-4 bg-surfaceHighlight border border-border rounded-lg">
              <p className="text-sm text-text leading-relaxed">{response.answer}</p>
            </div>

            {/* Confidence Meter */}
            <div className="p-4 bg-surfaceHighlight border border-border rounded-lg">
              <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-2">
                Confidence
              </h3>
              <div className="flex items-center gap-3">
                <div className="flex-1 h-2 bg-background rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      response.confidence >= 0.8 ? 'bg-success' :
                      response.confidence >= 0.6 ? 'bg-warning' :
                      'bg-danger'
                    }`}
                    style={{ width: `${response.confidence * 100}%` }}
                  />
                </div>
                <span className="text-sm text-text">{(response.confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {/* Citations */}
            {response.citations.length > 0 && (
              <div className="p-4 bg-surfaceHighlight border border-border rounded-lg">
                <h3 className="text-xs font-semibold text-textMuted uppercase tracking-wider mb-3">
                  Citations ({response.citations.length})
                </h3>
                <div className="space-y-2">
                  {response.citations.map((citation, index) => (
                    <div
                      key={citation.id}
                      className="p-2 bg-background border border-border rounded text-xs"
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-textMuted flex-shrink-0">[{index + 1}]</span>
                        <div>
                          <p className="text-text font-medium">{citation.summary}</p>
                          <p className="text-textMuted mt-1">{citation.reference}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Limitations */}
            {response.limitations.length > 0 && (
              <div className="p-4 bg-warning/10 border border-warning/30 rounded-lg">
                <h3 className="text-xs font-semibold text-warning uppercase tracking-wider mb-2">
                  Limitations
                </h3>
                <ul className="space-y-1">
                  {response.limitations.map((limitation, index) => (
                    <li key={index} className="text-xs text-textMuted flex items-start gap-2">
                      <span className="text-warning">•</span>
                      {limitation}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border bg-surfaceHighlight">
        <div className="flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask about entities, anomalies, or events..."
            className="flex-1 px-4 py-2 bg-background border border-border rounded-lg text-sm text-text placeholder-textMuted focus:outline-none focus:border-primary transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !question.trim()}
            className="px-4 py-2 bg-primary hover:bg-primaryHover disabled:bg-surfaceHighlight disabled:text-textMuted text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </form>
    </div>
  );
}
