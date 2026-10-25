// Donate page niceties: a live summary, and "Other amount" handling. The form works
// without this file; the server works out the amount from the same fields.
(function () {
  "use strict";
  const form = document.querySelector("[data-donate-form]");
  if (!form) return;
  const summary = form.querySelector("[data-donate-summary]");
  const button = form.querySelector("[data-donate-button]");
  const custom = form.querySelector("#f-custom_amount");
  const customRadio = form.querySelector("#f-amount_choice-custom");
  const inr = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

  function selectedAmount() {
    const choice = form.querySelector("input[name=amount_choice]:checked");
    if (!choice) return null;
    if (choice.value !== "custom") return Number(choice.value);
    const raw = (custom.value || "").replace(/[₹,\s]/g, "");
    return /^\d+$/.test(raw) ? Number(raw) : null;
  }

  function update() {
    const monthly = form.querySelector("input[name=frequency]:checked").value === "monthly";
    const amount = selectedAmount();
    // The custom box is only required when "Other amount" is chosen.
    custom.required = customRadio.checked;
    if (!amount) {
      summary.textContent = "";
      button.textContent = "Donate (demo)";
      return;
    }
    const text = inr.format(amount) + (monthly ? " every month" : " once");
    summary.textContent = "You're giving " + text + ".";
    button.textContent = "Donate " + inr.format(amount) + (monthly ? " monthly" : "") + " (demo)";
  }

  custom.addEventListener("input", function () {
    if (custom.value) customRadio.checked = true;
    update();
  });
  form.addEventListener("change", update);
  update();
})();
