const SECTOR_LINKS = [
  ["Communication Services", "XLC"], ["Consumer Discretionary", "XLY"], ["Consumer Staples", "XLP"],
  ["Energy", "XLE"], ["Financials", "XLF"], ["Health Care", "XLV"], ["Industrials", "XLI"],
  ["Materials", "XLB"], ["Real Estate", "XLRE"], ["Technology", "XLK"], ["Utilities", "XLU"]
];
const ASSET_LINKS = [
  ["Commodities", "commodities"], ["Intl Developed Markets", "international-developed"],
  ["REIT", "real-estate"], ["Gold", "gold"], ["Emerging Markets", "emerging-markets"],
  ["US Stock Market", "us-equities"], ["Short Treasuries", "short-treasuries"],
  ["Total Bond Market", "total-bond-market"], ["Intermediate Treasuries", "treasuries"],
  ["Long Treasuries", "long-treasuries"], ["Global Bonds", "global-bonds"]
];
const COUNTRY_LINKS = [
  ["Australia", "australia"], ["Brazil", "brazil"], ["Canada", "canada"], ["China", "china"],
  ["France", "france"], ["Germany", "germany"], ["Italy", "italy"], ["Japan", "japan"],
  ["South Korea", "south-korea"], ["Switzerland", "switzerland"],
  ["United Kingdom", "united-kingdom"], ["United States", "united-states"]
];

function populateMenu(id, items, hrefFor) {
  const menu = document.getElementById(id);
  if (!menu) return;
  menu.replaceChildren(...items.map(([label, value]) => {
    const link = document.createElement("a");
    link.className = "dropdown-item";
    link.href = hrefFor(value);
    link.textContent = label;
    return link;
  }));
}

function setupDropdown(dropdownId, toggleId) {
  const dropdown = document.getElementById(dropdownId);
  const toggle = document.getElementById(toggleId);
  if (!dropdown || !toggle) return;
  const close = () => { dropdown.classList.remove("is-open"); toggle.setAttribute("aria-expanded", "false"); };
  toggle.addEventListener("click", (event) => {
    event.stopPropagation();
    const open = !dropdown.classList.contains("is-open");
    document.querySelectorAll(".dropdown-menu").forEach((menu) => menu.classList.remove("is-open"));
    document.querySelectorAll(".dropdown-icon-toggle").forEach((button) => button.setAttribute("aria-expanded", "false"));
    if (open) { dropdown.classList.add("is-open"); toggle.setAttribute("aria-expanded", "true"); }
  });
  dropdown.addEventListener("keydown", (event) => {
    if (event.key === "Escape") { close(); toggle.focus(); }
  });
}

function ensureCountriesDropdown() {
  if (document.getElementById("countriesDropdown")) return;
  const link = document.querySelector('.nav-links > a[href="countries.html"]');
  if (!link) return;
  const dropdown = document.createElement("div"); dropdown.className = "dropdown dropdown-menu dropdown-split"; dropdown.id = "countriesDropdown";
  link.classList.add("nav-split-link");
  const toggle = document.createElement("button"); toggle.className = "dropdown-icon-toggle"; toggle.id = "countriesToggle"; toggle.type = "button"; toggle.setAttribute("aria-label", "Open countries menu"); toggle.setAttribute("aria-expanded", "false"); toggle.textContent = "▼";
  const menu = document.createElement("div"); menu.className = "dropdown-panel"; menu.id = "countriesMenu";
  link.replaceWith(dropdown); dropdown.append(link, toggle, menu);
}

function initNavigation() {
  ensureCountriesDropdown();
  populateMenu("sectorsMenu", SECTOR_LINKS, (symbol) => `sector.html?symbol=${encodeURIComponent(symbol)}`);
  populateMenu("assetClassesMenu", ASSET_LINKS, (key) => `asset-class.html?key=${encodeURIComponent(key)}`);
  populateMenu("countriesMenu", COUNTRY_LINKS, (key) => `asset-class.html?group=countries&key=${encodeURIComponent(key)}`);
  setupDropdown("sectorsDropdown", "sectorsToggle");
  setupDropdown("assetClassesDropdown", "assetClassesToggle");
  setupDropdown("countriesDropdown", "countriesToggle");
  document.addEventListener("click", (event) => {
    if (event.target.closest(".dropdown-menu")) return;
    document.querySelectorAll(".dropdown-menu").forEach((menu) => menu.classList.remove("is-open"));
    document.querySelectorAll(".dropdown-icon-toggle").forEach((button) => button.setAttribute("aria-expanded", "false"));
  });
}

function initTickerSearch() {
  const form = document.querySelector(".nav-search");
  const input = form?.querySelector(".search-input");
  if (!form || !input) return;
  const current = new URLSearchParams(location.search).get("symbol")?.trim().toUpperCase();
  if (current && /^[A-Z][A-Z0-9.-]{0,9}$/.test(current)) input.value = current;
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const symbol = input.value.trim().toUpperCase();
    if (!/^[A-Z][A-Z0-9.-]{0,9}$/.test(symbol)) {
      input.setCustomValidity("Enter a valid US stock or ETF symbol.");
      input.reportValidity();
      return;
    }
    input.setCustomValidity("");
    location.assign(`/index.html?symbol=${encodeURIComponent(symbol)}`);
  });
  input.addEventListener("input", () => input.setCustomValidity(""));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") { event.preventDefault(); form.requestSubmit(); }
  });
}

function formatKs(value) {
  if (!Number.isFinite(Number(value))) return "--";
  const number = Number(value);
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: number >= 1000 ? 0 : 1 }).format(number);
}

async function initMarketTicker() {
  const eligiblePages = new Set(["research", "sector-detail", "asset-detail", "rankings", "countries"]);
  if (!eligiblePages.has(document.body.dataset.page)) return;
  const navbar = document.querySelector(".navbar");
  if (!navbar || document.querySelector(".market-ticker")) return;
  const ticker = document.createElement("section");
  ticker.className = "market-ticker";
  ticker.setAttribute("aria-label", "Bitcoin-denominated market prices");
  const viewport = document.createElement("div"); viewport.className = "market-ticker-viewport";
  const track = document.createElement("div"); track.className = "market-ticker-track";
  const loading = document.createElement("span"); loading.className = "market-ticker-loading"; loading.textContent = "Loading Bitcoin-denominated market prices…";
  track.append(loading); viewport.append(track); ticker.append(viewport); navbar.insertAdjacentElement("afterend", ticker);
  try {
    const response = await fetch("/api/ticker", { cache: "no-store" });
    const payload = await response.json(); if (!response.ok) throw new Error(payload.error || "Market ticker unavailable.");
    const makeGroup = () => {
      const group = document.createElement("div"); group.className = "market-ticker-group";
      payload.items.forEach((item) => {
        const quote = document.createElement("span"); quote.className = "market-ticker-quote"; quote.title = `${item.symbol} · ${payload.source} · as of ${formatDate(item.asOf)}`;
        const label = document.createElement("strong"); label.textContent = `${item.label}/kS`;
        const value = document.createElement("span"); value.textContent = formatKs(item.valueKs);
        const change = document.createElement("span"); change.className = Number(item.change) >= 0 ? "positive-text" : "negative-text"; change.textContent = formatPercent(item.change, 2);
        quote.append(label, value, change); group.append(quote);
      });
      return group;
    };
    track.replaceChildren(makeGroup(), makeGroup());
  } catch (error) {
    loading.textContent = "Market prices are temporarily unavailable."; loading.classList.add("is-error");
  }
}

