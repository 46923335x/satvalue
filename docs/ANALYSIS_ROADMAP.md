# SatValue Analysis Page Roadmap

## Status

Planned. This roadmap begins after the completed page, data-quality, production, and portfolio milestones documented in `PAGE_ROADMAP.md`.

Primary route: `/analysis.html`

Primary navigation order:

1. Analysis
2. Sectors
3. Asset Classes
4. Countries
5. Portfolio

The Analysis link belongs immediately to the left of Sectors. It is the site's synthesis layer: existing pages answer what an individual asset or group did when denominated in Bitcoin; Analysis answers the questions that become possible only after Bitcoin is selected as the numeraire.

## Product thesis

SatValue should not compete by reproducing a conventional finance portal with a currency toggle. Its defensible product is a collection of analyses that make Bitcoin opportunity cost, purchasing-power preservation, and numeraire choice visible.

The page should answer:

- What assets preserved or increased Bitcoin purchasing power?
- How much Bitcoin was forgone by owning another asset?
- How often, and for how long, did an asset outperform Bitcoin?
- Which assets are near a BTC-denominated high rather than merely a USD high?
- Which apparent USD winners still lost Bitcoin purchasing power?
- How does the investment opportunity set change when return and risk are measured in BTC?

## Product principles

1. **Bitcoin is the numeraire.** Use “BTC-denominated,” “in Bitcoin terms,” or “Bitcoin purchasing power.” Do not describe USD as a benchmark on this page.
2. **Opportunity cost is concrete.** Whenever possible, pair percentages with BTC and current-dollar amounts.
3. **One aligned dataset drives every module.** A chart, table, card, and tooltip must not calculate from separately maintained observations.
4. **No shortened horizons.** A 5Y result requires a completed 5Y window. Missing history displays `--` with a reason.
5. **Current-universe bias is explicit.** A ranking of today's companies is not presented as a point-in-time historical universe.
6. **Analysis is descriptive, not predictive.** Efficient frontiers, scenario calculators, and historical probabilities must say what assumptions they use.
7. **Progressive disclosure beats density.** The default page should emphasize three signature products; advanced modules can sit below or behind tabs.

## Core mathematical definitions

Let:

- `P_i(t)` be the adjusted USD price or total-return proxy for asset `i` at time `t`.
- `B(t)` be the USD price of one BTC at time `t`.
- `Q_i(t) = P_i(t) / B(t)` be the BTC-denominated asset price.
- `t0` be the selected common starting observation.
- `t1` be the selected common ending observation.

### BTC-denominated cumulative return

`R_i,BTC(t0,t1) = Q_i(t1) / Q_i(t0) - 1`

This is the canonical return used throughout SatValue.

### Relative Wealth Index

`RWI_i(t) = 100 × Q_i(t) / Q_i(t0)`

Interpretation:

- 100 is the asset's starting Bitcoin purchasing power.
- 125 means Bitcoin purchasing power increased 25%.
- 40 means Bitcoin purchasing power declined 60%.
- Bitcoin itself is a constant 100 because `BTC/BTC = 1`.

Important product decision: a chart in which Bitcoin grows from 100 to 8,500 is a USD-normalized wealth index, not a BTC-denominated RWI. The page may offer a secondary “USD wealth” view, but the signature RWI must keep Bitcoin flat at 100.

### BTC opportunity cost

For initial capital `C` dollars:

- Asset ending wealth in USD: `W_i = C × P_i(t1) / P_i(t0)`.
- Asset ending wealth in BTC: `BTC_i = W_i / B(t1)`.
- BTC acquired at the start: `BTC_alt = C / B(t0)`.
- BTC forgone: `BTC_alt - BTC_i`.
- Current-dollar opportunity cost: `(BTC_alt - BTC_i) × B(t1)`.

The signed result is retained. A negative opportunity cost means the asset beat Bitcoin over the selected window.

### Rolling probability of beating Bitcoin

