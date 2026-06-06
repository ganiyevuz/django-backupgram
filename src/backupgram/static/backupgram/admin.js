/* django-backupgram — Backup Console interactions (vanilla, no deps). */
(function () {
  "use strict";

  function ready(fn) {
    if (document.readyState !== "loading") fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  /* ---- toast stack: promote Django admin messages into toasts ---- */
  function toastHost() {
    let h = document.getElementById("bgx-toasts");
    if (!h) {
      h = document.createElement("div");
      h.id = "bgx-toasts";
      document.body.appendChild(h);
    }
    return h;
  }
  function toast(text, level) {
    const el = document.createElement("div");
    el.className = "bgx-toast " + (level || "");
    el.textContent = text;
    toastHost().appendChild(el);
    setTimeout(() => {
      el.classList.add("leaving");
      el.addEventListener("animationend", () => el.remove(), { once: true });
    }, 4200);
  }
  function adoptDjangoMessages() {
    document.querySelectorAll("ul.messagelist li").forEach((li) => {
      const level = li.classList.contains("error")
        ? "error"
        : li.classList.contains("warning")
          ? "warning"
          : "";
      toast(li.textContent.trim(), level);
    });
    const list = document.querySelector("ul.messagelist");
    if (list) list.style.display = "none";
  }

  /* ---- copy-to-clipboard ---- */
  function wireCopy() {
    document.querySelectorAll("[data-copy]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const text = btn.getAttribute("data-copy");
        navigator.clipboard
          .writeText(text)
          .then(() => {
            const old = btn.textContent;
            btn.textContent = "copied ✓";
            setTimeout(() => (btn.textContent = old), 1300);
          })
          .catch(() => toast("Copy failed", "error"));
      });
    });
  }

  /* ---- custom confirm modal for destructive forms ---- */
  function el(tag, attrs, text) {
    const node = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach((k) => node.setAttribute(k, attrs[k]));
    if (text != null) node.textContent = text;
    return node;
  }
  function modal() {
    let m = document.getElementById("bgx-modal");
    if (m) return m;
    // Built entirely with createElement/textContent — no markup-string assignment.
    m = el("div", { id: "bgx-modal" });
    const box = el("div", { class: "bgx-modal-box", role: "dialog", "aria-modal": "true" });
    box.appendChild(el("h3", { id: "bgx-modal-title" }, "Are you sure?"));
    box.appendChild(el("p", { id: "bgx-modal-text" }));
    const actions = el("div", { class: "bgx-modal-actions" });
    actions.appendChild(el("button", { type: "button", class: "bgx-btn sm", "data-bgx-cancel": "" }, "Cancel"));
    actions.appendChild(el("button", { type: "button", class: "bgx-btn sm danger", "data-bgx-ok": "" }, "Confirm"));
    box.appendChild(actions);
    m.appendChild(box);
    document.body.appendChild(m);
    return m;
  }
  function wireConfirm() {
    const forms = document.querySelectorAll("form[data-confirm]");
    if (!forms.length) return;
    const m = modal();
    const text = m.querySelector("#bgx-modal-text");
    const okBtn = m.querySelector("[data-bgx-ok]");
    const cancelBtn = m.querySelector("[data-bgx-cancel]");
    let pending = null;
    function close() {
      m.classList.remove("open");
      pending = null;
    }
    cancelBtn.addEventListener("click", close);
    m.addEventListener("click", (e) => {
      if (e.target === m) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
    okBtn.addEventListener("click", () => {
      if (pending) pending.submit();
      close();
    });
    forms.forEach((form) => {
      form.addEventListener("submit", (e) => {
        if (form.dataset.bgxConfirmed) return; // already confirmed
        e.preventDefault();
        pending = form;
        text.textContent = form.getAttribute("data-confirm");
        m.classList.add("open");
        okBtn.focus();
      });
    });
    // mark confirmed before real submit so we don't loop
    okBtn.addEventListener(
      "click",
      () => {
        if (pending) pending.dataset.bgxConfirmed = "1";
      },
      true,
    );
  }

  /* ---- live job polling (job_detail) ---- */
  function pillClass(state) {
    if (state === "succeeded") return "bgx-pill ok";
    if (state === "failed") return "bgx-pill fail";
    if (state === "running" || state === "queued") return "bgx-pill run";
    return "bgx-pill muted";
  }
  function wireJobPolling() {
    const term = document.querySelector("[data-poll-url]");
    if (!term) return;
    const url = term.getAttribute("data-poll-url");
    const log = term.querySelector(".bgx-log");
    const pill = document.querySelector("[data-job-state]");
    const exit = document.querySelector("[data-job-exit]");
    const terminal = new Set(["succeeded", "failed"]);

    let stop = false;
    function tick() {
      if (stop) return;
      fetch(url, { headers: { "X-Requested-With": "fetch" } })
        .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
        .then((job) => {
          if (log && Array.isArray(job.log_tail)) {
            const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
            log.textContent = job.log_tail.join("\n");
            if (atBottom) log.scrollTop = log.scrollHeight;
          }
          if (pill) {
            pill.className = pillClass(job.state);
            pill.textContent = job.state;
          }
          if (exit) exit.textContent = job.exit_code;
          if (terminal.has(job.state)) {
            stop = true;
            term.classList.remove("is-live");
            toast("Job " + job.state, job.state === "failed" ? "error" : "");
          } else {
            setTimeout(tick, 2500);
          }
        })
        .catch(() => {
          setTimeout(tick, 5000);
        });
    }
    if (term.classList.contains("is-live")) setTimeout(tick, 2000);
  }

  ready(function () {
    adoptDjangoMessages();
    wireCopy();
    wireConfirm();
    wireJobPolling();
  });
})();
