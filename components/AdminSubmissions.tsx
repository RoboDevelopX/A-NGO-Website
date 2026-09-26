"use client";

import { useEffect, useState, type FormEvent } from "react";
import type { StoredSubmission } from "@/lib/submissions";

const TOKEN_KEY = "ngo-admin-token";

export function AdminSubmissions() {
  const [token, setToken] = useState("");
  const [items, setItems] = useState<StoredSubmission[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "volunteer" | "contact">("all");

  async function load(t: string) {
    setError(null);
    const res = await fetch("/api/submissions", { headers: { Authorization: `Bearer ${t}` } });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setItems(null);
      setError(data.error ?? "Could not load submissions.");
      try {
        sessionStorage.removeItem(TOKEN_KEY);
      } catch {}
      return;
    }
    try {
      sessionStorage.setItem(TOKEN_KEY, t);
    } catch {}
    setItems(data.submissions);
  }

  useEffect(() => {
    let saved: string | null = null;
    try {
      saved = sessionStorage.getItem(TOKEN_KEY);
    } catch {}
    if (saved) {
      setToken(saved);
      void load(saved);
    }
  }, []);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void load(token);
  }

  if (!items) {
    return (
      <form className="form admin-login" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="token">Admin token</label>
          <input id="token" type="password" value={token} onChange={(e) => setToken(e.target.value)} required />
        </div>
        {error && (
          <p className="notice notice--error" role="alert">
            {error}
          </p>
        )}
        <button className="btn btn--primary">View submissions</button>
      </form>
    );
  }

  const shown = items.filter((s) => filter === "all" || s.kind === filter);

  return (
    <div>
      <div className="admin-toolbar">
        <div className="tabs" role="tablist">
          {(["all", "volunteer", "contact"] as const).map((f) => (
            <button
              key={f}
              role="tab"
              aria-selected={filter === f}
              className={`tab ${filter === f ? "is-active" : ""}`}
              onClick={() => setFilter(f)}
            >
              {f === "all" ? `All (${items.length})` : `${f[0].toUpperCase()}${f.slice(1)} (${items.filter((s) => s.kind === f).length})`}
            </button>
          ))}
        </div>
        <button className="btn btn--outline" onClick={() => load(token)}>
          Refresh
        </button>
      </div>
      {shown.length === 0 ? (
        <p className="muted">No submissions yet.</p>
      ) : (
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Received</th>
                <th>Type</th>
                <th>Name</th>
                <th>Email</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {shown.map((s) => (
                <tr key={s.id}>
                  <td>{new Date(s.createdAt).toLocaleString()}</td>
                  <td>
                    <span className={`tag tag--${s.kind}`}>{s.kind}</span>
                  </td>
                  <td>{s.name}</td>
                  <td>
                    <a href={`mailto:${s.email}`}>{s.email}</a>
                    {s.phone && <div className="small muted">{s.phone}</div>}
                  </td>
                  <td>
                    {s.kind === "volunteer" ? (
                      <>
                        <div>
                          <strong>{s.roles.join(", ")}</strong> · {s.availability}
                        </div>
                        {s.message && <div className="small">{s.message}</div>}
                      </>
                    ) : (
                      <>
                        <div>
                          <strong>{s.subject}</strong>
                        </div>
                        <div className="small">{s.message}</div>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
