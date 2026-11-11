(function () {
  "use strict";
  var path = location.pathname;
  if (!(path === "/properties" || path.indexOf("/property/") === 0 || path === "/contact")) return;
  if (window.__rpChat) return;
  window.__rpChat = true;

  var STR = {
    en: {
      title: "Property assistant", sub: "Ask about our listings", ph: "Type your message…",
      send: "Send", wa: "WhatsApp", open: "Chat with us", lang: "ع",
      hi: "Hi! I can help you find a property or answer questions about a listing. What are you looking for?",
      err: "Something went wrong. Please try again.",
      chips: ["2 bedroom apartments for rent", "Villas for rent", "Explain the cheque plan"],
      note: "AI assistant: replies may be inaccurate. Please don't share ID numbers, passwords or bank details here."
    },
    ar: {
      title: "مساعد العقارات", sub: "اسألنا عن العقارات المتاحة", ph: "اكتب رسالتك…",
      send: "إرسال", wa: "واتساب", open: "تحدث معنا", lang: "EN",
      hi: "مرحباً! يمكنني مساعدتك في إيجاد عقار أو الإجابة عن أسئلتك حول أي عقار. ماذا تبحث عن؟",
      err: "حدث خطأ ما. يرجى المحاولة مرة أخرى.",
      chips: ["شقق غرفتين للإيجار", "فلل للإيجار", "اشرح لي نظام الشيكات"],
      note: "مساعد آلي: قد تكون الردود غير دقيقة. يرجى عدم مشاركة أرقام الهوية أو كلمات المرور أو بيانات البنك هنا."
    }
  };

  var lang = sessionStorage.getItem("rp_lang") ||
    ((document.documentElement.lang || "").slice(0, 2) === "ar" ? "ar" : "en");
  var token = sessionStorage.getItem("rp_chat_token") || null;
  var cfg = {}, busy = false, started = false;
  var el = {};

  function api(method, args, ok, fail, type) {
    frappe.call({
      method: "re_portal.api.chat." + method, type: type || "POST", args: args,
      callback: function (r) { ok(r.message || {}); },
      error: function () { if (fail) fail(); }
    });
  }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }
  // escape first, then allow only [text](/relative/path) links, **bold** and line breaks
  function render(text) {
    return esc(text)
      .replace(/\[([^\]]+)\]\((\/[A-Za-z0-9][A-Za-z0-9_\-\/.%]*)\)/g, '<a href="$2">$1</a>')
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\n/g, "<br>");
  }

  function addMsg(role, text, handoff) {
    var d = document.createElement("div");
    d.className = "rpc-msg " + (role === "user" ? "rpc-usr" : "rpc-bot");
    d.setAttribute("dir", "auto");
    d.innerHTML = role === "user" ? esc(text).replace(/\n/g, "<br>") : render(text);
    if (handoff && cfg.whatsapp) {
      var a = document.createElement("a");
      a.href = "https://wa.me/" + cfg.whatsapp; a.target = "_blank"; a.rel = "noopener";
      a.textContent = " " + STR[lang].wa + " ↗";
      d.appendChild(document.createElement("br")); d.appendChild(a);
    }
    el.log.appendChild(d);
    el.log.scrollTop = el.log.scrollHeight;
    return d;
  }

  function applyLang() {
    var s = STR[lang];
    el.panel.setAttribute("dir", lang === "ar" ? "rtl" : "ltr");
    el.ttl.firstChild.nodeValue = s.title; el.sub.textContent = s.sub;
    el.input.placeholder = s.ph; el.sendBtn.textContent = s.send;
    el.langBtn.textContent = s.lang; el.btn.title = s.open;
    el.wa.textContent = s.wa; el.note.textContent = s.note;
    el.chips.innerHTML = "";
    if (!started) {
      s.chips.forEach(function (c) {
        var b = document.createElement("button"); b.type = "button"; b.textContent = c;
        b.addEventListener("click", function () { send(c); });
        el.chips.appendChild(b);
      });
    }
  }

  function send(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true; started = true; el.chips.innerHTML = "";
    el.input.value = ""; el.sendBtn.disabled = true;
    addMsg("user", text);
    var wait = addMsg("bot", "…");
    api("send", { message: text, session_token: token, lang: lang }, function (r) {
      wait.remove();
      if (r.session_token) { token = r.session_token; sessionStorage.setItem("rp_chat_token", token); }
      addMsg("bot", r.reply || STR[lang].err, r.handoff);
      done();
    }, function () { wait.remove(); addMsg("bot", STR[lang].err, true); done(); });
  }
  function done() { busy = false; el.sendBtn.disabled = false; el.input.focus(); }

  function toggle(open) {
    var show = open === undefined ? !el.panel.classList.contains("rpc-open") : open;
    el.panel.classList.toggle("rpc-open", show);
    if (show && !el.log.childNodes.length) {
      if (token) {
        api("history", { session_token: token }, function (r) {
          (r.messages || []).forEach(function (m) { addMsg(m.role, m.text); });
          if (r.messages && r.messages.length) { started = true; applyLang(); }
          else addMsg("bot", STR[lang].hi);
        }, function () { addMsg("bot", STR[lang].hi); }, "GET");
      } else addMsg("bot", STR[lang].hi);
    }
    if (show) el.input.focus();
  }

  function build() {
    var panel = document.createElement("div");
    panel.className = "rpc-panel";
    panel.innerHTML =
      '<div class="rpc-head"><div class="rpc-ttl">x<small></small></div>' +
      '<a target="_blank" rel="noopener" style="display:none"></a>' +
      '<button type="button" class="rpc-lang"></button><button type="button" class="rpc-x">✕</button></div>' +
      '<div class="rpc-log"></div>' +
      '<div class="rpc-chips" style="padding:0 12px"></div>' +
      '<div class="rpc-note"></div>' +
      '<form class="rpc-form"><input type="text" maxlength="1000" autocomplete="off"><button type="submit"></button></form>';
    var btn = document.createElement("button");
    btn.className = "rpc-btn"; btn.type = "button"; btn.textContent = "💬";
    document.body.appendChild(panel); document.body.appendChild(btn);
    el = {
      panel: panel, btn: btn, ttl: panel.querySelector(".rpc-ttl"), sub: panel.querySelector("small"),
      wa: panel.querySelector(".rpc-head a"), langBtn: panel.querySelector(".rpc-lang"),
      log: panel.querySelector(".rpc-log"), chips: panel.querySelector(".rpc-chips"),
      input: panel.querySelector("input"), sendBtn: panel.querySelector(".rpc-form button"),
      note: panel.querySelector(".rpc-note")
    };
    if (cfg.whatsapp) { el.wa.href = "https://wa.me/" + cfg.whatsapp; el.wa.style.display = ""; }
    btn.addEventListener("click", function () { toggle(); });
    panel.querySelector(".rpc-x").addEventListener("click", function () { toggle(false); });
    el.langBtn.addEventListener("click", function () {
      lang = lang === "ar" ? "en" : "ar"; sessionStorage.setItem("rp_lang", lang); applyLang();
    });
    panel.querySelector("form").addEventListener("submit", function (e) {
      e.preventDefault(); send(el.input.value);
    });
    applyLang();
  }

  function boot() {
    api("config", {}, function (r) { cfg = r; if (r.enabled) build(); }, null, "GET");
  }
  if (window.frappe && frappe.ready) frappe.ready(boot);
  else window.addEventListener("load", boot);
})();
