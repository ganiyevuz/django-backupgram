/* django-backupgram — live cron description for SCHEDULE fields. */
(function () {
  "use strict";
  var DOW = ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"];
  var MON = ["","January","February","March","April","May","June","July","August","September","October","November","December"];

  function pad(n) { return (n < 10 ? "0" : "") + n; }

  function describe(expr) {
    expr = (expr || "").trim();
    if (!expr) return { text: "", ok: false };
    if (expr[0] === "@") {
      var map = {
        "@hourly": "Every hour, at minute 0",
        "@daily": "Every day at 00:00",
        "@midnight": "Every day at 00:00",
        "@weekly": "Every Sunday at 00:00",
        "@monthly": "On the 1st of every month at 00:00",
        "@yearly": "On January 1 at 00:00",
        "@annually": "On January 1 at 00:00",
      };
      if (map[expr]) return { text: map[expr], ok: true };
      if (/^@every\s+\S+/.test(expr)) return { text: "Every " + expr.slice(7).trim(), ok: true };
      return { text: "Unknown shortcut", ok: false };
    }
    var f = expr.split(/\s+/);
    if (f.length !== 5) return { text: "Expected 5 fields (min hour day month weekday) or an @shortcut", ok: false };
    var m = f[0], h = f[1], dom = f[2], mon = f[3], dow = f[4];

    function timePart() {
      if (m === "*" && h === "*") return "every minute";
      if (h === "*") return (m === "*" ? "every minute" : "at minute " + m + " of every hour");
      if (m === "*") return "every minute of hour " + h;
      var mi = parseInt(m, 10), hh = parseInt(h, 10);
      if (!isNaN(mi) && !isNaN(hh)) return "at " + pad(hh) + ":" + pad(mi);
      return "at " + h + ":" + m;
    }
    var when = timePart();
    var parts = [when];
    if (dow !== "*") {
      var d = parseInt(dow, 10);
      parts.push(!isNaN(d) && DOW[d % 7] ? "on " + DOW[d % 7] : "on weekday " + dow);
    } else if (dom !== "*") {
      parts.push("on day " + dom + " of the month");
    } else {
      parts.push("every day");
    }
    if (mon !== "*") {
      var mo = parseInt(mon, 10);
      parts.push(!isNaN(mo) && MON[mo] ? "in " + MON[mo] : "in month " + mon);
    }
    return { text: parts.join(", ").replace(/^(\w)/, function (c) { return c.toUpperCase(); }), ok: true };
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
    // preset chips that sit right after the preview
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

  function ready(fn) { document.readyState !== "loading" ? fn() : document.addEventListener("DOMContentLoaded", fn); }
  ready(function () { document.querySelectorAll("input[data-cron]").forEach(wire); });
})();
