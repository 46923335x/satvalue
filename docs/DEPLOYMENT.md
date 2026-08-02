# SatValue deployment

SatValue is packaged as a small containerized web service because its live data endpoints must keep Alpaca credentials on the server. It must not be deployed as a static-only site.

## Required production configuration

- `ALPACA_API_KEY_ID`: secret Alpaca key identifier
- `ALPACA_API_SECRET_KEY`: secret Alpaca key
- `HOST=0.0.0.0`
- `PORT`: supplied by the hosting platform, default `9000`

Never place the Alpaca values in HTML, JavaScript, an image, a repository, or a public build artifact. Rotate any credential that has been shared outside the deployment secret store.

## Container contract

- Build from the repository `Dockerfile`.
- Route HTTPS traffic to the container port.
- Configure the health check as `GET /api/health`.
- Keep at least one warm instance; market and issuer caches are process-local.
- Use a persistent log drain for request and upstream errors. Aggregate page-view analytics are intentionally memory-only and reset on restart.

## Refresh and stale policy

- Single-symbol market series: 5 minutes
- Browse rankings: 15 minutes
- State Street holdings and allocations: 6 hours
- Failed fund refreshes never masquerade as fresh data. XLC has a labeled last-verified fallback; other sector failures display an upstream error.

## Smoke test

After deployment, verify `/api/health`, `/api/series?symbol=SPY`, `/api/rankings?group=sectors`, and `/api/fund?symbol=XLC`, then load the research, sectors, asset classes, and countries pages at desktop and mobile widths.
