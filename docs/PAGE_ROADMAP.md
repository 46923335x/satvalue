# SatValue Page and Data Roadmap

## Implementation status — August 1, 2026

Milestones A through F are complete in the current build.

Milestones G through L are planned for the new Analysis product. The comprehensive specification, formulas, delivery sequence, API contract, and acceptance gates are maintained in [ANALYSIS_ROADMAP.md](ANALYSIS_ROADMAP.md).

| Milestone | Status | Delivered |
|---|---|---|
| A — Navigation and research reliability | Complete | Unified navigation/search, shared line/candle chart engine, exact ranges, loading/error states, risk metrics, drawdowns, calendar returns, and metadata |
| B — Complete sectors | Complete | Eleven-proxy common-date rankings, reusable sector detail route, and automatic State Street fund holdings/industry allocations |
| C — Complete asset classes | Complete | Versioned ten-proxy registry, common-date rankings, proxy disclosures, and detail pages |
| D — Replace countries prototype | Complete | Twelve live proxies; one API payload drives the map and table; issuer links, inception dates, and common as-of date |
| E — Production quality | Complete | Mobile and keyboard QA, explicit cache/stale policy, upstream health endpoint, security headers, minimal analytics, SEO files, legal pages, and container deployment package |
| F — Portfolio backtest | Complete | Weighted 2–20 holding backtests, optional start date, four rebalancing choices, USD/BTC/SPY comparisons, risk metrics, rolling returns, calendar returns, and aligned-history warnings |

## Product navigation

The primary navigation is now:

1. Sectors
2. Asset Classes
3. Countries
4. Portfolio

Industries is removed from the primary product scope. Portfolio links to the completed basic backtest.

## Non-negotiable data contract

Every published number must satisfy all of these rules:

- The page identifies the market proxy, upstream source, and as-of date.
- Equity data uses adjusted, completed daily SIP bars from Alpaca.
- BTC/USD uses Coinbase Exchange daily OHLC; Coin Metrics `PriceUSD` is a closing-value fallback only.
- Asset and BTC observations are aligned to a shared date before ratios are calculated.
- Trailing returns use exact calendar targets and the closest observation on or before the target.
- Rankings use one common end date across every row.
- Holdings and classifications come from the ETF issuer, not hand-entered estimates.
- Missing history displays `--`; it is never filled with fabricated data.
- Stale, partial, and upstream-error states are visibly different from valid results.
- Calculation tests cover ratio OHLC, trailing returns, CAGR, volatility, drawdown, and portfolio rebalancing.

## Canonical sources

| Data | Primary source | Fallback or validation | Notes |
|---|---|---|---|
| US equity and ETF OHLC | Alpaca historical SIP bars | Issuer closing price for spot checks | Adjusted bars; completed sessions only |
| BTC/USD OHLC | Coinbase Exchange BTC-USD candles | Coin Metrics `PriceUSD` | Coinbase enables candles; Coin Metrics fallback renders a line |
| Sector ETF holdings and industry allocation | State Street Select Sector SPDR fund pages/downloads | Fund factsheet | Store issuer as-of date with every snapshot |
| Country ETF holdings and metadata | iShares fund pages/downloads | Fund factsheet | Country pages represent investable ETF proxies, not national indexes |
| Asset-class taxonomy | Versioned SatValue proxy registry | Issuer fund pages | Each proxy and replacement requires review |

## Page inventory

### 1. Research view

Route: `/index.html?symbol=SPY`

Purpose: exact-symbol research for any supported US stock or ETF.

Required output:

- symbol and security name
- BTC-denominated candle chart
- source and as-of metadata
- trailing returns
- CAGR, annualized volatility, maximum drawdown, current drawdown
- drawdown chart
- calendar-year return table
- available start and end dates

Current status:

- Live symbol search, shared line/candle chart, exact ranges, trailing returns, summary statistics, drawdowns, calendar returns, and registry-backed security metadata are working.
- Unsupported symbols clear all prior values and display a useful upstream error.

Acceptance gate:

- Search, button click, and Enter key all open the same symbol.
- Unsupported symbols show a useful error without leaving stale values onscreen.
- Every metric is calculated from the same aligned ratio series.

### 2. Sectors landing page

Route: `/sectors.html`

Use the eleven Select Sector SPDR proxies:

| Sector | Proxy |
|---|---|
| Communication Services | XLC |
| Consumer Discretionary | XLY |
| Consumer Staples | XLP |
| Energy | XLE |
| Financials | XLF |
| Health Care | XLV |
| Industrials | XLI |
| Materials | XLB |
| Real Estate | XLRE |
| Technology | XLK |
| Utilities | XLU |

Required output:

- sortable BTC-relative returns for YTD, 1Y, 3Y, 5Y, and 10Y
- common as-of date and explicit proxy column
- heatmap or ranked table
- links to parameterized sector detail pages

Acceptance gate:

- All sectors are recalculated from one API response and common date window.
- A missing or younger ETF never silently receives a shortened-period return.

### 3. Sector detail page

Route target: `/sector.html?symbol=XLC`

The existing Communication Services page becomes the reusable template.

Current status: all eleven sector funds refresh top holdings and industry allocations automatically from State Street through `/api/fund?symbol=...`, with a six-hour cache and explicit stale/error behavior.

Required output:

- live BTC-relative research chart and metrics
- issuer-sourced top holdings
- issuer-sourced industry allocation
- fund name, benchmark, expense ratio, inception date, and holdings as-of date

Acceptance gate:

- No sector description, holding, or weight remains hard-coded without an issuer snapshot date.
- The page clearly separates fund holdings from index holdings.

### 4. Asset Classes

Routes: `/asset-classes.html` and `/asset-class.html?key=...`

Initial versioned proxy registry:

| Asset class | Initial proxy |
|---|---|
| US equities | SPY |
| International developed equities | VEA |
| Emerging-market equities | VWO |
| US Treasuries | IEF |
| Investment-grade corporate bonds | LQD |
| High-yield corporate bonds | HYG |
| Gold | GLD |
| US real estate | VNQ |
| Broad commodities | DBC |
| Bitcoin | BTC/USD |

Required output mirrors the sector landing and detail views. Each page must say that the result represents the listed investable proxy rather than the entire conceptual asset class.

### 5. Countries

Route: `/countries.html`

Initial proxy registry:

| Country | Initial proxy |
|---|---|
| Australia | EWA |
| Brazil | EWZ |
| Canada | EWC |
| China | MCHI |
| France | EWQ |
| Germany | EWG |
| Italy | EWI |
| Japan | EWJ |
| South Korea | EWY |
| Switzerland | EWL |
| United Kingdom | EWU |
| United States | SPY |

Required output:

- map and table driven by the same calculated API payload
- explicit ETF proxy in tooltips and table rows
- common as-of date
- exact-period BTC-relative returns
- issuer link and fund inception date

Acceptance gate:

- Remove all prototype country percentages before launch.
- The map and table must never contain separately maintained values.

### 6. Portfolio

Route: `/portfolio.html`

Delivered basic backtest scope:

- 2-20 ticker holdings with weights totaling 100%
- optional start date
- monthly, quarterly, annual, or no rebalancing
- buy-and-hold portfolio value in USD and BTC terms
- comparison with BTC and SPY
- CAGR, volatility, max drawdown, rolling returns, and calendar returns
- clear treatment of dividends, splits, missing history, and delisted symbols

Portfolio calculations reuse the completed single-asset data contract and expose effective shared-history dates whenever the requested period must be shortened.

## Delivery order

### Milestone A — Navigation and research reliability

Status: Complete.

- Reorder navigation and add inactive Portfolio placeholder.
- Make exact-symbol search work consistently on every page.
- Finish research metrics, loading states, and error states.
- Extract shared chart and calculation modules.

### Milestone B — Complete sectors

Status: Complete.

- Build the eleven-sector live ranking endpoint and landing page.
- Convert Communication Services into a reusable sector template.
- Automate issuer holdings and industry snapshots.

### Milestone C — Complete asset classes

Status: Complete.

- Implement and version the proxy registry.
- Build landing and detail pages from the shared components.
- Review proxy choices and disclosures.

### Milestone D — Replace the countries prototype

Status: Complete.

- Implement the country proxy registry and batch ranking endpoint.
- Drive both map and table from the same payload.
- Remove every hard-coded country return.

### Milestone E — Production quality

Status: Complete. The build includes a Docker deployment contract; production credentials must be supplied through the chosen host's secret store.

- Mobile and keyboard testing.
- Staleness monitoring and upstream health checks.
- Server-side cache with explicit refresh policy.
- SEO, legal pages, analytics, and deployment.

### Milestone F — Portfolio backtest

Status: Complete.

- Accept 2–20 unique US stock or ETF holdings whose weights total 100%.
- Support optional start dates and monthly, quarterly, annual, or no rebalancing.
- Compare a normalized $10,000 portfolio with SPY and Bitcoin in USD and BTC terms.
- Report cumulative trailing returns, CAGR, volatility, drawdown, rolling one-year returns, and calendar returns.
- Surface shared-history adjustments, data sources, as-of dates, and adjusted-price methodology.

## Definition of done for a page

A page is complete only when it has live data, a source, an as-of date, loading and error states, responsive behavior, keyboard support, automated calculation coverage, and no unlabeled placeholder values.
