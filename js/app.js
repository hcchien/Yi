/* 易 · 擲爻問卦 — casting logic & rendering */
(function () {
  "use strict";

  var UI = window.YI_UI;
  var HEX = window.YI || [];
  var LANGS = ["zh", "en", "ja", "ko", "es", "fr", "de"];

  // binary (bottom→top, 1=yang) → hexagram
  var byBin = {};
  HEX.forEach(function (h) { byBin[h.b] = h; });

  // ---------- state ----------
  var lang = detectLang();
  var casts = [];        // values 6/7/8/9, bottom→top
  var busy = false;
  var autoMode = false;

  // ---------- elements ----------
  var $ = function (id) { return document.getElementById(id); };
  var shell = $("shell"),
      castBtn = $("castBtn"),
      autoBtn = $("autoBtn"),
      resetBtn = $("resetBtn"),
      castStatus = $("castStatus"),
      castResult = $("castResult"),
      builder = $("builder"),
      builderNote = $("builderNote"),
      reading = $("reading"),
      readingBody = $("readingBody"),
      coins = [ $("coin0"), $("coin1"), $("coin2") ];

  function detectLang() {
    var requested = new URLSearchParams(location.search).get("lang");
    if (requested && LANGS.indexOf(requested) >= 0) return requested;
    var saved = null;
    try { saved = localStorage.getItem("yi-lang"); } catch (e) {}
    if (saved && LANGS.indexOf(saved) >= 0) return saved;

    // Follow the browser's ordered language preferences on the first visit.
    // Region variants such as zh-TW, en-US and pt-BR are reduced to their
    // primary language code; unsupported languages fall back to English.
    var browserLangs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || navigator.userLanguage || "en"];

    for (var i = 0; i < browserLangs.length; i++) {
      var primary = String(browserLangs[i]).toLowerCase().split(/[-_]/)[0];
      if (LANGS.indexOf(primary) >= 0) return primary;
    }
    return "en";
  }

  function t(key) { return UI[lang][key]; }
  function fmt(s, map) {
    return s.replace(/\{(\w+)\}/g, function (_, k) { return map[k] != null ? map[k] : ""; });
  }

  function restoreCastsFromUrl() {
    var match = location.hash.match(/^#cast=([6789]{6})$/);
    if (match) casts = match[1].split("").map(Number);
  }

  function readingUrl() {
    var bin = casts.map(function (v) { return (v === 7 || v === 9) ? "1" : "0"; }).join("");
    var h = byBin[bin];
    if (!h) return location.href.split("#")[0];
    var base = location.href.split("#")[0].split("?")[0];
    var url = new URL("readings/" + lang + "/" + h.n + "/", base);
    url.searchParams.set("cast", casts.join(""));
    return url.href;
  }

  function resultUrl() {
    return location.href.split("#")[0].split("?")[0] + "#cast=" + casts.join("");
  }

  // ---------- randomness ----------
  function coinFlip() { // true = yang(3) reverse side, false = yin(2)
    var a = new Uint8Array(1);
    crypto.getRandomValues(a);
    return (a[0] & 1) === 1;
  }

  // ---------- i18n ----------
  function applyStatic() {
    document.documentElement.lang = UI[lang].htmlLang;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      var v = t(el.getAttribute("data-i18n"));
      if (typeof v === "string") el.textContent = v;
    });
    var sel = $("langSelect");
    if (sel && sel.value !== lang) sel.value = lang;
    renderPositionGuide();
    renderBuilder();
    updateStatus();
    if (!reading.hidden) renderReading();
  }

  function renderPositionGuide() {
    var container = $("positionCards");
    if (!container) return;
    container.innerHTML = t("positionNames").map(function (name, i) {
      return '<article class="position-card">' +
        '<span class="position-no">' + (i + 1) + '</span>' +
        '<div><h3>' + esc(name) + '</h3><p>' + esc(t("positionMeanings")[i]) + '</p></div>' +
      '</article>';
    }).join("");
  }

  function updateStatus() {
    if (casts.length >= 6) {
      castStatus.textContent = t("done");
    } else if (casts.length === 0) {
      castStatus.textContent = t("castPrompt");
    } else {
      castStatus.textContent = fmt(t("castNext"), { n: t("castNth")[casts.length] });
    }
  }

  // ---------- builder ----------
  function renderBuilder(newIdx) {
    builder.innerHTML = "";
    for (var i = 0; i < 6; i++) {
      var v = casts[i];
      var row = document.createElement("div");
      row.className = "b-line" + (v == null ? " empty" : "") + (i === newIdx ? " new" : "");
      var yang = v === 7 || v === 9;
      var segs = (v == null || yang)
        ? '<span class="seg"></span>'
        : '<span class="seg"></span><span class="seg"></span>';
      var mark = v === 9 ? "○" : v === 6 ? "×" : "";
      row.innerHTML =
        '<span class="b-idx">' + t("lineNames")[i] + "</span>" +
        '<span class="b-bar">' + segs + "</span>" +
        '<span class="b-mark">' + mark + "</span>";
      builder.appendChild(row);
    }
  }

  // ---------- casting ----------
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  function resetCoins() {
    coins.forEach(function (c) {
      c.classList.remove("tossed");
      c.querySelector(".coin-inner").style.transition = "none";
      c.querySelector(".coin-inner").style.transform = "rotateX(0deg)";
      // force reflow so the next animation restarts
      void c.offsetWidth;
      c.querySelector(".coin-inner").style.transition = "";
    });
    castResult.textContent = "";
  }

  async function castOnce() {
    if (busy || casts.length >= 6) return;
    busy = true;
    castBtn.disabled = true;
    autoBtn.disabled = true;

    resetCoins();

    // shake the shell
    shell.classList.remove("shaking", "pouring");
    void shell.offsetWidth;
    shell.classList.add("shaking");
    await sleep(900);
    shell.classList.remove("shaking");
    shell.classList.add("pouring");
    await sleep(420);

    // toss coins
    var flips = [coinFlip(), coinFlip(), coinFlip()];
    coins.forEach(function (c, i) {
      c.style.setProperty("--drift", (i - 1) * 34 + (Math.random() * 24 - 12) + "px");
      c.style.setProperty("--spin", (Math.random() * 40 - 20) + "deg");
      c.style.animationDelay = i * 0.12 + "s";
      c.classList.add("tossed");
      var spins = 4 + ((Math.random() * 3) | 0);
      var deg = spins * 360 + (flips[i] ? 0 : 180);
      var inner = c.querySelector(".coin-inner");
      setTimeout(function () { inner.style.transform = "rotateX(" + deg + "deg)"; }, 80 + i * 120);
    });
    await sleep(700); // let the pour animation finish
    shell.classList.remove("pouring");
    await sleep(750); // wait for coin flips to settle

    var sum = flips.reduce(function (s, f) { return s + (f ? 3 : 2); }, 0);
    casts.push(sum);
    var idx = casts.length - 1;

    castResult.innerHTML = fmt(t("sumIs"), {
      s: "<strong>" + sum + "</strong>",
      v: "<strong>" + t("valueNames")[sum] + "</strong>"
    });
    renderBuilder(idx);
    updateStatus();
    await sleep(500);

    busy = false;
    if (casts.length >= 6) {
      castBtn.hidden = true;
      autoBtn.hidden = true;
      resetBtn.hidden = false;
      shell.classList.add("empty");
      await sleep(400);
      renderReading();
      reading.hidden = false;
      reading.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      castBtn.disabled = false;
      autoBtn.disabled = false;
      if (autoMode) castOnce();
    }
  }

  function reset() {
    casts = [];
    autoMode = false;
    busy = false;
    castBtn.hidden = false;
    castBtn.disabled = false;
    autoBtn.hidden = false;
    autoBtn.disabled = false;
    resetBtn.hidden = true;
    shell.classList.remove("empty");
    reading.hidden = true;
    readingBody.innerHTML = "";
    builderNote.textContent = "";
    if (history.replaceState) {
      history.replaceState(null, "", location.pathname + location.search);
    }
    resetCoins();
    renderBuilder();
    updateStatus();
    $("stage").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  // ---------- reading ----------
  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function escAttr(s) {
    return esc(s).replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function symbolHtml(bin, changing) {
    var html = '<div class="rd-sym" aria-hidden="true">';
    for (var i = 0; i < 6; i++) {
      var yang = bin[i] === "1";
      var chg = changing && changing.indexOf(i) >= 0;
      html += '<span class="l' + (chg ? " chg" : "") + '">' +
        (yang ? "<i></i>" : "<i></i><i></i>") + "</span>";
    }
    return html + "</div>";
  }

  function headHtml(h, bin, changing) {
    return '<div class="rd-head">' +
      symbolHtml(bin, changing) +
      '<div class="rd-title">' +
        '<div class="rd-no">' + fmt(t("hexNo"), { n: h.n }) + "</div>" +
        "<h2>" + esc(h.nm[lang]) + "</h2>" +
        '<div class="rd-zi">' + esc(h.nm.zh) + "（" + esc(h.zi) + "）</div>" +
      "</div></div>";
  }

  function shareHtml(h) {
    var url = readingUrl();
    var text = fmt(t("shareText"), { n: h.n, name: h.nm[lang] });
    var lineUrl = "https://social-plugins.line.me/lineit/share?url=" +
      encodeURIComponent(url) + "&text=" + encodeURIComponent(text);
    return '<div class="rd-share">' +
      '<h3>' + esc(t("shareTitle")) + '</h3>' +
      '<p>' + esc(t("shareIntro")) + '</p>' +
      '<div class="rd-share-actions">' +
        '<button class="share-btn share-native" type="button" data-share="native">' +
          '<span aria-hidden="true">↗</span>' + esc(t("shareBtn")) + '</button>' +
        '<a class="share-btn share-line" href="' + escAttr(lineUrl) +
          '" target="_blank" rel="noopener noreferrer">LINE</a>' +
        '<button class="share-btn" type="button" data-share="copy">' +
          '<span aria-hidden="true">⧉</span><span class="copy-label">' + esc(t("copyLink")) + '</span></button>' +
      '</div></div>';
  }

  function renderReading() {
    if (casts.length < 6) return;
    var bin = casts.map(function (v) { return (v === 7 || v === 9) ? "1" : "0"; }).join("");
    var tbin = casts.map(function (v) {
      return (v === 9) ? "0" : (v === 6) ? "1" : (v === 7 ? "1" : "0");
    }).join("");
    var changing = [];
    casts.forEach(function (v, i) { if (v === 6 || v === 9) changing.push(i); });

    var h = byBin[bin];
    var th = byBin[tbin];
    if (!h) { readingBody.textContent = "data error: " + bin; return; }

    var html = '<div class="rd-no" style="letter-spacing:.3em;color:var(--vermilion);margin-bottom:.6rem">' +
      esc(t("readingFor")) + " · " + esc(t("primary")) + "</div>";
    html += headHtml(h, bin, changing);

    // judgment
    html += '<div class="rd-sec"><span class="rd-label">' + esc(t("judgment")) + "</span>" +
      '<p class="rd-classical">' + esc(h.g) + "</p>" +
      '<p class="rd-plain">' + esc(h.gx[lang]) + "</p></div>";

    // lines
    html += '<div class="rd-sec"><span class="rd-label">' + esc(t("linesTitle")) + "</span>" +
      '<ul class="rd-lines">';
    h.ls.forEach(function (l, i) {
      var chg = changing.indexOf(i) >= 0;
      var changeHelp = chg
        ? '<span class="chg-badge">' + esc(t("changing")) + '</span>' +
          '<button class="chg-help" type="button" aria-label="' + escAttr(t("changingHelpLabel")) +
          '" data-tooltip="' + escAttr(t("changingHelp")) + '">?</button>'
        : "";
      html += "<li" + (chg ? ' class="chg"' : "") + ">" +
        '<div class="rd-line-t">' + esc(l[0]) + changeHelp + "</div>" +
        '<div class="rd-line-x">' + esc(l[1][lang]) + "</div></li>";
    });
    html += "</ul></div>";

    // all six changing → 用九 / 用六
    if (changing.length === 6 && h.u) {
      html += '<div class="rd-sec rd-transform">' +
        '<p class="rd-plain" style="margin-top:0">' +
        esc(fmt(t("allChanging"), { u: h.u[0].split("：")[0] })) + "</p>" +
        '<p class="rd-classical" style="margin-top:.6rem">' + esc(h.u[0]) + "</p>" +
        '<p class="rd-plain">' + esc(h.u[1][lang]) + "</p></div>";
    }

    // transformed hexagram
    if (changing.length === 0) {
      html += '<p class="rd-note">' + esc(t("noChanging")) + "</p>";
    } else if (th && th !== h) {
      html += '<div class="rd-sec rd-transform">' +
        '<span class="rd-label" style="background:var(--vermilion)">' + esc(t("transformTitle")) + "</span>" +
        '<p class="rd-plain" style="margin:.2rem 0 1rem">' + esc(t("transformIntro")) + "</p>" +
        headHtml(th, tbin, null) +
        '<p class="rd-classical">' + esc(th.g) + "</p>" +
        '<p class="rd-plain">' + esc(th.gx[lang]) + "</p></div>";
    }

    html += shareHtml(h);
    html += '<div class="rd-seal"><span>易</span></div>';
    readingBody.innerHTML = html;
    if (history.replaceState) history.replaceState(null, "", resultUrl());
  }

  async function copyReadingLink(button) {
    var url = readingUrl();
    try {
      await navigator.clipboard.writeText(url);
    } catch (e) {
      var input = document.createElement("textarea");
      input.value = url;
      input.setAttribute("readonly", "");
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      input.remove();
    }
    var label = button.querySelector(".copy-label");
    if (label) {
      var original = label.textContent;
      label.textContent = t("copied");
      setTimeout(function () { label.textContent = original; }, 1800);
    }
  }

  readingBody.addEventListener("click", async function (event) {
    var button = event.target.closest("[data-share]");
    if (!button) return;
    var bin = casts.map(function (v) { return (v === 7 || v === 9) ? "1" : "0"; }).join("");
    var h = byBin[bin];
    if (!h) return;
    if (button.getAttribute("data-share") === "copy") {
      await copyReadingLink(button);
      return;
    }
    var shareData = {
      title: t("title") + " · " + h.nm[lang],
      text: fmt(t("shareText"), { n: h.n, name: h.nm[lang] }),
      url: readingUrl()
    };
    if (navigator.share) {
      try { await navigator.share(shareData); } catch (e) {}
    } else {
      await copyReadingLink(button);
    }
  });

  // ---------- events ----------
  castBtn.addEventListener("click", function () { autoMode = false; castOnce(); });
  autoBtn.addEventListener("click", function () { autoMode = true; castOnce(); });
  resetBtn.addEventListener("click", reset);
  $("langSelect").addEventListener("change", function () {
    lang = this.value;
    try { localStorage.setItem("yi-lang", lang); } catch (e) {}
    applyStatic();
  });

  // ---------- init ----------
  restoreCastsFromUrl();
  applyStatic();
  if (casts.length === 6) {
    castBtn.hidden = true;
    autoBtn.hidden = true;
    resetBtn.hidden = false;
    shell.classList.add("empty");
    renderReading();
    reading.hidden = false;
  }
})();