function initUnitGuideLink() {
  document.querySelectorAll('.site-footer-links a[href="why-bitcoin.html"],.site-footer-links a[href="ks.html"]').forEach((link) => link.remove());
  const navLeft = document.querySelector(".nav-left");
  if (!navLeft || navLeft.querySelector(".nav-education")) return;
  const education = document.createElement("div"); education.className = "nav-education"; education.setAttribute("aria-label", "About SatValue");
  const links = [["Why Bitcoin?", "why-bitcoin.html"], ["What is kS?", "ks.html"]];
  links.forEach(([label, href]) => {
    const link = document.createElement("a"); link.href = href; link.textContent = label;
    if (location.pathname.endsWith(`/${href}`) || location.pathname.endsWith(href)) link.classList.add("is-current");
    education.append(link);
  });
  navLeft.append(education);
}

function formatPercent(value, digits = 1) {
  if (!Number.isFinite(Number(value))) return "--";
  const number = Number(value);
  return `${number >= 0 ? "+" : ""}${number.toFixed(digits)}%`;
}

function formatDate(value) {
  if (!value) return "--";
  return new Date(`${value}T00:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
}

function shiftMonths(value, months) {
  const copy = new Date(value);
  const targetDay = copy.getUTCDate();
  copy.setUTCDate(1);
  copy.setUTCMonth(copy.getUTCMonth() - months);
  const lastDay = new Date(Date.UTC(copy.getUTCFullYear(), copy.getUTCMonth() + 1, 0)).getUTCDate();
  copy.setUTCDate(Math.min(targetDay, lastDay));
  return copy;
}

function aggregateWeekly(rawData) {
  const buckets = new Map();
  for (const point of rawData) {
    const date = new Date(`${point.time}T00:00:00Z`);
    const day = date.getUTCDay();
    date.setUTCDate(date.getUTCDate() + (day === 0 ? -6 : 1 - day));
    const key = date.toISOString().slice(0, 10);
    const prior = buckets.get(key);
    if (!prior) buckets.set(key, { ...point });
    else {
      prior.rawHigh = Math.max(prior.rawHigh, point.rawHigh);
      prior.rawLow = Math.min(prior.rawLow, point.rawLow);
      prior.rawClose = point.rawClose;
      prior.time = point.time;
    }
  }
  return [...buckets.values()];
}

function aggregateMonthly(rawData) {
  const buckets = new Map();
  for (const point of rawData) {
    const key = point.time.slice(0, 7);
    const prior = buckets.get(key);
    if (!prior) buckets.set(key, { ...point });
    else {
      prior.rawHigh = Math.max(prior.rawHigh, point.rawHigh);
      prior.rawLow = Math.min(prior.rawLow, point.rawLow);
      prior.rawClose = point.rawClose;
      prior.time = point.time;
    }
  }
  return [...buckets.values()];
}

function rangeCutoff(range, latest) {
  const date = new Date(latest);
  if (range === "1W") date.setUTCDate(date.getUTCDate() - 7);
  else if (range === "1M") return shiftMonths(latest, 1);
  else if (range === "3M") return shiftMonths(latest, 3);
  else if (range === "6M") return shiftMonths(latest, 6);
  else if (range === "1Y") return shiftMonths(latest, 12);
  else if (range === "3Y") return shiftMonths(latest, 36);
  else if (range === "5Y") return shiftMonths(latest, 60);
  else if (range === "10Y") return shiftMonths(latest, 120);
  else if (range === "YTD") return new Date(Date.UTC(latest.getUTCFullYear(), 0, 1));
  else return null;
  return date;
}

function dataForRange(range, daily, weekly, monthly) {
  if (["10Y", "MAX"].includes(range)) return monthly;
  return ["3Y", "5Y"].includes(range) ? weekly : daily;
}

function visibleStartIndex(range, data) {
  if (range === "MAX" || !data.length) return 0;
  const latest = new Date(`${data[data.length - 1].time}T00:00:00Z`);
  const cutoff = rangeCutoff(range, latest);
  const index = data.findIndex((point) => new Date(`${point.time}T00:00:00Z`) >= cutoff);
  return index < 0 ? 0 : Math.max(0, index - 1);
}

async function loadResearchSeries(symbol) {
  const response = await fetch(`/api/series?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.error || `Market data request failed (${response.status}).`);
  const bars = (payload.bars || []).map((point) => ({
    time: point.time,
    rawOpen: Number(point.open), rawHigh: Number(point.high), rawLow: Number(point.low), rawClose: Number(point.close)
  })).filter((point) => [point.rawOpen, point.rawHigh, point.rawLow, point.rawClose].every((value) => Number.isFinite(value) && value > 0));
  if (!bars.length) throw new Error("No aligned market history is available for this symbol.");
  return { ...payload, bars };
}

function selectedResearchSymbol(container) {
  if (document.body.dataset.page !== "research") return container.dataset.symbol || "SPY";
  const requested = new URLSearchParams(location.search).get("symbol")?.trim().toUpperCase();
  return requested && /^[A-Z][A-Z0-9.-]{0,9}$/.test(requested) ? requested : (container.dataset.symbol || "SPY");
}

function updateTrailingReturns(values = {}) {
  document.querySelectorAll(".returns-table tbody tr").forEach((row) => {
    const label = row.cells[0]?.textContent.trim();
    const cell = row.cells[1];
    if (!cell) return;
    const value = values[label];
    cell.textContent = formatPercent(value);
    cell.className = `right-align ${Number.isFinite(Number(value)) ? (Number(value) >= 0 ? "positive-text" : "negative-text") : "muted-text"}`;
  });
}

function renderResearchMetrics(payload) {
  const metrics = payload.metrics || {};
  const mappings = [["metricCagr", metrics.cagr], ["metricVolatility", metrics.annualizedVolatility], ["metricMaxDrawdown", metrics.maxDrawdown], ["metricCurrentDrawdown", metrics.currentDrawdown]];
  mappings.forEach(([id, value]) => { const node = document.getElementById(id); if (node) node.textContent = formatPercent(value); });
  const rows = document.getElementById("calendarReturnRows");
  if (rows) {
    const values = payload.calendarReturns || [];
    rows.replaceChildren(...(values.length ? values : [{ year: "--", return: null }]).map((item) => {
      const row = document.createElement("tr");
      const year = document.createElement("td"); const value = document.createElement("td");
      year.textContent = item.year; value.textContent = formatPercent(item.return); value.className = `right-align ${Number(item.return) >= 0 ? "positive-text" : "negative-text"}`;
      row.append(year, value); return row;
    }));
  }
  const quiltRows = document.getElementById("calendarQuiltRows");
  if (quiltRows) {
    const rowsData = payload.monthlyCalendarReturns || [];
    const finiteValues = rowsData.flatMap((item) => [...(item.months || []), item.ytd]).filter((value) => value !== null && Number.isFinite(Number(value))).map(Number);
    const maxGain = Math.max(0, ...finiteValues);
    const maxLoss = Math.abs(Math.min(0, ...finiteValues));
    const heatCell = (value) => {
      const cell = document.createElement("td");
      if (value === null || !Number.isFinite(Number(value))) {
        cell.textContent = "--"; cell.className = "is-empty"; return cell;
      }
      const number = Number(value); const scale = number >= 0 ? (maxGain ? number / maxGain : 0) : (maxLoss ? Math.abs(number) / maxLoss : 0);
      const alpha = .1 + Math.max(0, Math.min(1, scale)) * .68;
      cell.textContent = formatPercent(number);
      cell.style.backgroundColor = number >= 0 ? `rgba(16,185,129,${alpha})` : `rgba(239,68,68,${alpha})`;
      cell.style.color = scale > .62 ? "#fff" : (number >= 0 ? "#047857" : "#b91c1c");
      return cell;
    };
    quiltRows.replaceChildren(...(rowsData.length ? rowsData : [{ year: "--", months: Array(12).fill(null), ytd: null }]).map((item) => {
      const row = document.createElement("tr"); const year = document.createElement("td"); year.textContent = item.year; row.append(year);
      (item.months || Array(12).fill(null)).forEach((value) => row.append(heatCell(value))); row.append(heatCell(item.ytd)); return row;
    }));
  }
  const availability = document.getElementById("researchAvailability");
  if (availability) availability.textContent = `Available aligned history: ${formatDate(payload.availableStart)} to ${formatDate(payload.availableEnd)}.`;
}

