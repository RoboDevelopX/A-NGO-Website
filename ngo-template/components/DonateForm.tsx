"use client";

import { useState, type FormEvent } from "react";

type Result = { receiptId: string; amount: number; frequency: "once" | "monthly" };

/**
 * Mock checkout. Card fields are for demonstration only: they are never sent
 * to the server, and /api/donate returns a fake receipt without moving money.
 */
export function DonateForm({
  presets,
  currencySymbol,
}: {
  presets: { amount: number; impact: string }[];
  currencySymbol: string;
}) {
  const [amount, setAmount] = useState<number | "">(presets[1]?.amount ?? presets[0]?.amount ?? 25);
  const [custom, setCustom] = useState(false);
  const [frequency, setFrequency] = useState<"once" | "monthly">("once");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Result | null>(null);

  const impact = presets.find((p) => p.amount === amount)?.impact;

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/donate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Deliberately excludes the card fields.
        body: JSON.stringify({ amount, frequency, name: fd.get("name"), email: fd.get("email") }),
      });
      const data = await res.json();
      if (!res.ok) {
        const first = data.fieldErrors ? Object.values(data.fieldErrors)[0] : null;
        setError((first as string) ?? data.error ?? "Payment failed.");
      } else {
        setResult(data);
      }
    } catch {
      setError("Couldn't reach the server. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  if (result) {
    return (
      <div className="notice notice--success" role="status">
        <h2>Thank you for your {result.frequency === "monthly" ? "monthly " : ""}gift!</h2>
        <p>
          This was a <strong>test donation</strong> of {currencySymbol}
          {result.amount}. No payment was taken.
        </p>
        <p className="small muted">Mock receipt: {result.receiptId}</p>
        <button className="btn btn--outline" onClick={() => setResult(null)}>
          Make another test donation
        </button>
      </div>
    );
  }

  return (
    <form className="form donate-form" onSubmit={onSubmit}>
      <p className="notice notice--info small">
        <strong>Demo mode:</strong> this checkout is a mock. No real payment is processed and card details never
        leave your browser.
      </p>

      <fieldset className="field">
        <legend>Frequency</legend>
        <div className="segmented">
          {(["once", "monthly"] as const).map((f) => (
            <label key={f} className={frequency === f ? "is-active" : ""}>
              <input type="radio" name="frequency" value={f} checked={frequency === f} onChange={() => setFrequency(f)} />
              {f === "once" ? "One-off" : "Monthly"}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="field">
        <legend>Amount</legend>
        <div className="amount-grid">
          {presets.map((p) => (
            <button
              key={p.amount}
              type="button"
              className={`amount ${!custom && amount === p.amount ? "is-active" : ""}`}
              aria-pressed={!custom && amount === p.amount}
              onClick={() => {
                setCustom(false);
                setAmount(p.amount);
              }}
            >
              {currencySymbol}
              {p.amount}
            </button>
          ))}
          <button
            type="button"
            className={`amount ${custom ? "is-active" : ""}`}
            aria-pressed={custom}
            onClick={() => {
              setCustom(true);
              setAmount("");
            }}
          >
            Other
          </button>
        </div>
        {custom && (
          <div className="field">
            <label htmlFor="custom-amount">Your amount ({currencySymbol})</label>
            <input
              id="custom-amount"
              type="number"
              min={1}
              step="1"
              inputMode="numeric"
              value={amount}
              onChange={(e) => setAmount(e.target.value === "" ? "" : Number(e.target.value))}
              required
            />
          </div>
        )}
        {impact && !custom && <p className="impact">{impact}</p>}
      </fieldset>

      <div className="form__row">
        <div className="field">
          <label htmlFor="d-name">Full name</label>
          <input id="d-name" name="name" autoComplete="name" required minLength={2} />
        </div>
        <div className="field">
          <label htmlFor="d-email">Email for your receipt</label>
          <input id="d-email" name="email" type="email" autoComplete="email" required />
        </div>
      </div>

      <div className="field">
        <label htmlFor="card">Card number (test only)</label>
        <input id="card" defaultValue="4242 4242 4242 4242" readOnly aria-readonly="true" />
      </div>
      <div className="form__row">
        <div className="field">
          <label htmlFor="exp">Expiry</label>
          <input id="exp" defaultValue="12 / 34" readOnly />
        </div>
        <div className="field">
          <label htmlFor="cvc">CVC</label>
          <input id="cvc" defaultValue="123" readOnly />
        </div>
      </div>

      {error && (
        <p className="notice notice--error" role="alert">
          {error}
        </p>
      )}

      <button className="btn btn--accent btn--lg btn--block" disabled={busy || amount === ""}>
        {busy
          ? "Processing…"
          : `Donate ${amount === "" ? "" : `${currencySymbol}${amount}`}${frequency === "monthly" ? " / month" : ""}`}
      </button>
    </form>
  );
}
