// Leontief — tables.js
// Responsibilities:
//   1. On /tables page: initialize and drive the full I-O Table Explorer.
//   2. On every page: hydrate .table-embed[data-year][data-matrix] elements
//      into compact read-only grids with an "Open in Explorer →" link.
// Depends on: Plotly (already loaded globally via base.html).
// Does NOT modify app.js, site.css, or any existing files.

(function () {
  "use strict";

  // -------------------------------------------------------------------------
  // Constants
  // -------------------------------------------------------------------------

  var MATRIX_DESCRIPTIONS = {
    Use:      "Use table — records how much each industry purchases from every other industry and from final demand categories.",
    Supply:   "Supply table — records how much of each commodity is produced (and imported) by each industry.",
    A:        "Direct requirements matrix — technical coefficients: how many dollars of each input are needed per dollar of output.",
    A_square: "Square direct requirements — the A matrix rearranged into a symmetric industry-by-industry form.",
    L:        "Total requirements matrix (Leontief inverse) — captures both direct and indirect input requirements: (I − A)⁻¹.",
    VA:       "Value-added shares — labour compensation, taxes on production, and gross operating surplus by sector.",
    FD:       "Final demand — Personal consumption, private investment, government spending, and exports by sector."
  };

  // -------------------------------------------------------------------------
  // URL param helpers
  // -------------------------------------------------------------------------

  function getParams() {
    var sp = new URLSearchParams(window.location.search);
    return {
      year:   parseInt(sp.get("year")   || "2024", 10),
      matrix: sp.get("matrix") || "L",
      agg:    sp.get("agg")    || "",
      view:   sp.get("view")   || "heatmap",
      search: sp.get("search") || ""
    };
  }

  function pushParams(p) {
    var sp = new URLSearchParams();
    sp.set("year",   String(p.year));
    sp.set("matrix", p.matrix);
    if (p.agg)    { sp.set("agg",    p.agg); }
    if (p.view)   { sp.set("view",   p.view); }
    if (p.search) { sp.set("search", p.search); }
    var newUrl = window.location.pathname + "?" + sp.toString();
    if (newUrl !== window.location.pathname + window.location.search) {
      history.replaceState(null, "", newUrl);
    }
  }

  // -------------------------------------------------------------------------
  // Debounce utility
  // -------------------------------------------------------------------------

  function debounce(fn, ms) {
    var timer = null;
    return function () {
      var ctx = this, args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(ctx, args); }, ms);
    };
  }

  // -------------------------------------------------------------------------
  // Safe fetch — returns null on failure, calls onErr with message
  // -------------------------------------------------------------------------

  function safeFetch(url, onErr) {
    return fetch(url)
      .then(function (r) {
        if (!r.ok) { throw new Error("HTTP " + r.status + " for " + url); }
        return r.json();
      })
      .catch(function (err) {
        if (onErr) { onErr(String(err)); }
        return null;
      });
  }

  // -------------------------------------------------------------------------
  // Grid builder — shared between Explorer grid view and compact table-embeds
  // -------------------------------------------------------------------------

  function buildGrid(payload, searchHits) {
    var rows      = payload.rows;
    var cols      = payload.cols;
    var rowLabels = payload.index_names  || payload.index || [];
    var colCodes  = payload.columns      || [];
    var colLabels = payload.column_names || colCodes;
    var values    = payload.values       || [];
    var hitRows   = (searchHits && searchHits.rows) ? searchHits.rows : [];
    var hitCols   = (searchHits && searchHits.cols) ? searchHits.cols : [];

    // Build sets for O(1) lookup
    var hitRowSet = {};
    hitRows.forEach(function (r) { hitRowSet[r] = true; });
    var hitColSet = {};
    hitCols.forEach(function (c) { hitColSet[c] = true; });

    // Compute max abs value for colour scale
    var maxAbs = 0;
    for (var ri = 0; ri < values.length; ri++) {
      for (var ci = 0; ci < (values[ri] || []).length; ci++) {
        var v = Math.abs(values[ri][ci] || 0);
        if (v > maxAbs) { maxAbs = v; }
      }
    }

    var table = document.createElement("table");
    table.className = "io-grid";

    // -- Header row --
    var thead = document.createElement("thead");
    var headerRow = document.createElement("tr");

    var corner = document.createElement("th");
    corner.className = "corner";
    corner.textContent = "Sector";
    headerRow.appendChild(corner);

    for (var ci2 = 0; ci2 < cols; ci2++) {
      var th = document.createElement("th");
      var code = colCodes[ci2] || ("C" + ci2);
      var colName = colLabels[ci2] || "";
      // Header shows the human-readable sector NAME (not the BEA code/number);
      // the code is kept in the tooltip so it is never lost. Mirrors the row
      // label cell (rowName || rowCode).
      th.textContent = colName || code;
      th.title       = colName ? (code + " — " + colName) : code;
      if (hitColSet[ci2]) { th.className = "col-hit"; }
      headerRow.appendChild(th);
    }
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // -- Body rows --
    var tbody = document.createElement("tbody");
    for (var ri2 = 0; ri2 < rows; ri2++) {
      var tr = document.createElement("tr");

      // Row label cell (sticky first column)
      var labelCell = document.createElement("td");
      var rowName = rowLabels[ri2] || "";
      var rowCode = payload.index ? (payload.index[ri2] || "") : "";
      labelCell.textContent = rowName || rowCode;
      labelCell.title       = rowCode ? (rowCode + " — " + rowName) : rowName;
      if (hitRowSet[ri2]) { labelCell.className = "row-hit"; }
      tr.appendChild(labelCell);

      var rowVals = values[ri2] || [];
      for (var ci3 = 0; ci3 < cols; ci3++) {
        var td = document.createElement("td");
        td.className = "val-cell";
        var num = rowVals[ci3];
        if (num === null || num === undefined || num === "") {
          td.textContent = "—";
        } else {
          var n = Number(num);
          if (isNaN(n)) {
            td.textContent = num;
          } else {
            td.textContent = n.toLocaleString("en-US", {
              maximumFractionDigits: 4,
              minimumFractionDigits: 0
            });
            // Subtle heat colouring (teal tint scaled to cell magnitude)
            if (maxAbs > 0) {
              var intensity = Math.abs(n) / maxAbs;
              var alpha = Math.round(intensity * 55);
              td.style.backgroundColor =
                "rgba(33,122,107," + (alpha / 255).toFixed(3) + ")";
            }
            if (hitRowSet[ri2] && hitColSet[ci3]) {
              td.classList.add("cell-hit");
            }
          }
        }
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    return table;
  }

  // -------------------------------------------------------------------------
  // Explorer — main controller (only active on /tables)
  // -------------------------------------------------------------------------

  function initExplorer() {
    // DOM refs
    var ctrlYear   = document.getElementById("ctrl-year");
    var ctrlMatrix = document.getElementById("ctrl-matrix");
    var ctrlAgg    = document.getElementById("ctrl-agg");
    var ctrlView   = document.getElementById("ctrl-view");
    var ctrlSearch = document.getElementById("ctrl-search");

    var captionEl  = document.getElementById("explorer-caption");
    var labelEl    = document.getElementById("caption-label");
    var descEl     = document.getElementById("caption-desc");
    var dimsEl     = document.getElementById("caption-dims");

    var statusEl   = document.getElementById("explorer-status");
    var heatmapEl  = document.getElementById("explorer-heatmap");
    var heatPlotEl = document.getElementById("heatmap-plot");
    var gridEl     = document.getElementById("explorer-grid");
    var gridInner  = document.getElementById("grid-inner");

    var searchBanner    = document.getElementById("search-banner");
    var searchBannerTxt = document.getElementById("search-banner-text");
    var searchClearBtn  = document.getElementById("search-clear");

    var dlBulk    = document.getElementById("dl-bulk");
    var dlBulkYr  = document.getElementById("dl-bulk-year");
    var dlCsv     = document.getElementById("dl-csv");
    var dlXlsx    = document.getElementById("dl-xlsx");
    var dlParquet = document.getElementById("dl-parquet");

    if (!ctrlYear) { return; }  // not on /tables

    // State object — source of truth for current selection
    var state = getParams();

    // Apply URL state to controls
    function applyStateToControls() {
      ctrlYear.value   = String(state.year);
      ctrlMatrix.value = state.matrix;
      ctrlAgg.value    = state.agg;
      ctrlView.value   = state.view;
      ctrlSearch.value = state.search;
    }

    // Update all download link hrefs for current (year, matrix)
    function updateDownloadLinks() {
      var base = "/api/table/" + state.year + "/" + state.matrix;
      dlCsv.href     = base + ".csv";
      dlXlsx.href    = base + ".xlsx";
      dlParquet.href = base + ".parquet";
      dlBulk.href    = "/api/bulk/" + state.year + ".zip";
      dlBulkYr.textContent = String(state.year);
    }

    // Show/hide the two view panels
    function setViewPanels(view) {
      if (view === "heatmap") {
        heatmapEl.style.display = "";
        gridEl.style.display    = "none";
      } else {
        heatmapEl.style.display = "none";
        gridEl.style.display    = "";
      }
    }

    // Status helpers
    function showStatus(msg, isError) {
      statusEl.textContent = msg;
      statusEl.className   = "explorer-status" + (isError ? " error" : "");
      statusEl.style.display  = "";
      heatmapEl.style.display = "none";
      gridEl.style.display    = "none";
      if (captionEl) { captionEl.style.display = "none"; }
    }

    function hideStatus() {
      statusEl.style.display = "none";
    }

    // Caption bar update
    function updateCaption(payload) {
      if (!captionEl) { return; }
      labelEl.textContent = payload.label || (state.matrix + " matrix, " + state.year);
      descEl.textContent  = MATRIX_DESCRIPTIONS[state.matrix] || "";
      dimsEl.textContent  = payload.rows + " × " + payload.cols + " matrix";
      captionEl.style.display = "";
    }

    // Search banner update
    function updateSearchBanner(searchHits, searchTerm) {
      if (!searchBanner) { return; }
      if (!searchTerm ||
          (!searchHits.rows.length && !searchHits.cols.length)) {
        searchBanner.style.display = "none";
        return;
      }
      var nRows  = searchHits.rows.length;
      var nCols  = searchHits.cols.length;
      var total  = nRows + nCols;
      searchBannerTxt.textContent =
        "“" + searchTerm + "” — " +
        total + " match" + (total !== 1 ? "es" : "") +
        " (" + nRows + " row" + (nRows !== 1 ? "s" : "") +
        ", " + nCols + " col" + (nCols !== 1 ? "s" : "") + ")";
      searchBanner.style.display = "";
    }

    // -----------------------------------------------------------------------
    // Main render — fetches table data; then drives heatmap or grid
    // -----------------------------------------------------------------------

    var _currentRender = 0;  // increment to cancel stale in-flight fetches

    function render() {
      pushParams(state);
      applyStateToControls();
      updateDownloadLinks();

      var token = ++_currentRender;
      showStatus("Loading…");

      // Build table API URL
      var tUrl = "/api/table/" + state.year + "/" + state.matrix;
      var tQs  = [];
      if (state.agg)    { tQs.push("agg="    + encodeURIComponent(state.agg)); }
      if (state.search) { tQs.push("search=" + encodeURIComponent(state.search)); }
      if (tQs.length)   { tUrl += "?" + tQs.join("&"); }

      safeFetch(tUrl, function (err) {
        if (token !== _currentRender) { return; }
        showStatus("Failed to load matrix data: " + err, true);
      }).then(function (payload) {
        if (!payload || token !== _currentRender) { return; }

        hideStatus();
        updateCaption(payload);
        updateSearchBanner(
          payload.search_hits || {rows: [], cols: []},
          state.search
        );
        setViewPanels(state.view);

        if (state.view === "heatmap") {
          renderHeatmap(token, payload);
        } else {
          renderGrid(payload);
        }
      });
    }

    // -----------------------------------------------------------------------
    // Heatmap — prefers chart API; falls back to client-side Plotly heatmap
    // -----------------------------------------------------------------------

    // Render the chart title as HTML above the plot (wraps responsively, unlike the
    // Plotly SVG title which truncates on narrow screens — DNA graph contract).
    function setHeatmapTitle(t) {
      var el = document.getElementById("heatmap-title");
      if (!el && heatPlotEl && heatPlotEl.parentNode) {
        el = document.createElement("div");
        el.id = "heatmap-title"; el.className = "ark-chart-title";
        el.style.margin = "0 0 8px";
        heatPlotEl.parentNode.insertBefore(el, heatPlotEl);
      }
      if (el) el.textContent = t || "";
    }

    function renderHeatmap(token, tablePayload) {
      var suffix   = state.agg ? (":" + state.agg) : "";
      var chartKey = "heatmap:" + state.year + ":" + state.matrix + suffix;

      safeFetch("/api/chart/" + chartKey, null)
        .then(function (data) {
          if (token !== _currentRender) { return; }
          if (data && data.figure && data.figure.data && window.Plotly) {
            var srvLayout = data.figure.layout || {};
            var title = (srvLayout.title && (srvLayout.title.text ||
                         (typeof srvLayout.title === "string" ? srvLayout.title : ""))) || "";
            setHeatmapTitle(title);   // HTML title (wraps) instead of the truncating Plotly SVG title
            var layout = Object.assign(
              { margin: { t: 16, b: 120, l: 160, r: 20 }, autosize: true },
              srvLayout
            );
            delete layout.title;
            // Theme + dark-aware re-theming via the kit (ArkPlotly registers the div).
            if (window.ArkPlotly) {
              ArkPlotly.plot(heatPlotEl, data.figure.data, layout,
                             { filename: chartKey.replace(/[^a-z0-9]+/gi, "_") });
            } else {
              Plotly.newPlot(heatPlotEl, data.figure.data, layout, {
                responsive: true,
                displaylogo: false,
                modeBarButtonsToRemove: ["lasso2d", "select2d"]
              });
            }
          } else {
            // Chart API unavailable or returned incomplete data — build client-side
            renderClientHeatmap(token, tablePayload);
          }
        });
    }

    function renderClientHeatmap(token, payload) {
      if (token !== _currentRender) { return; }
      if (!window.Plotly) {
        heatPlotEl.innerHTML =
          "<p style='padding:24px;color:#888;text-align:center'>" +
          "Plotly unavailable — switch to Grid view.</p>";
        return;
      }

      var rowLabels = payload.index_names  || payload.index   || [];
      var colLabels = payload.column_names || payload.columns || [];
      var values    = payload.values       || [];

      var traces = [{
        type: "heatmap",
        z:    values,
        x:    colLabels,
        y:    rowLabels,
        colorscale: "Teal",
        reversescale: false,
        showscale: true
      }];
      var layout = {
        margin: { t: 50, b: 120, l: 200, r: 40 },
        xaxis: { tickangle: -45, tickfont: { size: 9 } },
        yaxis: { tickfont: { size: 9 }, autorange: "reversed" },
        autosize: true
      };
      if (window.ArkPlotly) {
        ArkPlotly.plot(heatPlotEl, traces, layout, { filename: "io_heatmap" });
      } else {
        Plotly.newPlot(heatPlotEl, traces, layout,
          { responsive: true, displaylogo: false,
            modeBarButtonsToRemove: ["lasso2d", "select2d"] });
      }
    }

    // -----------------------------------------------------------------------
    // Grid view
    // -----------------------------------------------------------------------

    function renderGrid(payload) {
      gridInner.innerHTML = "";
      var table = buildGrid(
        payload,
        payload.search_hits || {rows: [], cols: []}
      );
      gridInner.appendChild(table);
    }

    // -----------------------------------------------------------------------
    // Control event listeners
    // -----------------------------------------------------------------------

    ctrlYear.addEventListener("change", function () {
      state.year = parseInt(this.value, 10);
      render();
    });

    ctrlMatrix.addEventListener("change", function () {
      state.matrix = this.value;
      render();
    });

    ctrlAgg.addEventListener("change", function () {
      state.agg = this.value;
      render();
    });

    ctrlView.addEventListener("change", function () {
      state.view = this.value;
      render();
    });

    var debouncedSearch = debounce(function () {
      state.search = ctrlSearch.value.trim();
      render();
    }, 350);

    ctrlSearch.addEventListener("input", debouncedSearch);

    if (searchClearBtn) {
      searchClearBtn.addEventListener("click", function () {
        ctrlSearch.value = "";
        state.search     = "";
        render();
      });
    }

    // Initial render
    applyStateToControls();
    render();
  }

  // -------------------------------------------------------------------------
  // Compact table-embed hydration (global — fires on every page)
  // Hydrates: <div class="table-embed" data-year="..." data-matrix="..."
  //                                    data-agg="...">
  // Note: app.js also calls LeontiefTables.hydrate for .table-embed[data-table]
  // -------------------------------------------------------------------------

  // Cap a matrix payload to a small preview slice so a compact embed NEVER inlines a
  // huge grid (DNA TABLE_RENDERING_STANDARD: the full matrix lives in the Explorer).
  function _previewPayload(p, maxR, maxC) {
    var totalR = p.rows || (p.values ? p.values.length : 0);
    var totalC = p.cols || ((p.values && p.values[0]) ? p.values[0].length : 0);
    var R = Math.min(maxR, totalR), C = Math.min(maxC, totalC);
    var out = {}; for (var k in p) out[k] = p[k];
    out.rows = R; out.cols = C;
    if (p.columns)      out.columns      = p.columns.slice(0, C);
    if (p.column_names) out.column_names = p.column_names.slice(0, C);
    if (p.index_names)  out.index_names  = p.index_names.slice(0, R);
    if (p.index)        out.index        = p.index.slice(0, R);
    if (p.values)       out.values       = p.values.slice(0, R).map(function (row) { return (row || []).slice(0, C); });
    return { p: out, truncated: (totalR > R || totalC > C), R: R, C: C, totalR: totalR, totalC: totalC };
  }

  function hydrateTableEmbed(el) {
    // Support both data-year/data-matrix attributes AND legacy data-table="YEAR/MATRIX"
    var year, matrix, agg;
    if (el.getAttribute("data-year")) {
      year   = el.getAttribute("data-year")   || "2024";
      matrix = el.getAttribute("data-matrix") || "L";
      agg    = el.getAttribute("data-agg")    || "";
    } else if (el.getAttribute("data-table")) {
      var parts = (el.getAttribute("data-table") || "").split("/");
      year   = parts[0] || "2024";
      matrix = parts[1] || "L";
      agg    = el.getAttribute("data-agg") || "";
    } else {
      return;  // nothing to hydrate
    }

    // Prevent double-init
    if (el.dataset.hydrated) { return; }
    el.dataset.hydrated = "1";

    // Build wrapper markup
    el.innerHTML = "";
    var wrapper = document.createElement("div");
    wrapper.className = "table-embed-compact";

    var header = document.createElement("div");
    header.className = "tec-header";

    var titleSpan = document.createElement("span");
    titleSpan.className   = "tec-title";
    titleSpan.textContent =
      matrix + " matrix, " + year + (agg ? " (" + agg + "-sector)" : "");

    var explorerUrl =
      "/tables?year=" + encodeURIComponent(year) +
      "&matrix=" + encodeURIComponent(matrix) +
      (agg ? "&agg=" + encodeURIComponent(agg) : "");

    var openLink = document.createElement("a");
    openLink.className   = "tec-open";
    openLink.href        = explorerUrl;
    openLink.textContent = "Open in Explorer →";

    header.appendChild(titleSpan);
    header.appendChild(openLink);
    wrapper.appendChild(header);

    var body = document.createElement("div");
    body.className = "tec-body";

    var loadingP = document.createElement("p");
    loadingP.className   = "tec-loading";
    loadingP.textContent = "Loading…";
    body.appendChild(loadingP);
    wrapper.appendChild(body);
    el.appendChild(wrapper);

    // Fetch and render
    var url = "/api/table/" + encodeURIComponent(year) +
              "/" + encodeURIComponent(matrix);
    if (agg) { url += "?agg=" + encodeURIComponent(agg); }

    safeFetch(url, function (err) {
      loadingP.remove();
      var errP = document.createElement("p");
      errP.className   = "tec-error";
      errP.textContent = "Failed to load matrix: " + err;
      body.appendChild(errP);
    }).then(function (payload) {
      if (!payload) { return; }
      loadingP.remove();
      if (payload.label) { titleSpan.textContent = payload.label; }
      // Compact PREVIEW only — never inline a huge matrix; the full grid is one click
      // away via "Open in Explorer →" (DNA table standard).
      var prev = _previewPayload(payload, 8, 8);
      // Wrap the matrix preview in a focusable scroll region (matrices don't reflow to
      // cards well) so a narrow viewport scrolls it accessibly instead of overflowing.
      var grid = buildGrid(prev.p, {rows: [], cols: []});
      var gwrap = document.createElement("div");
      gwrap.className = "ark-table-wrap";
      gwrap.setAttribute("role", "region");
      gwrap.setAttribute("tabindex", "0");
      gwrap.setAttribute("aria-label", "matrix preview (scrollable)");
      gwrap.appendChild(grid);
      body.appendChild(gwrap);
      if (prev.truncated) {
        var note = document.createElement("p");
        note.className = "tec-note";
        note.style.cssText = "margin:8px 0 0;font-size:.85rem;color:var(--ark-fg-dim)";
        note.textContent = "Preview: " + prev.R + "×" + prev.C + " of the full " +
          prev.totalR + "×" + prev.totalC + " matrix — use “Open in Explorer” for the complete table.";
        body.appendChild(note);
      }
    });
  }

  function hydrateAllTableEmbeds() {
    // Hydrate .table-embed elements that carry data-year/data-matrix/data-table
    document.querySelectorAll(
      ".table-embed[data-year], .table-embed[data-matrix], .table-embed[data-table]"
    ).forEach(hydrateTableEmbed);
  }

  // -------------------------------------------------------------------------
  // Entry point
  // -------------------------------------------------------------------------

  var _ready = false;

  function onReady() {
    if (_ready) { return; }
    _ready = true;

    // Explorer (only active on /tables page where ctrl-year exists)
    if (document.getElementById("ctrl-year")) {
      initExplorer();
    }

    // Global compact table-embed hydration
    hydrateAllTableEmbeds();

    // Expose API for app.js delegation
    window.LeontiefTables = {
      hydrate:    hydrateTableEmbed,
      hydrateAll: hydrateAllTableEmbeds
    };

    // Signal ready so app.js can delegate to us
    document.dispatchEvent(new CustomEvent("leontief:tables-ready"));
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onReady);
  } else {
    onReady();
  }

})();