function renderDrawdown(payload) {
  const container = document.getElementById("drawdownChart");
  if (!container || !window.LightweightCharts || !(payload.drawdowns || []).length) return;
  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth, height: container.clientHeight,
    layout: { background: { type: "solid", color: "transparent" }, textColor: "#64748b" },
    grid: { vertLines: { color: "rgba(15,23,42,.05)" }, horzLines: { color: "rgba(15,23,42,.05)" } },
    rightPriceScale: { borderVisible: false }, timeScale: { borderVisible: false }, handleScroll: { vertTouchDrag: false }
  });
  const area = chart.addAreaSeries({ lineColor: "#dc2626", topColor: "rgba(220,38,38,.28)", bottomColor: "rgba(220,38,38,.03)", lineWidth: 2, priceLineVisible: false, priceFormat: { type: "custom", formatter: (value) => `${value.toFixed(0)}%` } });
  area.setData(payload.drawdowns.map((point) => ({ time: point.time, value: Number(point.value) })));
  chart.timeScale().fitContent();
  window.addEventListener("resize", () => chart.applyOptions({ width: container.clientWidth }));
}

async function initResearchChart() {
  const container = document.getElementById("researchChart");
  const chartValue = document.getElementById("researchChartValue");
  const chartRange = document.getElementById("researchChartRange");
  const chartLabel = document.getElementById("researchChartLabel");
  const timeframeRow = document.getElementById("researchTimeframeRow");
  const status = document.getElementById("researchPageStatus");
  if (!container || !chartRange || !timeframeRow || !window.LightweightCharts) return null;
  const symbol = selectedResearchSymbol(container);
  const requestedLandingSecurity = document.body.dataset.page === "research" && new URLSearchParams(location.search).has("symbol");
  const landingHero = document.querySelector(".landing-hero");
  const heroTitle = document.getElementById("landingHeroTitle");
  const heroDescription = document.getElementById("landingHeroDescription");
  const heading = document.getElementById("researchAssetHeading");
  if (requestedLandingSecurity) {
    delete container.dataset.chartStyle;
    container.setAttribute("aria-label", "Stock Bitcoin-denominated candlestick chart");
  }
  if (requestedLandingSecurity && landingHero) {
    landingHero.classList.add("is-security-result");
    if (heroTitle) heroTitle.textContent = symbol;
    if (heroDescription) heroDescription.textContent = "Loading company profile and market data…";
    if (heading) heading.hidden = true;
  }
  if (chartLabel) chartLabel.textContent = `${symbol === "BTCUSD" ? "BTC" : symbol} / BTC`;
  try {
    const payload = await loadResearchSeries(symbol);
    window.__satvalueResearch = payload;
    updateTrailingReturns(payload.trailingReturns);
    renderResearchMetrics(payload);
    renderDrawdown(payload);
    if (heading) heading.textContent = payload.security?.name || symbol;
    if (requestedLandingSecurity && landingHero) {
      if (heroTitle) heroTitle.textContent = payload.security?.name || symbol;
      if (heroDescription) heroDescription.textContent = payload.security?.description || `${payload.security?.name || symbol} is a US-listed security${payload.security?.exchange ? ` traded on ${payload.security.exchange}` : ""}. The performance below is denominated in Bitcoin.`;
      if (heading) heading.hidden = true;
      const profileSource = document.getElementById("researchProfileSource");
      if (profileSource && payload.security?.profileSourceUrl) {
        const link = document.createElement("a"); link.href = payload.security.profileSourceUrl; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = payload.security.profileSource || "Company profile";
        profileSource.replaceChildren(link); profileSource.hidden = false;
      }
    }
    const meta = document.getElementById("researchSecurityMeta");
    if (meta) meta.textContent = "Performance measured in Bitcoin";
    const returnsHeading = document.getElementById("researchReturnsHeading");
    if (returnsHeading) returnsHeading.textContent = `${symbol === "BTCUSD" ? "BTC" : symbol}/BTC`;
    const researchSource = document.getElementById("researchDataSource");
    const sourceSummary = `${payload.source} · ${String(payload.feed).toUpperCase()} · latest shared completed observation ${formatDate(payload.asOf)}${payload.stale ? " · cached or potentially stale" : ""}`;
    if (researchSource) { researchSource.textContent = sourceSummary; researchSource.classList.toggle("is-stale", Boolean(payload.stale)); }
    if (status) { status.hidden = true; status.textContent = sourceSummary; status.classList.toggle("is-stale", Boolean(payload.stale)); }

    const daily = payload.bars; const weekly = aggregateWeekly(daily); const monthly = aggregateMonthly(daily);
    let active = daily; let current = []; let activeRange = "MAX"; let suppress = false; let rebasing = false; let lastBase = -1;
    const isCandlestick = payload.chartType === "candlestick" && container.dataset.chartStyle !== "line";
    const chart = LightweightCharts.createChart(container, {
      width: container.clientWidth, height: container.clientHeight,
      layout: { background: { type: "solid", color: "transparent" }, textColor: "#64748b" },
      grid: { vertLines: { color: "rgba(15,23,42,.06)" }, horzLines: { color: "rgba(15,23,42,.06)" } },
      crosshair: { mode: LightweightCharts.CrosshairMode.Normal, vertLine: { color: "#2563eb", labelBackgroundColor: "#2563eb" }, horzLine: { color: "#2563eb", labelBackgroundColor: "#2563eb" } },
      rightPriceScale: { borderColor: "rgba(15,23,42,.1)", scaleMargins: { top: .08, bottom: .1 } },
      timeScale: { borderColor: "rgba(15,23,42,.1)", timeVisible: true, barSpacing: 8, minBarSpacing: .25, rightOffset: 2 },
      handleScroll: { vertTouchDrag: false }
    });
    const common = { priceLineVisible: false, lastValueVisible: true, priceFormat: { type: "custom", precision: 1, minMove: .1, formatter: (price) => `${price.toFixed(1)}%` } };
    const series = isCandlestick ? chart.addCandlestickSeries({ ...common, upColor: "#22c55e", downColor: "#ef4444", borderUpColor: "#16a34a", borderDownColor: "#dc2626", wickUpColor: "#16a34a", wickDownColor: "#dc2626" }) : chart.addLineSeries({ ...common, color: "#2563eb", lineWidth: 2 });
    const shown = (point) => isCandlestick ? point.close : point.value;
    function rebase(index) {
      const baseIndex = Math.max(0, Math.min(active.length - 1, index)); const base = active[baseIndex].rawClose;
      current = active.map((point) => { const values = { time: point.time, open: ((point.rawOpen / base) - 1) * 100, high: ((point.rawHigh / base) - 1) * 100, low: ((point.rawLow / base) - 1) * 100, close: ((point.rawClose / base) - 1) * 100 }; return isCandlestick ? values : { time: values.time, value: values.close }; });
      series.setData(current); lastBase = baseIndex; const latest = shown(current[current.length - 1]); const color = latest >= 0 ? "#16a34a" : "#dc2626";
      series.applyOptions(isCandlestick ? { priceLineColor: color } : { color, priceLineColor: color }); if (chartValue) chartValue.textContent = formatPercent(latest, 2);
    }
    function applyRange(range) {
      activeRange = range; active = dataForRange(range, daily, weekly, monthly); const from = visibleStartIndex(range, active); const to = active.length - 1; suppress = true; rebase(from);
      chart.timeScale().applyOptions({ barSpacing: Math.max(.25, Math.min(10, Math.max(240, container.clientWidth - 90) / Math.max(1, to - from + 1))) });
      chart.timeScale().setVisibleRange({ from: current[from].time, to: current[to].time }); suppress = false;
      timeframeRow.querySelectorAll("[data-range]").forEach((button) => { const selected = button.dataset.range === range; button.classList.toggle("is-active", selected); button.setAttribute("aria-pressed", String(selected)); });
      chartRange.textContent = `${active[from].time} to ${active[to].time}`;
    }
    const restoreHorizonValue = () => { if (chartValue && current.length) chartValue.textContent = formatPercent(shown(current[current.length - 1]), 2); };
    chart.subscribeCrosshairMove((param) => { const point = param.seriesData?.get(series); if (point && chartValue) chartValue.textContent = formatPercent(shown(point), 2); else restoreHorizonValue(); });
    container.addEventListener("mouseleave", restoreHorizonValue);
    chart.timeScale().subscribeVisibleLogicalRangeChange((range) => { if (!range || suppress || rebasing) return; const index = Math.max(0, Math.min(active.length - 1, Math.floor(range.from))); if (index === lastBase) return; rebasing = true; rebase(index); chart.timeScale().setVisibleLogicalRange(range); rebasing = false; });
    timeframeRow.addEventListener("click", (event) => { const button = event.target.closest("[data-range]"); if (button) applyRange(button.dataset.range); });
    timeframeRow.addEventListener("keydown", (event) => { if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return; const buttons = [...timeframeRow.querySelectorAll("button")]; const index = buttons.indexOf(document.activeElement); if (index < 0) return; event.preventDefault(); buttons[(index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length].focus(); });
    window.addEventListener("resize", () => { chart.applyOptions({ width: container.clientWidth, height: container.clientHeight }); applyRange(activeRange); });
    applyRange("MAX");
    return payload;
  } catch (error) {
    if (requestedLandingSecurity && heroDescription) heroDescription.textContent = error.message || "Company profile and market data are unavailable.";
    chartRange.textContent = error.message || "Market data is unavailable."; if (chartValue) chartValue.textContent = "Unavailable"; updateTrailingReturns({});
    if (status) { status.hidden = false; status.textContent = error.message || "Market data is unavailable."; status.classList.add("is-error"); }
    container.replaceChildren();
    return null;
  }
}

async function fetchRegistry(group) {
  const response = await fetch(`/api/registry?group=${encodeURIComponent(group)}`, { cache: "no-store" });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "Registry unavailable.");
  return payload;
}

