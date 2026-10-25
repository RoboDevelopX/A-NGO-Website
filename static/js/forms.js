// Client-side validation for forms marked [data-validate].
// The server validates everything again; this only gives faster, friendlier feedback.
// Error copy comes from data-msg-* attributes rendered from app/schemas.py, so both
// sides always show the same words.
(function () {
  "use strict";

  const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const PHONE_CHARS_RE = /^\+?[0-9\s\-()]+$/;

  function messageFor(el) {
    const value = (el.value || "").trim();
    const d = el.dataset;
    if (el.required && !value) return d.msgRequired || "This field is required";
    if (!value) return "";
    const min = Number(el.getAttribute("minlength") || 0);
    const max = Number(el.getAttribute("maxlength") || 0);
    if (d.kind === "email" && !EMAIL_RE.test(value)) return d.msgInvalid;
    if (d.kind === "phone") {
      const digits = value.replace(/\D/g, "").length;
      if (!PHONE_CHARS_RE.test(value) || digits < 7 || digits > 15) return d.msgInvalid;
    }
    if (min && value.length < min) return d.msgShort || d.msgInvalid;
    if (max && value.length > max) return d.msgLong || d.msgInvalid;
    if (d.kind === "amount") {
      const amount = Number(value);
      const lo = Number(d.min || 0);
      const hi = Number(d.max || Infinity);
      if (!Number.isInteger(amount) || amount < lo || amount > hi) return d.msgInvalid;
    }
    return "";
  }

  function groupMessage(fieldset) {
    if (fieldset.dataset.required !== "true") return "";
    const checked = fieldset.querySelector("input:checked");
    return checked ? "" : fieldset.dataset.msgRequired;
  }

  function show(target, name, message) {
    const slot = document.getElementById("f-" + name + "-error");
    if (slot) {
      slot.textContent = "";
      if (message) {
        const hidden = document.createElement("span");
        hidden.className = "visually-hidden";
        hidden.textContent = "Error: ";
        slot.append(hidden, message);
      }
    }
    const container = target.closest(".field, .fieldset");
    if (container) container.classList.toggle(container.classList.contains("fieldset") ? "fieldset--invalid" : "field--invalid", !!message);
    const inputs = target.matches("fieldset") ? target.querySelectorAll("input") : [target];
    inputs.forEach(function (input) {
      if (message) input.setAttribute("aria-invalid", "true");
      else input.removeAttribute("aria-invalid");
    });
  }

  function validateControl(el) {
    if (el.matches("fieldset[data-choice-group]")) {
      const message = groupMessage(el);
      show(el, el.dataset.choiceGroup, message);
      return message;
    }
    const message = messageFor(el);
    show(el, el.name, message);
    return message;
  }

  function controls(form) {
    return form.querySelectorAll(
      ".field input:not([type=hidden]), .field select, .field textarea, fieldset[data-choice-group]"
    );
  }

  document.querySelectorAll("form[data-validate]").forEach(function (form) {
    // Errors appear on submit (the GOV.UK pattern) and clear live as soon as a flagged
    // field is fixed. We deliberately don't validate on blur: adding or removing an error
    // message on blur shifts the layout, so a click on "Submit" right after typing could
    // land on empty space instead of the button.
    const recheck = function (event) {
      const el = event.target.closest("fieldset[data-choice-group]") || event.target;
      const flagged = el.matches("fieldset")
        ? el.classList.contains("fieldset--invalid")
        : el.getAttribute("aria-invalid") === "true";
      if (flagged) validateControl(el);
    };
    form.addEventListener("input", recheck);
    form.addEventListener("change", recheck);

    form.addEventListener("submit", function (event) {
      if (form.dataset.submitting === "true") {
        // Double-submit guard (the server also rejects reused form tokens).
        event.preventDefault();
        return;
      }
      let firstInvalid = null;
      controls(form).forEach(function (el) {
        if (validateControl(el) && !firstInvalid) firstInvalid = el;
      });
      if (firstInvalid) {
        event.preventDefault();
        const focusTarget = firstInvalid.matches("fieldset") ? firstInvalid.querySelector("input") : firstInvalid;
        focusTarget.focus();
        return;
      }
      form.dataset.submitting = "true";
      const button = form.querySelector("[type=submit]");
      if (button) {
        button.setAttribute("aria-disabled", "true");
        button.setAttribute("aria-busy", "true");
        if (button.dataset.submitLabel) button.textContent = button.dataset.submitLabel;
      }
    });
  });

  // After a failed server-side submit, move focus to the error summary so screen reader
  // users hear what went wrong.
  const summary = document.querySelector("[data-error-summary]");
  if (summary) summary.focus();
})();
