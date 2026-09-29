import { useState } from "react";
import type { FormEvent } from "react";
import "./App.css";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000/api/v1";

type Citation = {
  source_url: string;
  source_type: string;
  source_id: string;
};

type Memory = {
  memory_type: string;
  title: string;
  summary: string;
  rationale: string;
  evidence: {
    quote: string;
    source_url: string;
    source_type: string;
    source_id: string;
    author: string;
    date: string | null;
  };
  alternatives: string[];
  decided_by: string;
  module: string;
  file_paths: string[];
  status: string;
  confidence: number;
  superseded_by: string | null;
};

type AskResponse = {
  question: string;
  answer: string;
  documented: boolean;
  memory_enabled: boolean;
  memories: Memory[];
  citations: Citation[];
};

type Message =
  | {
      role: "user";
      question: string;
    }
  | {
      role: "assistant";
      response: AskResponse;
    };

function App() {
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(event: FormEvent) {
    event.preventDefault();

    const trimmed = question.trim();

    if (!trimmed || loading) {
      return;
    }

    setError("");
    setLoading(true);

    setMessages((current) => [
      ...current,
      {
        role: "user",
        question: trimmed,
      },
    ]);

    setQuestion("");

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: trimmed,
          memory_enabled: memoryEnabled,
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API request failed with status ${response.status}`,
        );
      }

      const data: AskResponse = await response.json();

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          response: data,
        },
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to contact the memory agent.",
      );
    } finally {
      setLoading(false);
    }
  }

  function clearConversation() {
    setMessages([]);
    setError("");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark">S</span>

          <div>
            <h1>AI Codebase Memory Agent</h1>
            <p>Evidence-backed software history</p>
          </div>
        </div>

        <div className="topbar-actions">
          <div className="memory-control">
            <span>Memory</span>

            <button
              type="button"
              className={`memory-toggle ${
                memoryEnabled ? "enabled" : "disabled"
              }`}
              onClick={() =>
                setMemoryEnabled((current) => !current)
              }
              aria-pressed={memoryEnabled}
            >
              <span className="toggle-dot" />
              {memoryEnabled ? "ON" : "OFF"}
            </button>
          </div>

          <button
            type="button"
            className="clear-button"
            onClick={clearConversation}
          >
            Clear
          </button>
        </div>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="hero-badge">CODEBASE MEMORY</div>

          <h2>Ask why a decision was made.</h2>

          <p>
            Retrieve documented engineering decisions, rationale,
            evidence, and source citations from your codebase history.
          </p>
        </section>

        <section className="chat-panel">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">?</div>

              <h3>What would you like to know?</h3>

              <p>
                Try asking why a framework, architecture, or
                implementation approach was chosen.
              </p>

              <div className="example-questions">
                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Why did we choose FastAPI?")
                  }
                >
                  Why did we choose FastAPI?
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion(
                      "What was the backend framework decision?",
                    )
                  }
                >
                  What was the backend framework decision?
                </button>

                <button
                  type="button"
                  onClick={() =>
                    setQuestion("Why did we choose Redis?")
                  }
                >
                  Why did we choose Redis?
                </button>
              </div>
            </div>
          ) : (
            <div className="messages">
              {messages.map((message, index) => {
                if (message.role === "user") {
                  return (
                    <div
                      className="message-row user-row"
                      key={`user-${index}`}
                    >
                      <div className="user-message">
                        {message.question}
                      </div>
                    </div>
                  );
                }

                const result = message.response;
                const primary = result.memories[0];

                return (
                  <div
                    className="message-row assistant-row"
                    key={`assistant-${index}`}
                  >
                    <div className="assistant-message">
                      <div className="assistant-label">
                        <span className="assistant-dot" />
                        Memory Agent
                      </div>

                      {!result.documented ? (
                        <div className="not-documented">
                          <div className="not-documented-title">
                            NOT DOCUMENTED
                          </div>

                          <p>{result.answer}</p>

                          {result.memory_enabled && (
                            <small>
                              No evidence-backed memory matched
                              this question.
                            </small>
                          )}
                        </div>
                      ) : (
                        <>
                          <h3>
                            {primary?.title ||
                              "Documented decision"}
                          </h3>

                          <div className="answer-section">
                            <span className="section-label">
                              RATIONALE
                            </span>

                            <p>
                              {primary?.rationale ||
                                result.answer}
                            </p>
                          </div>

                          {primary?.alternatives?.length ? (
                            <div className="answer-section">
                              <span className="section-label">
                                ALTERNATIVES
                              </span>

                              <ul>
                                {primary.alternatives.map(
                                  (alternative) => (
                                    <li key={alternative}>
                                      {alternative}
                                    </li>
                                  ),
                                )}
                              </ul>
                            </div>
                          ) : null}

                          {primary?.evidence?.quote && (
                            <div className="evidence-card">
                              <div className="evidence-header">
                                <span className="section-label">
                                  EVIDENCE
                                </span>

                                <span className="verified">
                                  VERIFIED
                                </span>
                              </div>

                              <blockquote>
                                {primary.evidence.quote}
                              </blockquote>
                            </div>
                          )}

                          {result.citations.length > 0 && (
                            <div className="citation-section">
                              <span className="section-label">
                                SOURCE
                              </span>

                              {result.citations.map(
                                (citation) => (
                                  <a
                                    key={`${citation.source_type}-${citation.source_id}`}
                                    href={citation.source_url}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="citation-link"
                                  >
                                    GitHub{" "}
                                    {citation.source_type ===
                                    "github_pr"
                                      ? `PR #${citation.source_id}`
                                      : citation.source_id}
                                    <span>↗</span>
                                  </a>
                                ),
                              )}
                            </div>
                          )}

                          {primary?.module && (
                            <div className="metadata">
                              <span>
                                Module:{" "}
                                <strong>
                                  {primary.module}
                                </strong>
                              </span>

                              <span>
                                Status:{" "}
                                <strong>
                                  {primary.status}
                                </strong>
                              </span>

                              <span>
                                Confidence:{" "}
                                <strong>
                                  {Math.round(
                                    primary.confidence * 100,
                                  )}
                                  %
                                </strong>
                              </span>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                );
              })}

              {loading && (
                <div className="message-row assistant-row">
                  <div className="assistant-message loading-message">
                    <span className="loading-dot" />
                    Searching evidence-backed memory...
                  </div>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className="error-banner">
              <strong>Connection error:</strong> {error}
            </div>
          )}

          <form
            className="composer"
            onSubmit={askQuestion}
          >
            <input
              value={question}
              onChange={(event) =>
                setQuestion(event.target.value)
              }
              placeholder="Ask about your codebase decisions..."
              disabled={loading}
              aria-label="Ask about your codebase"
            />

            <button
              type="submit"
              disabled={loading || !question.trim()}
            >
              {loading ? "..." : "Ask"}
            </button>
          </form>

          <div className="composer-footer">
            <span>
              {memoryEnabled
                ? "Memory is enabled — answers use documented evidence."
                : "Memory is disabled — no codebase memory will be used."}
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
