# SatValue Roadmap

## Objective

Turn the current static prototype into a professional web application for viewing asset performance denominated in Bitcoin as the numeraire.

The site should feel familiar to users of Portfolio Visualizer and TradingView:

- clean research/dashboard UX
- fast symbol lookup
- high quality interactive charts
- professional return, risk, and drawdown tables
- sector and country browsing
- sensible MVP defaults so the first production version is complete, coherent, and easy to extend

## Core Financial Definition

For any asset with a USD price series:

`asset_btc_price_t = asset_usd_price_t / btc_usd_price_t`

From that derived BTC-denominated price series:

- period returns are computed normally from the BTC-denominated series
- cumulative returns are chained normally
- drawdowns are computed normally from the BTC-denominated wealth index
- rolling returns, CAGR, volatility, Sharpe-like statistics, and calendar returns are all based on the BTC-denominated return series

This means the app is not "showing BTC price". It is showing how an asset performs when Bitcoin is the unit of account.

## Product Vision

The MVP should answer these user questions immediately:

- How has `SPY` performed in BTC terms?
- How does one sector compare with another in BTC terms?
- Which countries or regional equity proxies have held value best versus BTC?
- What are the trailing returns, drawdowns, and calendar-year results?
- Can I search a symbol and get a clean chart plus summary table without configuration friction?

## MVP Scope

The first live version should include the features below and no more.

### 1. Research Dashboard

A primary research page with:

- symbol search
- asset metadata header
- interactive price chart in BTC terms
- trailing return table
- drawdown chart
- calendar returns table
- basic summary statistics

### 2. Browsing

Navigation and filtered views for:

- sectors
- industries
- countries
- asset classes

For MVP, these can be driven by curated datasets or mapping tables rather than a full commercial taxonomy system.

### 3. Comparison Mode

Support comparing a small number of series on one chart:

- default: one selected asset
- MVP comparison limit: up to 3 series

### 4. Time Controls

Support the standard ranges users expect:

- 1M
- 3M
- 6M
- YTD
- 1Y
- 3Y
- 5Y
- 10Y
- MAX

### 5. Metrics

MVP output should include:

- BTC-denominated price chart
- cumulative return
- trailing returns
- CAGR where applicable
- annualized volatility
- max drawdown
- drawdown series
- calendar year returns
- start date / end date

### 6. Default MVP Experience

The default landing experience should be opinionated:

- default symbol: `SPY`
- numeraire fixed to `BTC`
- default range: `MAX`
- default comparison: off
- default chart type: line
- default frequency: daily
- default metric cards: CAGR, max drawdown, latest price in BTC, latest price in sats

## Non-MVP, Later

These are valuable but should not block the first complete release:

- user accounts
- saved watchlists
- portfolio backtesting
- factor exposures
- optimization tools
- alerts
- export to PDF
- advanced technical studies
- intraday data
- authentication and billing

## Recommended Technical Direction

The current repo is too minimal to scale from as-is. The fastest professional path is:

- frontend: React + Vite + TypeScript
- styling: a disciplined design system with CSS variables and reusable layout/components
- charting:
  - either TradingView widget embeds for quick external charting where allowed
  - or a first-party charting layer using a professional chart library for full control
- data layer:
  - Alpaca as the upstream market-data provider for equities, ETFs, and reference market data
  - BTC/USD reference series sourced through the same server-side data pipeline
  - cached metadata for sectors, industries, countries, and asset classes
- API/backend:
  - lightweight SatValue server that computes BTC-denominated series and metrics
  - browser never calls Alpaca directly
  - server fetches Alpaca data, normalizes it, and caches responses
  - cache-first MVP with no database requirement
  - database introduced later only if advanced product features actually need persistence

### Default Live Data Architecture

For MVP, the live-data path should be:

- frontend calls SatValue-owned API endpoints only
- SatValue server proxies and normalizes Alpaca responses
- server caches market data and symbol metadata to protect against rate limits and repeated fetches
- BTC-denominated calculations are performed server-side from cached upstream USD data
- no persistent database is required for launch

This is the simplest path to:

- real ticker search
- live and historical data-backed pages
- hidden API keys
- low frontend complexity
- lower operational burden than frontend-direct provider access
- lower maintenance burden than introducing a DB too early

## Recommended Architecture

### Frontend

Create these top-level screens:

- `/` landing page with default `SPY` research view
- `/asset/:symbol` detailed research page
- `/compare` comparison workspace
- `/browse/sectors`
- `/browse/industries`
- `/browse/countries`
- `/browse/asset-classes`

