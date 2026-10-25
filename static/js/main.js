// Progressive enhancement only: every page works without JavaScript.
(function () {
  "use strict";

  // Mobile navigation toggle.
  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      const open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      nav.classList.toggle("is-open", !open);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        toggle.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
        toggle.focus();
      }
    });
  }

  // Animated impact stats. The real number is already in the HTML, so with JS off or
  // reduced motion on, visitors simply see the final value.
  const counters = document.querySelectorAll("[data-count-to]");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (counters.length && !reduceMotion && "IntersectionObserver" in window) {
    const format = new Intl.NumberFormat("en-IN");
    const animate = function (el) {
      const target = Number(el.dataset.countTo);
      const suffix = el.dataset.suffix || "";
      const duration = 1400;
      const start = performance.now();
      const step = function (now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = format.format(Math.round(target * eased)) + suffix;
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };
    const observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            animate(entry.target);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.4 }
    );
    counters.forEach(function (el) {
      // Screen readers get the final value once, not every animation frame.
      el.setAttribute("aria-label", el.textContent.trim());
      observer.observe(el);
    });
  }
})();
