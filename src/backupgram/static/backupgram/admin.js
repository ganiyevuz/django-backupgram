/* django-backupgram — live cron description for SCHEDULE fields.
   Uses the bundled cronstrue (https://github.com/bradymholt/cRonstrue, MIT). */
(function () {
  "use strict";

  // go-cron / Quartz style @shortcuts → standard 5-field cron (cronstrue
  // understands standard cron; it does not parse these named shortcuts).
  var SHORTCUTS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
  };

  function describe(expr) {
    expr = (expr || "").trim();
    if (!expr) return { text: "", ok: false };
    if (expr[0] === "@") {
      if (SHORTCUTS[expr]) {
        expr = SHORTCUTS[expr];
      } else if (/^@every\s+\S+/.test(expr)) {
        return { text: "Every " + expr.slice(7).trim(), ok: true };
      } else {
        return { text: "Unknown shortcut", ok: false };
      }
    }
    if (typeof window.cronstrue === "undefined") {
      return { text: "", ok: true }; // library missing — stay silent
    }
    try {
      return {
        text: window.cronstrue.toString(expr, {
          throwExceptionOnParseError: true,
          use24HourTimeFormat: true,
        }),
        ok: true,
      };
    } catch (e) {
      return { text: "Invalid cron expression", ok: false };
    }
  }

  function wire(input) {
    var preview = document.getElementById(input.getAttribute("data-cron-preview"));
    function update() {
      if (!preview) return;
      var r = describe(input.value);
      preview.textContent = r.text;
      preview.classList.toggle("invalid", !!input.value && !r.ok);
    }
    input.addEventListener("input", update);
    update();
    var presets = preview ? preview.nextElementSibling : null;
    if (presets) {
      presets.querySelectorAll("[data-cron-set]").forEach(function (btn) {
        btn.addEventListener("click", function () {
          input.value = btn.getAttribute("data-cron-set");
          update();
          input.focus();
        });
      });
    }
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  // Restore: click an available backup to fill the form's File field.
  function wireFillFile() {
    var input =
      document.getElementById("id_file") ||
      document.querySelector('form [name="file"]');
    if (!input) return;
    document.querySelectorAll("[data-fill-file]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        input.value = btn.getAttribute("data-fill-file");
        input.focus();
        input.scrollIntoView({ block: "center", behavior: "smooth" });
      });
    });
  }

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }
  ready(function () {
    document.querySelectorAll("input[data-cron]").forEach(wire);
    // Static, read-only cron descriptions (e.g. the dashboard Schedule card).
    document.querySelectorAll("[data-cron-text]").forEach(function (el) {
      var r = describe(el.getAttribute("data-cron-text"));
      if (r.text) el.textContent = r.text;
    });
    wireFillFile();
  });
})();