Create these frontend modules:

- app shell and top navigation
- symbol search and autocomplete
- chart workspace
- return tables
- drawdown visualization
- calendar return grid
- metadata badges
- reusable empty/loading/error states

### Backend / Data Services

Create these backend responsibilities:

- fetch Alpaca asset metadata, snapshots, and historical bars
- cache symbol metadata for search and lookup
- cache BTC/USD history and asset USD price history
- align dates and handle missing values
- compute BTC-denominated price history on request
- compute return statistics and drawdowns server-side
- expose SatValue-owned API endpoints for frontend consumption
- hide provider credentials and provider-specific request details from the browser

### Cache Strategy

The cache layer is the rate-limit and reliability boundary for MVP.

- asset universe / symbol metadata: long TTL with scheduled refresh
- historical daily bars: long TTL and reused across repeated requests
- current snapshots / latest price data: short TTL
- BTC/USD reference series: cached like any other upstream series
- unsupported or not-found symbols: short negative cache
- cache may be in memory and/or on disk; no external cache service is required for MVP

### Data Model

For MVP, think in terms of logical resources and caches rather than persisted database tables.

Core resources:

- instruments / metadata cache
- historical bars cache
- BTC/USD reference series cache
- derived BTC-denominated series generated on request
- optional disk cache for repeated symbol queries

Minimum metadata fields:

- symbol
- name
- exchange
- country
- sector
- industry
- asset_class
- first_available_date
- last_available_date

Persistence is optional for MVP. A database should only be introduced later if the product needs durable state for user accounts, watchlists, precomputed rankings, analytics, billing, or heavier cross-sectional querying.

## API Plan

MVP endpoints:

- `GET /api/search?q=spy`
- `GET /api/assets/:symbol`
- `GET /api/assets/:symbol/chart?range=MAX`
- `GET /api/assets/:symbol/returns`
- `GET /api/assets/:symbol/drawdowns`
- `GET /api/assets/:symbol/calendar-returns`
- `GET /api/browse/sectors`
- `GET /api/browse/sectors/:sector`
- `GET /api/browse/countries`
- `GET /api/browse/countries/:country`
- `GET /api/snapshots?symbols=SPY,QQQ,XLC`

Comparison endpoint:

- `GET /api/compare?symbols=SPY,QQQ,EFA&range=5Y`

These are SatValue server endpoints backed by Alpaca. They should normalize upstream data, enforce caching, and hide credentials and provider-specific response shapes from the frontend.

## UI / UX Requirements

To feel professional, the UI should borrow the interaction patterns users already understand:

### Portfolio Visualizer-style elements

- table-dense research layout
- visible date range controls
- clear metric headings
- sortable tables
- clean typography and restrained colors
- easy-to-scan tabular outputs

### TradingView-style elements

- prominent symbol header
- crisp chart area
- responsive crosshair or hover states
- range buttons above chart
- comparison overlay support
- polished chart legend and series labels

### SatValue-specific requirements

- every displayed number should clearly indicate BTC denomination where needed
- sats display should be available for intuitive scale
- tooltips should explain that asset BTC value is `asset_usd / btc_usd`
- users should never confuse nominal USD returns with BTC-denominated returns

## Data and Calculation Rules

These rules should be fixed early and documented in code:

### Series Alignment

- use daily data for MVP
- align asset and BTC series by date
- use only dates where both values exist
- corporate action-adjusted asset prices are preferred

### Return Calculation

- daily return: `(btc_price_t / btc_price_t-1) - 1`
- cumulative index starts at 1.0 or 100
- trailing return windows use the BTC-denominated series, not USD

### Drawdown Calculation

- compute wealth index from BTC returns
- compute rolling peak on wealth index
- drawdown = `(wealth / rolling_peak) - 1`

### Missing Data

- no forward-filling across long gaps for traded assets
- show partial-history warnings if date coverage is short
- comparison mode uses intersection dates by default for fair comparison

## Delivery Phases

## Phase 0. Foundation Reset

Goal: replace the current static prototype with a buildable local app skeleton.

Tasks:

- create a modern frontend app structure
- introduce TypeScript
- create a shared layout and design tokens
- remove dead demo code and placeholders
- create a lightweight dev server workflow

Definition of done:

- app runs on localhost
- browser shows a real app shell, not a static mock
- codebase has folders for pages, components, services, and mock data

## Phase 1. Fake Data MVP UI

Goal: build the complete user interface with mock data before worrying about live data quality.

Tasks:

