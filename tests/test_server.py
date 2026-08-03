import unittest
from datetime import date
from io import BytesIO

from server import ASSET_CLASSES, COUNTRIES, MarketDataError, PortfolioValidationError, build_portfolio_values, build_ratio_series, calendar_returns, canonical_symbol, extract_morningstar_company_description, extract_morningstar_etf_payload, extract_morningstar_etf_strategy, extract_morningstar_strategy_response, extract_yahoo_etf_description, monthly_calendar_returns, morningstar_exchange_slug, parse_state_street_xlc, read_request_body, research_metrics, return_for_target, rolling_returns, security_metadata, summarize_company_description, trailing_returns, validate_portfolio_request


class RequestBodyTests(unittest.TestCase):
    def test_reads_content_length_body(self):
        body = b'{"holdings":[]}'
        self.assertEqual(read_request_body({"Content-Length": str(len(body))}, BytesIO(body), 1024), body)

    def test_reads_chunked_body_used_by_reverse_proxies(self):
        encoded = b'5\r\n{"hol\r\nA\r\ndings":[]}\r\n0\r\n\r\n'
        self.assertEqual(
            read_request_body({"Transfer-Encoding": "chunked"}, BytesIO(encoded), 1024),
            b'{"holdings":[]}',
        )

    def test_rejects_chunked_body_over_limit(self):
        with self.assertRaises(MarketDataError):
            read_request_body({"Transfer-Encoding": "chunked"}, BytesIO(b'5\r\nhello\r\n0\r\n\r\n'), 4)


class SymbolTests(unittest.TestCase):
    def test_legacy_fb_symbol_uses_meta_history(self):
        self.assertEqual(canonical_symbol("FB"), "META")

    def test_company_profile_summary_removes_markup_and_limits_length(self):
        text = "<p>First sentence about the company.</p> Second sentence provides useful context. " + ("Extra detail. " * 80)
        summary = summarize_company_description(text, 120)
        self.assertNotIn("<p>", summary)
        self.assertLessEqual(len(summary), 120)

    def test_extracts_complete_morningstar_company_profile(self):
        markup = '<div><span itemprop="description">First sentence. <em>Second</em> sentence &amp; detail.</span></div>'
        self.assertEqual(
            extract_morningstar_company_description(markup),
            "First sentence. Second sentence & detail.",
        )

    def test_extracts_complete_morningstar_etf_strategy(self):
        markup = '<div class="sal-mip-strategy__body">Track the broad market. <strong>Invests</strong> at least 80%.</div>'
        self.assertEqual(
            extract_morningstar_etf_strategy(markup),
            "Track the broad market. Invests at least 80%.",
        )

    def test_extracts_morningstar_etf_strategy_payload_without_executing_page_script(self):
        markup = '''<script>window.__NUXT__=(function(a,b,c){return {helper:function(){return {}},security:{securityID:a},strategy:{status:"ok",payload:{contentType:b,token:c}}}}("FEUSA0002P","content-marker","temporary-token"));</script>'''
        self.assertEqual(
            extract_morningstar_etf_payload(markup),
            {"securityId": "FEUSA0002P", "contentType": "content-marker", "token": "temporary-token"},
        )

    def test_extracts_strategy_text_from_nested_service_response(self):
        payload = {"data": {"investmentStrategy": "The fund seeks broad-market exposure and normally invests substantially all assets in its target index."}}
        self.assertEqual(
            extract_morningstar_strategy_response(payload),
            payload["data"]["investmentStrategy"],
        )

    def test_extracts_etf_description_from_fallback_profile(self):
        payload = {"quoteSummary": {"result": [{"summaryProfile": {"longBusinessSummary": "The fund tracks a diversified value index.  It normally invests at least 80% in index constituents."}}]}}
        self.assertEqual(
            extract_yahoo_etf_description(payload),
            "The fund tracks a diversified value index. It normally invests at least 80% in index constituents.",
        )

    def test_maps_alpaca_exchange_to_morningstar_market(self):
        self.assertEqual(morningstar_exchange_slug("NASDAQ"), "xnas")
        self.assertEqual(morningstar_exchange_slug("NYSE"), "xnys")
        self.assertIsNone(morningstar_exchange_slug("UNKNOWN"))


