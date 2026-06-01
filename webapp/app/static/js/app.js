// Wassily — app.js
// Responsibilities:
//   1. Hydrate .chart-embed elements via /api/chart/{key} + Plotly.newPlot
//   2. Code-block copy buttons (reads .raw-code textarea; matches narrative_service markup)
//   3. Global search (progressive enhancement on #site-search if present)
//   4. KaTeX fallback trigger (base.html fires it via onload; this is a safety net)
// NOTE: .table-embed hydration is owned by tables.js — do not duplicate here.
(function () {
  "use strict";

  // -----------------------------------------------------------------------
  // Chart hydration
  // -----------------------------------------------------------------------

  function dlButtons(dl) {
    if (!dl) return "";
    var b = '<span class="dl-btns">Download:';
    if (dl.csv)     b += ' <a href="' + dl.csv     + '">CSV</a>';
    if (dl.xlsx)    b += ' <a href="' + dl.xlsx    + '">XLSX</a>';
    if (dl.json)    b += ' <a href="' + dl.json    + '">JSON</a>';
    if (dl.parquet) b += ' <a href="' + dl.parquet + '">Parquet</a>';
    return b + "</span>";
  }

  function renderChart(el, payload) {
    var fig = payload.figure || {};
    el.innerHTML = "";

    // Plot holder
    var holder = document.createElement("div");
    holder.style.minHeight = "420px";
    el.appendChild(holder);

    if (fig.data && window.Plotly) {
      var layout = Object.assign({ margin: { t: 40, b: 60, l: 60, r: 20 } }, fig.layout || {});
      Plotly.newPlot(holder, fig.data, layout, {
        responsive: true,
        displaylogo: false,
        modeBarButtonsToRemove: ["lasso2d", "select2d"]
      });
    } else {
      holder.innerHTML =
        '<p style="color:#888;padding:24px;text-align:center">' +
        (payload.caption || "Chart unavailable.") + "</p>";
    }

    // Caption + download row
    var meta = document.createElement("div");
    meta.className = "chart-meta";
    meta.innerHTML =
      "<span>" + (payload.caption || "") + "</span>" +
      dlButtons(payload.download);
    el.appendChild(meta);
  }

  function hydrateChart(el) {
    var key = el.getAttribute("data-chart");
    var params = (el.getAttribute("data-params") || "").replace(/&amp;/g, "&");
    if (!key) return;

    // Loading state
    el.innerHTML = '<p class="chart-loading">Loading chart…</p>';

    // URL-encode the key so compound keys with colons (e.g. heatmap:2002:L)
    // pass through as path segments intact.  encodeURIComponent encodes ":"
    // but the FastAPI {chart_key:path} convertor accepts them after decode.
    // We encode each segment individually so "/" separators stay as-is (there
    // are none in chart keys, but be defensive).
    var encodedKey = key.split("/").map(encodeURIComponent).join("/");

    fetch("/api/chart/" + encodedKey + (params ? "?" + params : ""))
      .then(function (r) {
        if (!r.ok) { throw new Error("HTTP " + r.status); }
        return r.json();
      })
      .then(function (p) { renderChart(el, p); })
      .catch(function (err) {
        el.innerHTML =
          '<p class="chart-error">Failed to load chart (' + key + ').</p>';
        console.warn("chart load failed:", key, err);
      });
  }

  function hydrateAllCharts() {
    document.querySelectorAll(".chart-embed[data-chart]").forEach(hydrateChart);
  }

  // -----------------------------------------------------------------------
  // Table embed hydration — DELEGATED to tables.js
  // app.js only calls WassilyTables.hydrate; tables.js owns the logic.
  // -----------------------------------------------------------------------

  function hydrateAllTables() {
    var embeds = document.querySelectorAll(".table-embed[data-table]");
    if (!embeds.length) return;
    if (window.WassilyTables && window.WassilyTables.hydrate) {
      embeds.forEach(window.WassilyTables.hydrate);
    } else {
      // tables.js not ready yet — wait for its ready event
      document.addEventListener("wassily:tables-ready", function () {
        embeds.forEach(window.WassilyTables.hydrate);
      });
    }
  }

  // -----------------------------------------------------------------------
  // Code-block copy buttons
  //
  // Matches narrative_service.py markup exactly:
  //   <figure class="code-block">
  //     <figcaption>…
  //       <button class="copy-btn">copy</button>
  //       <a class="dl-code" href="/api/file/…" download>download</a>
  //     </figcaption>
  //     <div class="highlight">…</div>
  //     <textarea class="raw-code" hidden>…</textarea>
  //   </figure>
  //
  // The raw code is stored in the hidden textarea; copy reads it directly
  // (no network round-trip).
  // -----------------------------------------------------------------------

  function initCodeBlocks() {
    document.querySelectorAll(".copy-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        // Walk up to the containing <figure class="code-block">
        var fig = btn.closest("figure");
        if (!fig) return;

        var textarea = fig.querySelector(".raw-code");
        var text = textarea ? textarea.value : "";

        if (!navigator.clipboard) {
          // Fallback for insecure contexts
          try {
            var ta = document.createElement("textarea");
            ta.value = text;
            ta.style.position = "fixed";
            ta.style.opacity  = "0";
            document.body.appendChild(ta);
            ta.select();
            document.execCommand("copy");
            document.body.removeChild(ta);
            _flashCopyBtn(btn, "Copied!");
          } catch (_) {
            _flashCopyBtn(btn, "Error");
          }
          return;
        }

        navigator.clipboard.writeText(text).then(function () {
          _flashCopyBtn(btn, "Copied!");
        }).catch(function () {
          _flashCopyBtn(btn, "Error");
        });
      });
    });
  }

  function _flashCopyBtn(btn, msg) {
    var orig = btn.textContent;
    btn.textContent = msg;
    btn.disabled = true;
    setTimeout(function () {
      btn.textContent = orig;
      btn.disabled = false;
    }, 1500);
  }

  // -----------------------------------------------------------------------
  // KaTeX safety-net
  // base.html fires renderMathInElement via the auto-render script's onload.
  // This call runs after DOMContentLoaded as a second pass in case the
  // onload fired before late-inserted content appeared (narrative pages, etc.)
  // -----------------------------------------------------------------------

  function runKaTeX() {
    if (typeof renderMathInElement === "function") {
      renderMathInElement(document.body, {
        delimiters: [
          { left: "$$", right: "$$", display: true  },
          { left: "$",  right: "$",  display: false }
        ],
        throwOnError: false
      });
    }
  }

  // -----------------------------------------------------------------------
  // Global site search — progressive enhancement
  // Targets #site-search if it exists in the DOM; no-ops otherwise.
  // base.html does NOT currently include this element, so this is forward-
  // compatible for a future nav-bar search box addition.
  //
  // API shape:  GET /api/search?q=<term>
  //   -> { "sectors": [{"code": str, "name": str}, ...],
  //        "pages":   [{"title": str, "url": str}, ...] }
  //
  // Sector hit -> navigate to /tables?search={code}
  // Page hit   -> navigate to hit.url
  // -----------------------------------------------------------------------

  function initSiteSearch() {
    var input = document.getElementById("site-search");
    if (!input) return;  // not present — no-op

    // Create dropdown container
    var dropdown = document.createElement("div");
    dropdown.className = "search-dropdown";
    dropdown.style.display = "none";
    // Insert after the input
    input.parentNode.insertBefore(dropdown, input.nextSibling);

    var _searchTimer = null;
    var _lastQ = "";

    function doSearch(q) {
      q = q.trim();
      if (q === _lastQ) return;
      _lastQ = q;

      if (!q) {
        hideDropdown();
        return;
      }

      fetch("/api/search?q=" + encodeURIComponent(q))
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data) { hideDropdown(); return; }
          renderDropdown(data, q);
        })
        .catch(function () { hideDropdown(); });
    }

    function renderDropdown(data, q) {
      dropdown.innerHTML = "";

      var sectors = (data.sectors || []).slice(0, 8);
      var pages   = (data.pages   || []).slice(0, 4);

      if (!sectors.length && !pages.length) {
        dropdown.innerHTML =
          '<div class="search-dd-empty">No results for “' + _esc(q) + '”</div>';
      } else {
        if (sectors.length) {
          var sh = document.createElement("div");
          sh.className = "search-dd-group-label";
          sh.textContent = "Sectors";
          dropdown.appendChild(sh);
          sectors.forEach(function (sec) {
            var item = document.createElement("a");
            item.className = "search-dd-item";
            item.href = "/tables?search=" + encodeURIComponent(sec.code);
            item.innerHTML =
              '<span class="search-dd-code">' + _esc(sec.code) + "</span> " +
              '<span class="search-dd-name">' + _esc(sec.name) + "</span>";
            dropdown.appendChild(item);
          });
        }
        if (pages.length) {
          var ph = document.createElement("div");
          ph.className = "search-dd-group-label";
          ph.textContent = "Pages";
          dropdown.appendChild(ph);
          pages.forEach(function (pg) {
            var item = document.createElement("a");
            item.className = "search-dd-item";
            item.href = pg.url;
            item.textContent = pg.title;
            dropdown.appendChild(item);
          });
        }
      }

      dropdown.style.display = "";
    }

    function hideDropdown() {
      dropdown.style.display = "none";
      dropdown.innerHTML = "";
      _lastQ = "";
    }

    function _esc(s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    // Debounced input handler
    input.addEventListener("input", function () {
      clearTimeout(_searchTimer);
      _searchTimer = setTimeout(function () { doSearch(input.value); }, 280);
    });

    // Close on click-outside
    document.addEventListener("click", function (e) {
      if (!input.contains(e.target) && !dropdown.contains(e.target)) {
        hideDropdown();
      }
    });

    // Keyboard: Escape closes
    input.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { hideDropdown(); input.blur(); }
    });
  }

  // -----------------------------------------------------------------------
  // Entry point
  // -----------------------------------------------------------------------

  document.addEventListener("DOMContentLoaded", function () {
    hydrateAllCharts();
    hydrateAllTables();
    initCodeBlocks();
    initSiteSearch();
    runKaTeX();
  });

  // Expose for use by tables.js and external callers
  window.WassilyApp = {
    renderChart: renderChart,
    dlButtons:   dlButtons
  };

})();