For horizon `h`, calculate every completed rolling BTC-denominated return with a full calendar-length window:

`Pr(beat BTC, h) = count(R_i,BTC(t,t+h) > 0) / count(valid completed windows)`

The UI must show the observation count, first valid start, last valid end, and that daily rolling windows overlap.

### BTC all-time high and drawdown

- Running BTC high: `H_i(t) = max(Q_i(s))` for all `s ≤ t`.
- BTC drawdown: `D_i(t) = Q_i(t) / H_i(t) - 1`.
- Current distance from BTC high is the latest `D_i(t)`.
- “All-time” always means all available aligned history and must display the available start date.

### Three-numeraire return

- Nominal USD: `P_i(t1) / P_i(t0) - 1`.
- CPI-adjusted: `(P_i(t1) / P_i(t0)) × (CPI(t0) / CPI(t1)) - 1`.
- BTC-denominated: `Q_i(t1) / Q_i(t0) - 1`.

CPI is monthly. The module must use a documented monthly alignment rule rather than silently interpolating daily inflation.

## Recommended page information architecture

### Header and controls

Use the same global header and ticker tape as the market pages. Add Analysis immediately before Sectors.

The Analysis page begins with a compact control bar:

- Universe: Core Assets, Sectors, Asset Classes, Countries, or Custom.
- Symbols: searchable multi-select for Custom, initially limited to 12.
- Start: Max, 10Y, 5Y, 3Y, 1Y, or custom date.
- End: latest common completed observation by default.
- Initial capital: `$10,000` by default for opportunity-cost calculations.
- Frequency: daily for calculations; chart display can downsample to weekly or monthly.

Changing a control updates every visible module from one response and one common date range.

### Section 1 — Relative Wealth Index

This is the page's primary visual and signature feature.

Required output:

- Multi-series line chart normalized to 100 at the effective start.
- Bitcoin baseline fixed at 100.
- End labels, legend toggles, hover date, and exact RWI value.
- Optional secondary toggle: BTC purchasing power / USD wealth.
- Effective start, common end, sources, and unavailable-symbol explanations.

Default universe: a small core set such as SPY, QQQ, GLD, VNQ, IEF, DBC, and BTC.

### Section 2 — BTC Opportunity Cost

Required output:

- Ranked table and a selected-asset narrative card.
- Initial investment, asset ending USD value, asset ending BTC value, BTC alternative, BTC forgone, and current-dollar opportunity cost.
- USD return and BTC-denominated return shown together.
- Positive and negative opportunity costs distinguished without moral language.

Example sentence pattern:

> Investing $10,000 in AAPL at the effective start produced $X, equal to Y BTC today. Buying Bitcoin instead would represent Z BTC, a difference of N BTC or $M at the ending BTC price.

### Section 3 — BTC Purchasing-Power Heatmap

Required output:

- Rows from the selected universe.
- Columns: 1M, 3M, 6M, 1Y, 3Y, 5Y, and 10Y.
- Green means a gain in Bitcoin purchasing power; red means a loss.
- Exact values remain visible; color is not the only signal.
- Sort by any horizon and reset to registry order.
- Bitcoin may appear as a zero baseline only when educationally helpful; it should not occupy a ranking row by default.

### Section 4 — Persistence of Outperformance

Combine closely related behavioral metrics:

- Probability of beating Bitcoin over 1Y, 3Y, 5Y, and 10Y rolling windows.
- Median and longest continuous outperformance spell.
- Date of the last BTC-denominated all-time high.
- Current BTC drawdown.
- Whether the asset ever recovered its prior BTC high.

This section answers “When did it stop outperforming?” and “How durable was the outperformance?” rather than merely showing trailing returns.

### Section 5 — Winners That Still Lost

A screen for assets with positive USD returns and negative BTC-denominated returns over the selected horizon.

Required columns:

- Asset.
- USD return.
- BTC-denominated return.
- BTC forgone from the selected initial capital.
- Distance from BTC all-time high.

The copy must remain analytical rather than anti-equity.

### Section 6 — Three Numeraires

Compare nominal USD, CPI-adjusted USD, and BTC-denominated returns.

Use grouped bars or a compact comparison table. This module should not load until the CPI data contract and monthly alignment tests are complete.

### Section 7 — Wealth Rankings and Historical Leaders

Two related views:

- Current ranking: which assets preserved the most BTC purchasing power over the selected window.
- Historical leader timeline: monthly snapshots of rank and RWI.

Version 1 uses clearly labeled current registries. A claim about historical market leadership requires point-in-time constituents and belongs in a later data milestone.

### Section 8 — Advanced Portfolio Geometry

Place advanced modules behind an “Advanced” tab:

- BTC-denominated efficient frontier.
- BTC-denominated co-movement matrix among assets.
- USD-return correlation and beta to BTC as a separate conventional statistic.

Do not label a correlation with `BTC/BTC` as “correlation to BTC”; the numeraire series is constant and its correlation is undefined. The valid BTC-denominated product is a correlation matrix of changes in `ln(P_i/B)` across non-BTC assets.

### Section 9 — Monetary Unit Calculator

An educational scenario tool:

- User supplies a BTC/USD rate and a USD asset price.
- Output is BTC, sats, and kS.
- Optional presets: median home, S&P 500 level, gold ounce, oil barrel.
- Results are labeled scenarios, not forecasts.

Link to “Why Bitcoin?” and “What is kS?” from this module.

## Delivery sequence

### Milestone G — Analysis foundation

Goal: create the shell and reusable multi-asset analysis engine.

Scope:

- Add Analysis immediately left of Sectors in every global header.
- Create `/analysis.html` with loading, empty, error, and stale states.
- Add the shared control bar and URL-serializable state.
- Extract a reusable server function that loads multiple adjusted symbols and BTC once, aligns them to common completed dates, and returns both USD and BTC-denominated series.
- Add deterministic downsampling for charts without changing metric inputs.
- Add analysis cache keys based on symbols, dates, horizons, and module version.

Acceptance gate:

- One request supplies every visible module with one effective start and common end.
- Reordering symbols does not change calculated values.
- A missing symbol does not shift the common dates for successfully returned symbols without an explicit warning.
- Sources, available starts, common end, registry version, cache age, and stale state are returned.

### Milestone H — Signature Analysis MVP

Goal: launch the three highest-impact products.

Scope:

- Relative Wealth Index.
- BTC Opportunity Cost.
- BTC Purchasing-Power Heatmap.
- Core Assets, Sectors, and Asset Classes universes.

Acceptance gate:

- RWI begins at exactly 100 for every included series.
- Bitcoin remains exactly 100 in BTC mode.
- Opportunity-cost BTC and dollar values reconcile to the RWI result.
- Heatmap results equal the existing exact-calendar trailing-return functions.
- Missing 10Y history displays `--`, never a shortened result.

### Milestone I — Persistence and BTC-high analytics

Goal: answer how often outperformance occurred and whether it endured.

Scope:

- Rolling probability of beating Bitcoin.
- BTC relative-strength view.
- BTC all-time highs, current drawdowns, and recovery status.
- Winners That Still Lost screen.
- Outperformance-spell durations.

Acceptance gate:

- Rolling windows have exact calendar targets and published sample counts.
- No observation uses future information in a running-high calculation.
- Current drawdown matches the existing ratio-series drawdown engine.
- Every “all-time” label includes the available-history start.

### Milestone J — Three numeraires and wealth history

Goal: add macro context and historical ranking views.

Scope:

- Monthly CPI-U data from an official source.
- Nominal, CPI-adjusted, and BTC-denominated comparison.
- Current wealth rankings.
- Monthly historical-leader timeline for versioned current registries.
- Country universe support.

