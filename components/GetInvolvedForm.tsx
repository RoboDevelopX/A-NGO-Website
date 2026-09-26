"use client";

import { useState, type FormEvent } from "react";
import { validateSubmission, type FieldErrors } from "@/lib/validation";

type Kind = "volunteer" | "contact";
type Status = { state: "idle" | "submitting" } | { state: "success"; kind: Kind } | { state: "error"; message: string };

export function GetInvolvedForm({
  roles,
  availabilityOptions,
  initialKind = "volunteer",
  contactEmail,
}: {
  roles: string[];
  availabilityOptions: string[];
  initialKind?: Kind;
  contactEmail: string;
}) {
  const [kind, setKind] = useState<Kind>(initialKind);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [status, setStatus] = useState<Status>({ state: "idle" });

  function collect(form: HTMLFormElement) {
    const fd = new FormData(form);
    const common = {
      kind,
      name: String(fd.get("name") ?? ""),
      email: String(fd.get("email") ?? ""),
      phone: String(fd.get("phone") ?? ""),
      message: String(fd.get("message") ?? ""),
      consent: fd.get("consent") === "on",
      website: String(fd.get("website") ?? ""),
    };
    return kind === "volunteer"
      ? { ...common, roles: fd.getAll("roles").map(String), availability: String(fd.get("availability") ?? "") }
      : { ...common, subject: String(fd.get("subject") ?? "") };
  }

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const payload = collect(form);

    // Validate in the browser for instant feedback. The server re-validates with the same schema.
    const check = validateSubmission(payload);
    if (!check.ok && !payload.website) {
      setErrors(check.errors);
      focusFirstError(form, check.errors);
      return;
    }

    setErrors({});
    setStatus({ state: "submitting" });
    try {
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = (await res.json().catch(() => ({}))) as { error?: string; fieldErrors?: FieldErrors };
      if (res.ok) {
        form.reset();
        setStatus({ state: "success", kind });
        return;
      }
      if (data.fieldErrors) {
        setErrors(data.fieldErrors);
        focusFirstError(form, data.fieldErrors);
      }
      setStatus({ state: "error", message: data.error ?? "Something went wrong. Please try again." });
    } catch {
      setStatus({ state: "error", message: `We couldn't reach the server. Please try again or email ${contactEmail}.` });
    }
  }

  if (status.state === "success") {
    return (
      <div className="notice notice--success" role="status">
        <h2>Thank you!</h2>
        <p>
          {status.kind === "volunteer"
            ? "Your volunteer application has been received. Our coordinator will be in touch within a few days."
            : "Your message has been received. We usually reply within two working days."}
        </p>
        <button className="btn btn--outline" onClick={() => setStatus({ state: "idle" })}>
          Send another
        </button>
      </div>
    );
  }

  const err = (field: string) =>
    errors[field] ? (
      <p className="field__error" id={`${field}-error`}>
        {errors[field]}
      </p>
    ) : null;
  const aria = (field: string) =>
    errors[field] ? { "aria-invalid": true as const, "aria-describedby": `${field}-error` } : {};

  return (
    <div>
      <div className="tabs" role="tablist" aria-label="Form type">
        {(["volunteer", "contact"] as const).map((k) => (
          <button
            key={k}
            role="tab"
            type="button"
            aria-selected={kind === k}
            className={`tab ${kind === k ? "is-active" : ""}`}
            onClick={() => {
              setKind(k);
              setErrors({});
              setStatus({ state: "idle" });
            }}
          >
            {k === "volunteer" ? "Volunteer" : "General enquiry"}
          </button>
        ))}
      </div>

      <form className="form" onSubmit={onSubmit} noValidate>
        <div className="form__row">
          <div className="field">
            <label htmlFor="name">Full name *</label>
            <input id="name" name="name" autoComplete="name" {...aria("name")} />
            {err("name")}
          </div>
          <div className="field">
            <label htmlFor="email">Email *</label>
            <input id="email" name="email" type="email" autoComplete="email" {...aria("email")} />
            {err("email")}
          </div>
        </div>

        <div className="field">
          <label htmlFor="phone">Phone (optional)</label>
          <input id="phone" name="phone" type="tel" autoComplete="tel" {...aria("phone")} />
          {err("phone")}
        </div>

        {kind === "volunteer" ? (
          <>
            <fieldset className="field" {...aria("roles")}>
              <legend>What would you like to help with? *</legend>
              <div className="checkbox-grid">
                {roles.map((r) => (
                  <label key={r} className="check">
                    <input type="checkbox" name="roles" value={r} /> {r}
                  </label>
                ))}
              </div>
              {err("roles")}
            </fieldset>
            <div className="field">
              <label htmlFor="availability">When are you available? *</label>
              <select id="availability" name="availability" defaultValue="" {...aria("availability")}>
                <option value="" disabled>
                  Choose one
                </option>
                {availabilityOptions.map((o) => (
                  <option key={o}>{o}</option>
                ))}
              </select>
              {err("availability")}
            </div>
          </>
        ) : (
          <div className="field">
            <label htmlFor="subject">Subject *</label>
            <input id="subject" name="subject" {...aria("subject")} />
            {err("subject")}
          </div>
        )}

        <div className="field">
          <label htmlFor="message">
            {kind === "volunteer" ? "Anything else we should know? (optional)" : "Message *"}
          </label>
          <textarea id="message" name="message" rows={5} {...aria("message")} />
          {err("message")}
        </div>

        {/* Honeypot: visually hidden, ignored by people, filled by bots. */}
        <div className="hp" aria-hidden="true">
          <label htmlFor="website">Leave this empty</label>
          <input id="website" name="website" tabIndex={-1} autoComplete="off" />
        </div>

        <div className="field">
          <label className="check">
            <input type="checkbox" name="consent" {...aria("consent")} /> I agree to be contacted about my enquiry. *
          </label>
          {err("consent")}
        </div>

        {status.state === "error" && (
          <p className="notice notice--error" role="alert">
            {status.message}
          </p>
        )}

        <button className="btn btn--primary btn--lg" disabled={status.state === "submitting"}>
          {status.state === "submitting"
            ? "Sending…"
            : kind === "volunteer"
              ? "Send volunteer application"
              : "Send message"}
        </button>
      </form>
    </div>
  );
}

function focusFirstError(form: HTMLFormElement, errors: FieldErrors) {
  const first = Object.keys(errors)[0];
  const el = first ? (form.querySelector(`[name="${first}"]`) as HTMLElement | null) : null;
  el?.focus();
}