class RatioSeriesTests(unittest.TestCase):
    def test_monthly_calendar_quilt_uses_previous_month_and_year_end(self):
        series = [
            {"time": "2024-12-31", "close": 100},
            {"time": "2025-01-31", "close": 110},
            {"time": "2025-02-28", "close": 99},
            {"time": "2025-12-31", "close": 120},
        ]
        rows = monthly_calendar_returns(series)
        self.assertEqual(rows[0]["year"], 2025)
        self.assertAlmostEqual(rows[0]["months"][0], 10.0)
        self.assertAlmostEqual(rows[0]["months"][1], -10.0)
        self.assertAlmostEqual(rows[0]["ytd"], 20.0)

    def test_ratio_uses_crossed_high_low_bounds(self):
        stock = [{"t": "2026-01-02T05:00:00Z", "o": 100, "h": 110, "l": 90, "c": 105}]
        btc = [{"t": "2026-01-02T00:00:00Z", "o": 50, "h": 55, "l": 45, "c": 52.5}]
        point = build_ratio_series(stock, btc)[0]
        self.assertAlmostEqual(point["open"], 2.0)
        self.assertAlmostEqual(point["high"], 110 / 45)
        self.assertAlmostEqual(point["low"], 90 / 55)
        self.assertAlmostEqual(point["close"], 2.0)

    def test_return_uses_closest_point_on_or_before_target(self):
        series = [
            {"time": "2025-01-03", "close": 1.0},
            {"time": "2025-01-06", "close": 1.1},
            {"time": "2026-01-05", "close": 1.5},
        ]
        self.assertAlmostEqual(return_for_target(series, date(2025, 1, 5)), 50.0)

    def test_metrics_include_cagr_volatility_and_drawdowns(self):
        series = [
            {"time": "2024-01-02", "close": 1.0},
            {"time": "2024-12-31", "close": 2.0},
            {"time": "2025-12-31", "close": 1.5},
        ]
        metrics = research_metrics(series)
        self.assertAlmostEqual(metrics["cagr"], (1.5 ** 0.5 - 1) * 100, delta=0.3)
        self.assertGreater(metrics["annualizedVolatility"], 0)
        self.assertAlmostEqual(metrics["maxDrawdown"], -25.0)
        self.assertAlmostEqual(metrics["currentDrawdown"], -25.0)

    def test_calendar_returns_use_prior_year_end(self):
        series = [
            {"time": "2023-12-29", "close": 1.0},
            {"time": "2024-12-31", "close": 1.25},
            {"time": "2025-12-31", "close": 1.0},
        ]
        rows = calendar_returns(series)
        self.assertEqual(rows[0]["year"], 2025)
        self.assertAlmostEqual(rows[0]["return"], -20.0)
        self.assertAlmostEqual(rows[1]["return"], 25.0)

    def test_trailing_returns_do_not_fill_missing_history(self):
        series = [{"time": "2026-01-02", "close": 1.0}, {"time": "2026-07-31", "close": 1.2}]
        values = trailing_returns(series)
        self.assertIsNone(values["1-Year"])
        self.assertIsNone(values["10-Year"])


class StateStreetParserTests(unittest.TestCase):
    def test_parses_published_holdings_and_industry_tables(self):
        holdings = "".join(
            f"<tr><td>{name}</td><td>1,000</td><td>{weight}%</td></tr>"
            for name, weight in [
                ("META PLATFORMS INC CLASS A", "16.28"),
                ("ALPHABET INC CL A", "10.44"),
                ("ALPHABET INC CL C", "8.42"),
                ("AT+T INC", "4.85"),
                ("VERIZON COMMUNICATIONS INC", "4.77"),
            ]
        )
        allocations = "".join(
            f"<tr><td>{name}</td><td>{weight}%</td></tr>"
            for name, weight in [
                ("Interactive Media &amp; Services", "35.20"),
                ("Entertainment", "29.30"),
                ("Media", "16.85"),
                ("Diversified Telecommunication Services", "14.11"),
                ("Wireless Telecommunication Services", "4.55"),
            ]
        )
        page = f"""
            <h3>Fund Top Holdings <span class="date">as of Jul 30 2026</span></h3>
            <table><tbody>{holdings}</tbody></table>
            <h3>Fund Industry Allocation <span class="date">as of Jul 30 2026</span></h3>
            <table><tbody>{allocations}</tbody></table>
        """
        payload = parse_state_street_xlc(page)
        self.assertEqual(payload["asOf"], "2026-07-30")
        self.assertEqual(payload["topHoldings"][0], {"name": "Meta Platforms Class A", "weight": 16.28})
        self.assertEqual(payload["industryAllocations"][0]["name"], "Interactive Media & Services")