Acceptance gate:

- CPI vintage, series identifier, month, and alignment rule are visible.
- Rankings at a historical date use only information available at or before that date.
- Current-universe and point-in-time-universe results are never presented as equivalent.

### Milestone K — Advanced allocation analysis

Goal: extend portfolio research into BTC-denominated capital allocation.

Scope:

- Historical BTC-denominated mean returns and covariance matrix.
- Long-only efficient frontier with configurable maximum weights.
- BTC-denominated cross-asset correlation matrix.
- Separate USD-return correlation and beta to BTC.
- Downloadable calculation inputs and results.

Acceptance gate:

- Return frequency, annualization, estimator, constraints, and window are stated.
- Frontier portfolios satisfy weights summing to 100% and all configured bounds.
- Singular covariance and insufficient-history cases fail clearly.
- The module is described as historical analysis, not an expected-return forecast.

### Milestone L — Education, animation, and production polish

Goal: complete the product narrative and make complex results approachable.

Scope:

- Monetary Unit Calculator.
- Historical-leader animation with reduced-motion fallback.
- Shareable URLs and exportable PNG/CSV output.
- Analysis-specific metadata, social card, keyboard navigation, and mobile layouts.
- Analytics events for universe, horizon, module, and export usage without storing portfolio contents or custom ticker lists.

Acceptance gate:

- Every animation has pause, scrub, and reduced-motion behavior.
- Exports contain date range, source, proxy, and methodology metadata.
- A shared URL recreates the same controls and results.
- The first useful result renders before lower-priority modules are requested.

## Feature-to-milestone map

| Proposed feature | Milestone | Priority | Notes |
|---|---:|---:|---|
| BTC Opportunity Cost | H | 1 | Signature narrative metric |
| BTC Relative Strength | I | 1 | Reuses ratio OHLC |
| Rolling Excess Returns / Beat BTC probability | I | 1 | Publish sample size and overlap |
| New Highs vs BTC | I | 1 | Pair USD ATH with BTC ATH status |
| Bitcoin Inflation Adjusted / Three Numeraires | J | 2 | Requires CPI contract |
| Wealth Rankings | J | 2 | Label current-universe bias |
| Heatmap | H | 1 | Immediate visual summary |
| BTC Drawdown | I | 1 | Reuses ratio drawdown engine |
| Winners That Still Lost | I | 2 | Derived screen, low data cost |
| Historical Leaders | J/L | 3 | Static timeline first, animation later |
| Efficient Frontier | K | 3 | Advanced tab |
| Correlation analysis | K | 3 | Separate valid BTC and USD concepts |
| Monetary Debasement Calculator | L | 3 | Educational scenario tool |
| Relative Wealth Index | H | 1 | Primary page visual |

## Proposed server contract

### `POST /api/analysis`

Initial request:

```json
{
  "universe": "core",
  "symbols": ["SPY", "QQQ", "GLD", "VNQ", "IEF", "DBC"],
  "start": "2016-01-01",
  "end": null,
  "initialCapitalUsd": 10000,
  "horizons": ["1M", "3M", "6M", "1Y", "3Y", "5Y", "10Y"],
  "modules": ["rwi", "opportunityCost", "heatmap"]
}
```

Top-level response requirements:

```json
{
  "effectiveStart": "2016-01-04",
  "commonAsOf": "2026-07-31",
  "generatedAt": "...",
  "registryVersion": "...",
  "stale": false,
  "sources": {
    "assets": "Alpaca SIP adjusted daily bars",
    "bitcoin": "Coinbase Exchange BTC/USD"
  },
  "availability": [],
  "modules": {}
}
```

The response should be modular so later milestones can add `persistence`, `highs`, `numeraires`, and `frontier` without breaking the MVP contract.

## Data architecture work

The current server already contains most low-level calculations. The main refactor is orchestration:

