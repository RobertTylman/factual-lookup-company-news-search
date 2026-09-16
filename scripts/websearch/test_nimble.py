"""Offline Nimble request-contract tests; no credentials or API calls required."""

import os
import unittest
from unittest.mock import patch

from websearch import run_official_news_probe as runner
from websearch.score_official_search_metrics import ENDPOINTS as SCORED_ENDPOINTS


class NimbleTests(unittest.TestCase):
    def test_depths_use_search_only_and_normalize_results(self):
        response = {"results": [
            {"url": "https://example.com/news", "title": "News",
             "description": "Search evidence", "content": "Full page must not leak"},
            {"url": "https://example.com/news", "description": "Duplicate"},
            None, {"title": "Missing URL"},
            *[{"url": f"https://example.com/{i}", "description": str(i)} for i in range(12)],
        ]}
        for depth in ("lite", "lite_news", "standard"):
            endpoint = f"nimble_{depth}"
            with self.subTest(depth=depth), patch.dict(os.environ, {"NIMBLE_API_KEY": "test"}), patch.object(
                runner, "_http", return_value={"ok": True, "response": response}
            ) as http:
                hits, _ = runner.call_endpoint(endpoint, "Unmodified question?", {})
                self.assertEqual(http.call_args.kwargs["body"], {
                    "query": "Unmodified question?", "search_depth": "standard" if depth == "standard" else "lite",
                    "full_content": False, "focus": "news" if depth == "lite_news" else "general", "max_results": 10,
                })
                self.assertEqual(http.call_args.kwargs["url"], "https://sdk.nimbleway.com/v2/search")
                self.assertEqual(http.call_args.kwargs["headers"]["Authorization"], "Bearer test")
                self.assertEqual(len(hits), 10)
                self.assertEqual(hits[0]["snippet"], "Search evidence")
                self.assertEqual(len({h["url"] for h in hits}), 10)
                self.assertIn(endpoint, runner.ENDPOINTS)
                self.assertIn(endpoint, SCORED_ENDPOINTS)

    def test_failed_request_does_not_extract_error_body(self):
        with patch.dict(os.environ, {"NIMBLE_API_KEY": "test"}), patch.object(
            runner, "_http", return_value={"ok": False, "status_code": 401, "response": {}}
        ):
            hits, raw = runner.call_endpoint("nimble_standard", "Question", {})
        self.assertEqual(hits, [])
        self.assertEqual(raw["status_code"], 401)

    def test_missing_descriptions_do_not_fall_back_to_full_content(self):
        self.assertEqual(runner._parse_nimble(None), [])
        hits = runner._parse_nimble({"results": [{"url": "https://example.com", "content": "page"}]})
        self.assertEqual(hits[0]["snippet"], "")




if __name__ == "__main__":
    unittest.main()