class RegistryCopyTests(unittest.TestCase):
    def test_asset_proxy_labels_are_specific(self):
        assets = {item["symbol"]: item for item in ASSET_CLASSES}
        self.assertEqual(assets["VTI"]["name"], "US Stock Market")
        self.assertEqual(assets["SHY"]["name"], "Short Treasuries")
        self.assertEqual(assets["IEF"]["name"], "Intermediate Treasuries")
        self.assertEqual(assets["TLT"]["name"], "Long Treasuries")
        self.assertEqual(assets["BNDX"]["name"], "Global Bonds")

    def test_bitcoin_uses_data_start_instead_of_fund_inception(self):
        bitcoin = security_metadata("BTCUSD")
        self.assertEqual(bitcoin["dataStartDate"], "2015-07-20")
        self.assertNotIn("inceptionDate", bitcoin)

    def test_country_proxies_use_direct_issuer_pages(self):
        for country in COUNTRIES:
            with self.subTest(symbol=country["symbol"]):
                self.assertNotIn("search=", country["issuerUrl"])
                if country["symbol"] != "SPY":
                    self.assertRegex(country["issuerUrl"], r"ishares\.com/us/products/\d+$")


class PortfolioBacktestTests(unittest.TestCase):
    def setUp(self):
        self.dates = ["2026-01-30", "2026-02-02", "2026-02-27"]
        self.closes = {
            "AAA": dict(zip(self.dates, [100.0, 200.0, 200.0])),
            "BBB": dict(zip(self.dates, [100.0, 100.0, 200.0])),
        }
        self.btc = dict(zip(self.dates, [50000.0, 50000.0, 50000.0]))
        self.spy = dict(zip(self.dates, [100.0, 110.0, 120.0]))
        self.benchmarks = {"SPY": self.spy}
        self.weights = {"AAA": 0.5, "BBB": 0.5}

    def test_no_rebalancing_preserves_initial_share_counts(self):
        rows = build_portfolio_values(self.dates, self.closes, self.btc, self.benchmarks, self.weights, "none")
        self.assertAlmostEqual(rows[0]["portfolioBtc"], 10.0)
        self.assertAlmostEqual(rows[-1]["portfolioUsd"], 1000000.0)
        self.assertAlmostEqual(rows[-1]["btcUsd"], 500000.0)
        self.assertAlmostEqual(rows[-1]["benchmarksUsd"]["SPY"], 600000.0)
        self.assertAlmostEqual(rows[-1]["portfolioBtc"], 20.0)
        self.assertAlmostEqual(rows[-1]["benchmarksBtc"]["SPY"], 12.0)
        self.assertTrue(all(row["bitcoinBtc"] == 10.0 for row in rows))

    def test_monthly_rebalancing_resets_weights_after_period_change(self):
        rows = build_portfolio_values(self.dates, self.closes, self.btc, self.benchmarks, self.weights, "monthly")
        self.assertAlmostEqual(rows[1]["portfolioUsd"], 750000.0)
        self.assertAlmostEqual(rows[-1]["portfolioUsd"], 1125000.0)

    def test_request_requires_unique_holdings_totaling_one_hundred_percent(self):
        with self.assertRaisesRegex(PortfolioValidationError, "total 100"):
            validate_portfolio_request({"holdings": [{"symbol": "SPY", "weight": 60}, {"symbol": "QQQ", "weight": 30}]})
        with self.assertRaisesRegex(PortfolioValidationError, "duplicate"):
            validate_portfolio_request({"holdings": [{"symbol": "SPY", "weight": 50}, {"symbol": "SPY", "weight": 50}]})

    def test_optional_start_date_accepts_json_null(self):
        weights, rebalancing, requested_start, benchmarks = validate_portfolio_request({
            "holdings": [{"symbol": "SPY", "weight": 60}, {"symbol": "QQQ", "weight": 40}],
            "startDate": None,
            "benchmarks": ["VTI", "QQQ"],
        })
        self.assertEqual(weights, {"SPY": 0.6, "QQQ": 0.4})
        self.assertEqual(rebalancing, "monthly")
        self.assertIsNone(requested_start)
        self.assertEqual(benchmarks, ["VTI", "QQQ"])

    def test_benchmark_tickers_accept_comma_separated_text(self):
        _, _, _, benchmarks = validate_portfolio_request({
            "holdings": [{"symbol": "SPY", "weight": 60}, {"symbol": "QQQ", "weight": 40}],
            "benchmarks": "VTI, QQQ",
        })
        self.assertEqual(benchmarks, ["VTI", "QQQ"])

    def test_rolling_returns_use_calendar_targets(self):
        series = [
            {"time": "2024-01-31", "close": 100.0},
            {"time": "2025-01-30", "close": 120.0},
            {"time": "2025-01-31", "close": 125.0},
        ]
        rows = rolling_returns(series)
        self.assertEqual(rows[-1]["time"], "2025-01-31")
        self.assertAlmostEqual(rows[-1]["value"], 25.0)


if __name__ == "__main__":
    unittest.main()