- build asset research page
- build header, search box, range selector, chart frame, trailing returns, drawdown panel, and calendar returns table
- create browse pages for sectors and countries
- wire MVP defaults

Definition of done:

- users can click through a full realistic product flow
- all major layouts exist
- browser-refresh workflow is productive

## Phase 2. Calculation Engine

Goal: implement trustworthy BTC-denominated calculations.

Tasks:

- create functions to derive BTC-denominated price series
- compute daily returns, cumulative returns, CAGR, volatility, max drawdown, and calendar returns
- add test coverage for calculation correctness

Definition of done:

- calculation module is independently testable
- known examples produce expected outputs

## Phase 3. Live Data Integration

Goal: connect the UI to real data.

Tasks:

- integrate Alpaca as the upstream market-data source
- source asset USD price history
- source BTC/USD history
- build server-side symbol search from cached asset metadata
- build the API endpoints
- cache bars, snapshots, and metadata responses
- compute BTC-denominated series from cached upstream data

Definition of done:

- live symbol lookup works
- default `SPY` page renders from real data
- charts and tables update from API responses

## Phase 4. Browse and Compare

Goal: make the site useful beyond single-symbol lookup.

Tasks:

- sector landing pages
- country landing pages
- compare up to 3 symbols
- ranking tables by BTC performance over selected windows

Definition of done:

- browsing feels coherent
- comparisons are readable and fast

## Phase 5. Professional Polish

Goal: make the site production-presentable.

Tasks:

- loading skeletons
- error states
- consistent typography and spacing
- mobile and tablet responsiveness
- accessibility cleanup
- SEO metadata
- favicon, social preview, and polished branding

Definition of done:

- no placeholder content remains
- product looks intentional and publishable

## Phase 6. Production Readiness

Goal: prepare for deployment and maintenance.

Tasks:

- environment configuration
- deploy target selection
- observability/logging
- upstream failure handling
- cache invalidation / TTL tuning
- provider rate-limit handling
- secret management for Alpaca credentials
- smoke tests
- basic analytics

Definition of done:

- reproducible local setup
- documented deploy path
- stable enough for public sharing

Later, if product requirements expand, persistent storage can be added for user accounts, saved watchlists, precomputed rankings/screens, analytics, heavy cross-sectional querying, or billing/auth state.

## Proposed Folder Structure

Once rebuilt, the repo should roughly look like:

```text
satvalue-main/
  docs/
    ROADMAP.md
  src/
    app/
    components/
    features/
      asset-research/
      browse/
      compare/
    services/
      api/
      calculations/
      formatters/
    data/
      mock/
    styles/
  server/
    api/
    data/
    services/
  tests/
  public/
```

## Immediate Build Order

This is the most efficient order to work through with visible progress after every task.

1. Replace the current static site with a local app scaffold and dev server.
2. Build the app shell and navigation.
3. Build the asset research page with mock data.
4. Build the trailing returns and drawdown components.
5. Build the browse pages for sectors and countries.
6. Implement the BTC denomination calculation module and tests.
7. Connect the UI to a real API/data source.
8. Add comparison mode.
9. Polish responsiveness, states, and visual quality.
10. Prepare deployment.

## Localhost Workflow Recommendation

To move quickly and review each change visually, use this workflow:

### Setup

- run a frontend dev server on localhost
- keep one browser tab pinned to the app
- use browser refresh after every completed subtask
- keep scope narrow: one visible slice of UI or one backend capability at a time

### Working Rhythm

For each roadmap item:

1. implement one thin slice
2. refresh browser
3. verify layout or behavior immediately
4. fix visual or functional regressions before moving on

### First Milestone to Target

The best first milestone is:

"A professional local app shell on localhost with a search bar, symbol header, chart placeholder, trailing returns table, drawdown panel, and sector/country navigation using mock data."

That milestone gives immediate visual feedback and creates the foundation for real calculations and live data.

## Acceptance Criteria for MVP Launch

The MVP is ready when all of the following are true:

- site runs reliably on localhost
- default `SPY` research view is complete
- chart, trailing returns, drawdowns, and calendar returns all render from the same BTC-denominated dataset
- sector and country browsing exists
- users can search and open supported symbols
- comparison mode works for up to 3 symbols
- styling is consistent and professional
- no placeholder percentages remain
- the site communicates clearly that Bitcoin is the numeraire

## Recommended Next Action

Start with Phase 0 immediately:

- scaffold the real app
- get localhost running
- keep a browser open
- rebuild the current page into a reusable research dashboard with mock data first

After that foundation is in place, every subsequent task will be visible in the browser and much easier to validate.