1. Extract the multi-symbol loading logic now embedded in ranking and portfolio flows.
2. Return a canonical aligned dataset containing adjusted USD close, BTC/USD close, BTC-denominated close, and availability metadata.
3. Calculate all modules from that canonical dataset.
4. Cache raw provider results separately from derived analysis responses.
5. Keep the full daily series for calculations and derive smaller display series for charts.
6. Add a module-version field to invalidate cached derived calculations after formula changes.

Longer term, persistent daily storage is preferable to repeated provider downloads. It becomes important for historical-leader animation, point-in-time universes, reproducible CPI vintages, and large custom universes.

## Test plan

### Unit tests

- RWI starts at 100 and BTC stays at 100.
- Opportunity cost reconciles in BTC and current dollars.
- A zero BTC-denominated return yields zero opportunity cost before rounding.
- Rolling probabilities include only complete calendar windows.
- Running highs and drawdowns have no look-ahead.
- Heatmap values equal canonical trailing-return values.
- CPI-adjusted return uses the documented month alignment.
- Correlation with the constant BTC/BTC series is rejected as undefined.
- Efficient-frontier weights satisfy constraints.

### Integration tests

- One analysis response uses one common end date across modules.
- Missing symbols and unavailable histories produce explicit availability records.
- Core, sector, asset-class, country, and custom universes resolve to the correct versioned proxies.
- Cached and uncached requests return identical calculations.
- Provider fallback changes source metadata without silently changing chart type or available fields.

### Interface tests

- Analysis is the first market-navigation item.
- Controls are keyboard accessible and reflected in the URL.
- Chart legend controls and table sorting work without stale values.
- Heatmap is readable without relying on color alone.
- Long tables and charts work at mobile widths.
- Reduced-motion users receive a static historical-leader view.

## Risks and decisions that must remain visible

### Survivorship bias

A ranking of current companies over a historical period favors survivors. Version 1 should use transparent curated or current registries and label them. A defensible historical market leaderboard eventually requires licensed or maintained point-in-time constituents, delisted securities, corporate actions, mergers, and symbol history.

### Total-return interpretation

Adjusted provider bars must be documented consistently. If a module represents adjusted price rather than a fully reinvested total-return index, the page must not call it total return.

### Common-history compression

Adding a young asset can shorten the common RWI period. The UI should allow “strict common period” and later may add a clearly labeled staggered-start view. Strict common period is the default.

### Overlapping rolling windows

Daily rolling 5Y and 10Y windows are highly overlapping. The probability is descriptive, not a set of independent trials. Publish the methodology and optionally add non-overlapping annual cohorts later.

### Multiple comparisons

Large leaderboards create apparent winners by chance. Avoid significance language unless statistical controls are explicitly added.

### Provider limits and latency

Custom universes and long history multiply daily bars. Limit the MVP to 12 symbols, batch Alpaca requests, load BTC once, cache aggressively, and defer lower-page modules.

## Recommended first release

The first public Analysis release should contain only:

1. Relative Wealth Index.
2. BTC Opportunity Cost.
3. BTC Purchasing-Power Heatmap.

Those three features share one dataset, are understandable without advanced finance knowledge, and establish a coherent identity for SatValue. The next release should add rolling beat-BTC probabilities, BTC highs, BTC drawdowns, and Winners That Still Lost. Efficient-frontier and animated-leaderboard work should wait until the signature layer is stable and widely used.

## Definition of done

The Analysis page is complete only when:

- Analysis appears immediately left of Sectors on every primary page.
- Every visible metric comes from one aligned, versioned response.
- RWI, opportunity-cost, and heatmap formulas have automated tests.
- The page exposes effective dates, sources, proxies, missing history, and stale state.
- BTC-numeraire terminology is consistent throughout.
- Desktop, mobile, keyboard, reduced-motion, loading, empty, partial, and error states are verified.
- Shareable state recreates the selected universe and period.
- No placeholder, fabricated, shortened, or separately maintained result appears.