async function configureDetailPage() {
  const page = document.body.dataset.page;
  if (!page?.endsWith("detail")) return;
  const params = new URLSearchParams(location.search);
  const group = page === "sector-detail" ? "sectors" : (params.get("group") === "countries" ? "countries" : "asset-classes");
  const registry = await fetchRegistry(group);
  const item = page === "sector-detail"
    ? registry.items.find((entry) => entry.symbol === (params.get("symbol") || "XLC").toUpperCase())
    : registry.items.find((entry) => entry.key === (params.get("key") || "us-equities"));
  if (!item) throw new Error("That research proxy is not configured.");
  if (group === "countries") {
    document.querySelector('.nav-link-direct[href="asset-classes.html"]')?.classList.remove("is-current");
    document.querySelector('.nav-link-direct[href="countries.html"]')?.classList.add("is-current");
  }
  const chart = document.getElementById("researchChart");
  chart.dataset.symbol = item.symbol === "BTC/USD" ? "BTCUSD" : item.symbol;
  delete chart.dataset.chartStyle;
  document.body.dataset.fundSymbol = item.symbol;
  const title = document.getElementById("detailTitle"); if (title) title.textContent = item.name;
  const description = document.getElementById("detailDescription");
  if (description) {
    const showDescription = group === "sectors";
    description.hidden = !showDescription;
    description.textContent = showDescription ? (item.description || "") : "";
  }
  const facts = document.getElementById("fundFacts");
  if (facts) {
    const dateFact = item.dataStartDate ? ["Data start", formatDate(item.dataStartDate)] : ["Fund inception", formatDate(item.inceptionDate)];
    const entries = [["Proxy", item.symbol], ...(group === "sectors" ? [dateFact] : []), ["Expense ratio", Number.isFinite(item.expenseRatio) ? `${item.expenseRatio.toFixed(2)}%` : null], ["Benchmark", item.benchmark]];
    facts.replaceChildren(...entries.filter(([, value]) => value).map(([label, value]) => { const span = document.createElement("span"); span.textContent = `${label}: ${value}`; return span; }));
  }
  const detailHero = document.getElementById("detailHero");
  if (detailHero) detailHero.hidden = false;
  const proxySource = document.getElementById("proxySource");
  if (proxySource && item.issuerUrl) { const link = document.createElement("a"); link.href = item.issuerUrl; link.target = "_blank"; link.rel = "noopener noreferrer"; link.textContent = `${item.issuer || "Issuer"} fund information`; proxySource.replaceChildren(link); }
  const disclosure = document.getElementById("proxyDisclosure"); if (disclosure) disclosure.textContent = group === "countries"
    ? `${item.name} is represented by ${item.symbol}. The result describes that country equity ETF, not the national economy or an uninvestable headline index. Trailing returns are cumulative, not annualized. Summary metrics use the full available common history; volatility is annualized from daily changes using 252 observations per year.`
    : `${item.name} is represented by ${item.symbol}. The result describes that investable proxy, not the complete conceptual asset class. Trailing returns are cumulative, not annualized. Summary metrics use the full available common history; volatility is annualized from daily changes using 252 observations per year.`;
  document.title = `${item.name} | SatValue`;
}

function renderFundRows(tableBody, rows) {
  tableBody.replaceChildren(...rows.map((item) => { const row = document.createElement("tr"); const name = document.createElement("td"); const weight = document.createElement("td"); name.textContent = item.name; weight.textContent = `${Number(item.weight).toFixed(2)}%`; weight.className = "right-align"; row.append(name, weight); return row; }));
}

function renderFundStatus(element, label, payload) {
  const source = document.createElement("a"); source.href = payload.sourceUrl; source.target = "_blank"; source.rel = "noopener noreferrer"; source.textContent = label;
  element.replaceChildren(source, document.createTextNode(` · ${payload.stale ? "cached fallback" : "automatically refreshed every 6 hours"} · as of ${formatDate(payload.asOf)}`));
  element.classList.toggle("is-stale", Boolean(payload.stale)); element.title = payload.warning || "Loaded automatically from State Street.";
}

async function initFundSnapshot() {
  const industryRows = document.getElementById("industryAllocationRows"); const holdingRows = document.getElementById("topHoldingRows");
  const industryStatus = document.getElementById("industryDataStatus"); const holdingsStatus = document.getElementById("holdingsDataStatus");
  if (!industryRows || !holdingRows || !industryStatus || !holdingsStatus) return;
  const symbol = document.body.dataset.fundSymbol || "XLC";
  try {
    const response = await fetch(`/api/fund?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store" }); const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Issuer details unavailable.");
    renderFundRows(industryRows, payload.industryAllocations || []); renderFundRows(holdingRows, payload.topHoldings || []);
    renderFundStatus(industryStatus, "State Street fund allocation", payload); renderFundStatus(holdingsStatus, "State Street fund holdings", payload);
  } catch (error) {
    const industryError = document.createElement("tr"); const industryCell = document.createElement("td"); industryCell.colSpan = 2; industryCell.className = "error-cell"; industryCell.textContent = error.message; industryError.append(industryCell);
    const holdingsError = document.createElement("tr"); const holdingsCell = document.createElement("td"); holdingsCell.colSpan = 2; holdingsCell.className = "error-cell"; holdingsCell.textContent = error.message; holdingsError.append(holdingsCell);
    industryRows.replaceChildren(industryError); holdingRows.replaceChildren(holdingsError); industryStatus.textContent = error.message; holdingsStatus.textContent = error.message;
    industryStatus.classList.add("is-error"); holdingsStatus.classList.add("is-error");
  }
}

function rankingLink(group, item) {
  return group === "sectors" ? `sector.html?symbol=${encodeURIComponent(item.symbol)}` : `asset-class.html?key=${encodeURIComponent(item.key)}`;
}

function returnCell(value) {
  const cell = document.createElement("td"); cell.textContent = formatPercent(value); cell.className = !Number.isFinite(Number(value)) ? "muted-text" : (Number(value) >= 0 ? "heat-positive" : "heat-negative"); return cell;
}

async function initRankingPage() {
  const body = document.getElementById("rankingRows"); const source = document.getElementById("rankingSource"); const group = document.body.dataset.rankingGroup;
  if (!body || !group) return;
  try {
    const response = await fetch(`/api/rankings?group=${encodeURIComponent(group)}`, { cache: "no-store" }); const payload = await response.json(); if (!response.ok) throw new Error(payload.error || "Rankings unavailable.");
    window.__satvalueRankings = payload; let items = payload.items.slice();
    let sortKey = "name"; let direction = 1;
    source.textContent = `${payload.source} · common as of ${formatDate(payload.asOf)} · registry ${payload.registryVersion} · refreshes every ${Math.round(payload.cacheTtlSeconds / 60)} minutes${payload.stale ? " · STALE" : ""}`; source.classList.toggle("is-stale", payload.stale);
    function render() {
      body.replaceChildren(...items.map((item) => {
        const row = document.createElement("tr"); const name = document.createElement("td"); const link = document.createElement("a"); link.href = rankingLink(group, item); link.textContent = item.name; link.title = `${item.name} (${item.symbol})`; name.append(link);
        const proxy = document.createElement("td"); proxy.textContent = item.symbol; proxy.className = "proxy-cell"; row.append(name, proxy);
        ["YTD", "1-Year", "3-Year", "5-Year", "10-Year"].forEach((period) => row.append(returnCell(item.returns?.[period])));
        return row;
      }));
    }
    document.querySelectorAll("[data-sort]").forEach((button) => button.addEventListener("click", () => { const next = button.dataset.sort; direction = sortKey === next ? direction * -1 : (next === "name" ? 1 : -1); sortKey = next; items.sort((a, b) => { const av = next === "name" ? a.name : a.returns?.[next]; const bv = next === "name" ? b.name : b.returns?.[next]; if (av == null) return 1; if (bv == null) return -1; return (typeof av === "string" ? av.localeCompare(bv) : av - bv) * direction; }); render(); }));
    items.sort((a, b) => a.name.localeCompare(b.name)); render();
  } catch (error) { body.innerHTML = `<tr><td colspan="7" class="error-cell"></td></tr>`; body.querySelector("td").textContent = error.message; source.textContent = "Rankings unavailable"; source.classList.add("is-error"); }
}

async function initCountries() {
  const rows = document.getElementById("countryRows"); const source = document.getElementById("countrySource"); const map = document.getElementById("countriesMap");
  if (!rows || !source || !map) return;
  try {
    const response = await fetch("/api/rankings?group=countries", { cache: "no-store" }); const payload = await response.json(); if (!response.ok) throw new Error(payload.error || "Country data unavailable.");
    window.__satvalueCountries = payload; let items = payload.items.slice(); let sortKey = "name"; let direction = 1;
    source.textContent = `${payload.source} · common as of ${formatDate(payload.asOf)} · registry ${payload.registryVersion}${payload.stale ? " · STALE" : ""}`; source.classList.toggle("is-stale", payload.stale);
    const renderRows = () => rows.replaceChildren(...items.map((item) => { const row = document.createElement("tr"); const name = document.createElement("td"); const link = document.createElement("a"); link.href = `asset-class.html?group=countries&key=${encodeURIComponent(item.key)}`; link.textContent = item.name; name.append(link); row.append(name); ["YTD", "1-Year", "3-Year", "5-Year", "10-Year"].forEach((period) => row.append(returnCell(item.returns?.[period]))); return row; }));
    document.querySelectorAll("[data-country-sort]").forEach((button) => button.addEventListener("click", () => { const next = button.dataset.countrySort; direction = sortKey === next ? direction * -1 : (next === "name" ? 1 : -1); sortKey = next; items.sort((a, b) => { const av = next === "name" ? a.name : a.returns?.[next]; const bv = next === "name" ? b.name : b.returns?.[next]; if (av == null) return 1; if (bv == null) return -1; return (typeof av === "string" ? av.localeCompare(bv) : av - bv) * direction; }); renderRows(); }));
    items.sort((a, b) => a.name.localeCompare(b.name)); renderRows();
    if (!window.Plotly) throw new Error("Map library unavailable.");
    const trace = { type: "choropleth", locationmode: "ISO-3", locations: items.map((item) => item.iso3), z: items.map((item) => item.returns?.["1-Year"]), text: items.map((item) => item.name), customdata: items.map((item) => [item.key, item.symbol, item.returns?.YTD, item.returns?.["1-Year"], item.returns?.["3-Year"], item.returns?.["5-Year"], item.returns?.["10-Year"]]), colorscale: [[0,"#fecaca"],[.45,"#fef3c7"],[.5,"#f8fafc"],[.55,"#d1fae5"],[1,"#10b981"]], zmid: 0, marker: { line: { color: "#d5dce8", width: .8 } }, hovertemplate: "<b>%{text}</b> · %{customdata[1]}<br>YTD %{customdata[2]:.1f}%<br>1Y %{customdata[3]:.1f}%<br>3Y %{customdata[4]:.1f}%<br>5Y %{customdata[5]:.1f}%<br>10Y %{customdata[6]:.1f}%<extra></extra>", colorbar: { title: "1Y in BTC", ticksuffix: "%", thickness: 12 } };
    const compactLabels = new Set(["Australia", "Brazil", "Canada", "China", "Japan", "South Korea", "United Kingdom", "United States"]);
    const labelText = () => items.map((item) => window.innerWidth < 760 && !compactLabels.has(item.name) ? "" : item.name);
    const labels = { type: "scattergeo", mode: "text", lat: items.map((item) => item.lat), lon: items.map((item) => item.lon), text: labelText(), customdata: items.map((item) => item.key), textfont: { family: "Inter, Arial, sans-serif", size: 11, color: "#172033" }, textposition: "middle center", hoverinfo: "skip", showlegend: false };
    await Plotly.newPlot(map, [trace, labels], { margin: { t: 5, r: 5, b: 5, l: 5 }, geo: { projection: { type: "natural earth", scale: 1.05 }, showframe: false, showcoastlines: false, showcountries: true, countrycolor: "#d5dce8", showland: true, landcolor: "#f5f7fb", bgcolor: "transparent" }, paper_bgcolor: "transparent", dragmode: "pan" }, { responsive: true, displayModeBar: false, scrollZoom: true });
    map.on("plotly_click", (event) => { const point = event.points?.[0]; const key = point?.data?.type === "scattergeo" ? point.customdata : point?.customdata?.[0]; if (key) location.href = `asset-class.html?group=countries&key=${encodeURIComponent(key)}`; });
    window.addEventListener("resize", () => Plotly.restyle(map, { text: [labelText()] }, [1]));
    const adjust = (delta) => { const current = map.layout?.geo?.projection?.scale || 1.05; Plotly.relayout(map, { "geo.projection.scale": Math.max(.9, Math.min(4, current + delta)) }); };
    document.getElementById("countriesZoomIn")?.addEventListener("click", () => adjust(.2)); document.getElementById("countriesZoomOut")?.addEventListener("click", () => adjust(-.2));
  } catch (error) { rows.innerHTML = `<tr><td colspan="6" class="error-cell"></td></tr>`; rows.querySelector("td").textContent = error.message; source.textContent = error.message; source.classList.add("is-error"); }
}

function addPortfolioHoldingRow(symbol = "", weight = "") {
  const body = document.getElementById("portfolioHoldingRows");
  if (!body || body.rows.length >= 20) return;
  const row = document.createElement("tr");
  const symbolCell = document.createElement("td");
  const weightCell = document.createElement("td");
  const actionCell = document.createElement("td");
  const symbolInput = document.createElement("input");
  symbolInput.className = "portfolio-symbol-input"; symbolInput.value = symbol; symbolInput.maxLength = 10; symbolInput.required = true; symbolInput.autocomplete = "off"; symbolInput.placeholder = "SPY"; symbolInput.setAttribute("aria-label", "Holding ticker");
  const weightInput = document.createElement("input");
  weightInput.className = "portfolio-weight-input"; weightInput.type = "number"; weightInput.min = "0.01"; weightInput.max = "100"; weightInput.step = "0.01"; weightInput.value = weight; weightInput.required = true; weightInput.setAttribute("aria-label", "Holding weight percent");
  const percent = document.createElement("span"); percent.className = "weight-suffix"; percent.textContent = "%";
  const weightWrap = document.createElement("div"); weightWrap.className = "weight-input-wrap"; weightWrap.append(weightInput, percent);
  const remove = document.createElement("button"); remove.type = "button"; remove.className = "remove-holding-button"; remove.textContent = "Remove"; remove.setAttribute("aria-label", `Remove ${symbol || "holding"}`);
  remove.addEventListener("click", () => { if (body.rows.length > 2) { row.remove(); updatePortfolioWeightTotal(); } });
  [symbolInput, weightInput].forEach((input) => input.addEventListener("input", updatePortfolioWeightTotal));
  symbolCell.append(symbolInput); weightCell.append(weightWrap); actionCell.append(remove); row.append(symbolCell, weightCell, actionCell); body.append(row); updatePortfolioWeightTotal();
}

function updatePortfolioWeightTotal() {
  const totalNode = document.getElementById("portfolioWeightTotal");
  if (!totalNode) return;
  const total = [...document.querySelectorAll(".portfolio-weight-input")].reduce((sum, input) => sum + (Number(input.value) || 0), 0);
  totalNode.textContent = `${total.toFixed(2)}%`; totalNode.classList.toggle("is-valid", Math.abs(total - 100) < .001); totalNode.classList.toggle("is-invalid", Math.abs(total - 100) >= .001);
}

function portfolioRequestFromForm() {
  const holdings = [...document.querySelectorAll("#portfolioHoldingRows tr")].map((row) => ({
    symbol: row.querySelector(".portfolio-symbol-input").value.trim().toUpperCase(),
    weight: Number(row.querySelector(".portfolio-weight-input").value)
  }));
  const benchmarks = document.getElementById("portfolioBenchmarks").value.split(",").map((symbol) => symbol.trim().toUpperCase()).filter(Boolean);
  return { holdings, benchmarks, startDate: document.getElementById("portfolioStartDate").value || null, rebalancing: document.getElementById("portfolioRebalancing").value };
}

function createPortfolioChart(container, definitions, formatter, options = {}) {
  if (!container || !window.LightweightCharts) throw new Error("Chart library unavailable.");
  if (container.__satvalueResize) window.removeEventListener("resize", container.__satvalueResize);
  if (container.__satvalueChart?.remove) container.__satvalueChart.remove();
  container.replaceChildren();
  const chart = LightweightCharts.createChart(container, {
    width: container.clientWidth, height: container.clientHeight,
    layout: { background: { type: "solid", color: "transparent" }, textColor: "#64748b" },
    grid: { vertLines: { color: "rgba(15,23,42,.05)" }, horzLines: { color: "rgba(15,23,42,.05)" } },
    rightPriceScale: { borderVisible: false, mode: options.logarithmic ? LightweightCharts.PriceScaleMode.Logarithmic : LightweightCharts.PriceScaleMode.Normal }, timeScale: { borderVisible: false, minBarSpacing: .05, rightOffset: 0 }, handleScroll: { vertTouchDrag: false }
  });
  definitions.forEach((definition) => {
    const commonOptions = { lineWidth: definition.width || 2, priceLineVisible: false, lastValueVisible: true, priceFormat: { type: "custom", formatter } };
    const series = definition.baseline ? chart.addBaselineSeries({
      ...commonOptions,
      baseValue: { type: "price", price: definition.baseValue ?? 0 },
      topLineColor: definition.topColor || "#059669",
      bottomLineColor: definition.bottomColor || "#dc2626",
      topFillColor1: "rgba(5,150,105,0)", topFillColor2: "rgba(5,150,105,0)",
      bottomFillColor1: "rgba(220,38,38,0)", bottomFillColor2: "rgba(220,38,38,0)"
    }) : chart.addLineSeries({ ...commonOptions, color: definition.color });
    series.setData(definition.data);
    if (definition.zeroLine) series.createPriceLine({ price: 0, color: "#94a3b8", lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, axisLabelVisible: true });
  });
  chart.timeScale().fitContent();
  const resize = () => chart.applyOptions({ width: container.clientWidth, height: container.clientHeight });
  window.addEventListener("resize", resize, { passive: true }); container.__satvalueResize = resize; container.__satvalueChart = chart;
  return chart;
}

function valueSeries(rows, key, multiplier = 1) {
  return rows.map((row) => ({ time: row.time, value: Number(row[key]) * multiplier })).filter((point) => Number.isFinite(point.value));
}

function portfolioRangeStart(range, data) {
  if (!data.length || range === "MAX") return data[0]?.time;
  const end = new Date(`${data[data.length - 1].time}T00:00:00Z`); const start = new Date(end);
  if (range === "YTD") start.setUTCMonth(0, 1);
  else if (range === "1W") start.setUTCDate(start.getUTCDate() - 7);
  else { const months = { "1M": 1, "3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60, "10Y": 120 }[range] || 0; start.setUTCMonth(start.getUTCMonth() - months); }
  const target = start.toISOString().slice(0, 10);
  return data.find((point) => point.time >= target)?.time || data[0].time;
}

function bindPortfolioGrowthRange(chart, data, selectedRange = "MAX", onSelect = () => {}) {
  const original = document.getElementById("portfolioGrowthTimeframeRow"); if (!original || !data.length) return;
  const row = original.cloneNode(true); original.replaceWith(row);
  const apply = (range) => {
    chart.timeScale().setVisibleRange({ from: portfolioRangeStart(range, data), to: data[data.length - 1].time });
    row.querySelectorAll("[data-range]").forEach((button) => { const active = button.dataset.range === range; button.classList.toggle("is-active", active); button.setAttribute("aria-pressed", String(active)); }); onSelect(range);
  };
  row.addEventListener("click", (event) => { const button = event.target.closest("[data-range]"); if (button) apply(button.dataset.range); });
  row.addEventListener("keydown", (event) => { if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return; const buttons = [...row.querySelectorAll("button")]; const index = buttons.indexOf(document.activeElement); if (index < 0) return; event.preventDefault(); buttons[(index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length].focus(); });
  apply(selectedRange);
}

function portfolioHeaderRow(containerId, firstLabel, portfolioName, benchmarks) {
  const head = document.getElementById(containerId); const labels = [firstLabel, `${portfolioName}/BTC`, ...benchmarks.map((symbol) => `${symbol}/BTC`)]
  head.replaceChildren(...labels.map((label) => { const cell = document.createElement("th"); cell.textContent = label; return cell; }));
}

function renderPortfolioAnnualized(payload) {
  const metrics = payload.metrics || {}; const benchmarks = (payload.benchmarks || []).map((item) => item.symbol);
  const values = [["Portfolio/BTC", metrics.portfolioVsBtc?.cagr], ...benchmarks.map((symbol) => [`${symbol}/BTC`, metrics.benchmarks?.[symbol]?.cagr])];
  const container = document.getElementById("portfolioAnnualizedValues");
  container.replaceChildren(...values.map(([label, value]) => { const item = document.createElement("div"); const name = document.createElement("span"); const result = document.createElement("strong"); name.textContent = label; result.textContent = formatPlainPercent(value); item.append(name, result); return item; }));
}

function renderPortfolioTables(payload, portfolioName) {
  const periods = ["YTD", "1-Month", "1-Year", "3-Year", "5-Year", "10-Year"];
  const benchmarks = (payload.benchmarks || []).map((item) => item.symbol);
  portfolioHeaderRow("portfolioTrailingHead", "Period", portfolioName, benchmarks);
  const trailingBody = document.getElementById("portfolioTrailingRows");
  trailingBody.replaceChildren(...periods.map((period) => {
    const row = document.createElement("tr"); const label = document.createElement("td"); label.textContent = period; row.append(label);
    row.append(returnCell(payload.trailingReturns?.portfolioVsBtc?.[period]));
    benchmarks.forEach((symbol) => row.append(returnCell(payload.trailingReturns?.benchmarks?.[symbol]?.[period]))); return row;
  }));
  const portfolioByYear = new Map((payload.calendarReturns?.portfolioVsBtc || []).map((item) => [item.year, item.return]));
  const benchmarkYears = Object.fromEntries(benchmarks.map((symbol) => [symbol, new Map((payload.calendarReturns?.benchmarks?.[symbol] || []).map((item) => [item.year, item.return]))]));
  const years = [...new Set([...portfolioByYear.keys(), ...Object.values(benchmarkYears).flatMap((values) => [...values.keys()])])].sort((a, b) => b - a);
  portfolioHeaderRow("portfolioCalendarHead", "Year", portfolioName, benchmarks);
  const calendarBody = document.getElementById("portfolioCalendarRows");
  calendarBody.replaceChildren(...years.map((year) => { const row = document.createElement("tr"); const label = document.createElement("td"); label.textContent = year; row.append(label, returnCell(portfolioByYear.get(year))); benchmarks.forEach((symbol) => row.append(returnCell(benchmarkYears[symbol].get(year)))); return row; }));
}

function formatPlainPercent(value) {
  const numeric = Number(value); return Number.isFinite(numeric) ? `${numeric.toFixed(2)}%` : "--";
}

function formatBitcoin(value) {
  const numeric = Number(value); return Number.isFinite(numeric) ? `${numeric.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} BTC` : "--";
}

function portfolioTableCell(value, kind = "percent") {
  const cell = document.createElement("td"); cell.textContent = kind === "btc" ? formatBitcoin(value) : formatPlainPercent(value); return cell;
}

function renderPortfolioAllocation(payload, portfolioName) {
  const colors = ["#2417e8", "#426e9a", "#7fa4c8", "#b8cce0", "#5f63d8", "#2f8f83", "#8c6cc5", "#d69558"];
  const body = document.getElementById("portfolioAllocationRows"); const legend = document.getElementById("portfolioAllocationLegend"); const donut = document.getElementById("portfolioAllocationDonut");
  body.replaceChildren(...payload.holdings.map((holding) => { const row = document.createElement("tr"); const symbol = document.createElement("td"); const weight = document.createElement("td"); symbol.textContent = holding.symbol; weight.textContent = `${Number(holding.weight).toFixed(2)}%`; row.append(symbol, weight); return row; }));
  let cursor = 0; const segments = payload.holdings.map((holding, index) => { const start = cursor; cursor += Number(holding.weight); return `${colors[index % colors.length]} ${start}% ${cursor}%`; }); donut.style.background = `conic-gradient(${segments.join(",")})`;
  legend.replaceChildren(...payload.holdings.map((holding, index) => { const item = document.createElement("span"); const marker = document.createElement("i"); marker.style.background = colors[index % colors.length]; item.append(marker, document.createTextNode(`${holding.symbol} ${Number(holding.weight).toFixed(0)}%`)); return item; }));
  document.getElementById("allocationPortfolioName").textContent = portfolioName;
}

function calendarExtreme(rows, mode) {
  const values = (rows || []).map((item) => Number(item.return)).filter(Number.isFinite); if (!values.length) return null; return mode === "max" ? Math.max(...values) : Math.min(...values);
}

function renderPortfolioPerformance(payload, first, last, portfolioName) {
  const metrics = payload.metrics || {}; const calendar = payload.calendarReturns || {}; const body = document.getElementById("portfolioPerformanceRows");
  const benchmarks = (payload.benchmarks || []).map((item) => item.symbol);
  portfolioHeaderRow("portfolioPerformanceHead", "Metric", portfolioName, benchmarks);
  const rows = [
    ["Start Balance", "btc", first.portfolioBtc, ...benchmarks.map((symbol) => first.benchmarksBtc?.[symbol])],
    ["End Balance", "btc", last.portfolioBtc, ...benchmarks.map((symbol) => last.benchmarksBtc?.[symbol])],
    ["Annualized Return (CAGR)", "percent", metrics.portfolioVsBtc?.cagr, ...benchmarks.map((symbol) => metrics.benchmarks?.[symbol]?.cagr)],
    ["Standard Deviation", "percent", metrics.portfolioVsBtc?.annualizedVolatility, ...benchmarks.map((symbol) => metrics.benchmarks?.[symbol]?.annualizedVolatility)],
    ["Best Year", "percent", calendarExtreme(calendar.portfolioVsBtc, "max"), ...benchmarks.map((symbol) => calendarExtreme(calendar.benchmarks?.[symbol], "max"))],
    ["Worst Year", "percent", calendarExtreme(calendar.portfolioVsBtc, "min"), ...benchmarks.map((symbol) => calendarExtreme(calendar.benchmarks?.[symbol], "min"))],
    ["Maximum Drawdown", "percent", metrics.portfolioVsBtc?.maxDrawdown, ...benchmarks.map((symbol) => metrics.benchmarks?.[symbol]?.maxDrawdown)]
  ];
  body.replaceChildren(...rows.map(([label, kind, ...values]) => { const row = document.createElement("tr"); const heading = document.createElement("th"); heading.scope = "row"; heading.textContent = label; row.append(heading, ...values.map((value) => portfolioTableCell(value, kind))); return row; }));
}

function renderPortfolioResults(payload) {
  const rows = payload.series || []; if (!rows.length) throw new Error("Portfolio response contained no observations.");
  const results = document.getElementById("portfolioResults"); results.hidden = false;
  const portfolioName = document.getElementById("portfolioName").value.trim() || "Portfolio"; const last = rows[rows.length - 1]; const metrics = payload.metrics || {};
  document.getElementById("portfolioResultsTitle").textContent = `Portfolio Analysis Results (${formatDate(payload.effectiveStart)} – ${formatDate(payload.availableEnd)})`;
  const relativeResult = ((Number(last.portfolioBtc) / Number(rows[0].portfolioBtc)) - 1) * 100; const opportunity = document.getElementById("portfolioOpportunityCost");
  if (Number.isFinite(relativeResult)) opportunity.textContent = Math.abs(relativeResult) < .05 ? "Your portfolio has kept pace with simply holding BTC" : relativeResult < 0 ? `Your portfolio has lost ${Math.abs(relativeResult).toFixed(0)}% versus simply holding BTC` : `Your portfolio has gained ${relativeResult.toFixed(0)}% versus simply holding BTC`;
  document.getElementById("portfolioSource").textContent = `${payload.source} · ${payload.rebalancing} rebalancing · latest shared observation ${formatDate(payload.asOf)}`;
  renderPortfolioAnnualized(payload); document.getElementById("portfolioVolatilityBtc").textContent = formatPlainPercent(metrics.portfolioVsBtc?.annualizedVolatility); document.getElementById("portfolioDrawdownBtc").textContent = formatPlainPercent(Math.abs(Number(metrics.portfolioVsBtc?.maxDrawdown)));
  document.getElementById("portfolioGrowthSummary").textContent = `${formatBitcoin(rows[0].portfolioBtc)} invested at the effective start would be worth ${formatBitcoin(last.portfolioBtc)} at the end of the selected period.`;
  renderPortfolioAllocation(payload, portfolioName); renderPortfolioPerformance(payload, rows[0], last, portfolioName);
  const growthDefinitions = [
    { data: valueSeries(rows, "portfolioBtc"), color: "#2563eb", width: 3 }
  ]; const growthContainer = document.getElementById("portfolioGrowthChart"); const logScale = document.getElementById("portfolioLogScale"); let growthRange = "MAX"; const drawGrowth = () => { const chart = createPortfolioChart(growthContainer, growthDefinitions, (value) => `${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 4 })} BTC`, { logarithmic: logScale.checked }); bindPortfolioGrowthRange(chart, growthDefinitions[0].data, growthRange, (range) => { growthRange = range; }); }; logScale.onchange = drawGrowth; drawGrowth();
  createPortfolioChart(document.getElementById("portfolioRollingChart"), [{ data: (payload.rollingReturns || []).map((point) => ({ time: point.time, value: Number(point.value) })), baseline: true, baseValue: 0, zeroLine: true, topColor: "#059669", bottomColor: "#dc2626", width: 2 }], (value) => `${Number(value).toFixed(1)}%`);
  renderPortfolioTables(payload, portfolioName); document.getElementById("portfolioMethodology").textContent = payload.methodology;
  const warnings = document.getElementById("portfolioWarnings"); const messages = (payload.warnings || []).length ? payload.warnings : [`Note: The analysis period begins on ${formatDate(payload.effectiveStart)}, the first shared completed observation for all selected assets and benchmarks.`]; warnings.replaceChildren(...messages.map((message) => { const p = document.createElement("p"); p.textContent = message; return p; }));
}

function initPortfolio() {
  const form = document.getElementById("portfolioForm"); if (!form) return;
  addPortfolioHoldingRow("SPY", "60"); addPortfolioHoldingRow("IEF", "40");
  const start = document.getElementById("portfolioStartDate"); const yesterday = new Date(Date.now() - 86400000); start.max = yesterday.toISOString().slice(0, 10);
  document.getElementById("addPortfolioHolding").addEventListener("click", () => addPortfolioHoldingRow());
  const builder = document.getElementById("portfolioBuilder"); const toggle = document.getElementById("portfolioConfigToggle");
  const setConfigExpanded = (expanded) => { builder.hidden = !expanded; toggle.setAttribute("aria-expanded", String(expanded)); toggle.querySelector(".config-chevron").textContent = expanded ? "⌃" : "⌄"; };
  toggle.addEventListener("click", () => setConfigExpanded(toggle.getAttribute("aria-expanded") !== "true"));
  const tabs = [document.getElementById("portfolioSettingsTab"), document.getElementById("portfolioAssetsTab")];
  const activateTab = (selected) => { tabs.forEach((tab) => { const active = tab === selected; tab.classList.toggle("is-active", active); tab.setAttribute("aria-selected", String(active)); document.getElementById(tab.getAttribute("aria-controls")).hidden = !active; }); };
  tabs.forEach((tab) => tab.addEventListener("click", () => activateTab(tab)));
  form.addEventListener("submit", async (event) => {
    event.preventDefault(); const status = document.getElementById("portfolioStatus"); const submit = form.querySelector('[type="submit"]'); const results = document.getElementById("portfolioResults");
    status.textContent = "Analyzing completed daily observations…"; status.className = "portfolio-status-inline"; submit.disabled = true;
    try {
      const response = await fetch("/api/portfolio", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(portfolioRequestFromForm()) });
      const payload = await response.json().catch(() => ({})); if (!response.ok) throw new Error(payload.error || "Portfolio backtest failed.");
      renderPortfolioResults(payload); status.textContent = payload.stale ? `Results may be stale · last shared observation ${formatDate(payload.asOf)}` : `Analysis complete · last shared observation ${formatDate(payload.asOf)}`; status.classList.toggle("is-stale", Boolean(payload.stale)); setConfigExpanded(false);
    } catch (error) { results.hidden = true; status.textContent = error.message; status.classList.add("is-error"); }
    finally { submit.disabled = false; }
  });
  form.requestSubmit();
}

function trackPageView() {
  const body = JSON.stringify({ page: location.pathname });
  if (navigator.sendBeacon) navigator.sendBeacon("/api/analytics", new Blob([body], { type: "application/json" }));
  else fetch("/api/analytics", { method: "POST", headers: { "Content-Type": "application/json" }, body, keepalive: true }).catch(() => {});
}

async function bootstrap() {
  initNavigation(); initTickerSearch(); initMarketTicker(); initUnitGuideLink(); initPortfolio(); trackPageView();
  try { await configureDetailPage(); } catch (error) { const status = document.getElementById("researchPageStatus"); if (status) { status.textContent = error.message; status.classList.add("is-error"); } return; }
  await Promise.all([initResearchChart(), initFundSnapshot(), initRankingPage(), initCountries()]);
}

bootstrap();
