"""Offline You request contracts; no vendor or judge calls."""
import os
import unittest
from unittest.mock import patch
from websearch import run_official_news_probe as news
from websearch import score_official_search_metrics as score


class YouContracts(unittest.TestCase):
    def test_highlights_requests(self):
        payload = {"results": {"web": [{"url": "https://example.com", "snippets": ["fallback"],
                   "contents": {"highlights": ["Relevant evidence"]}}]}}
        for arm in ("you_highlights", "you_highlights_core"):
            with self.subTest(arm=arm), patch.dict(os.environ, {"YDC_API_KEY": "test-key"}):
                body = {"query": "Unchanged question?", "count": 10,
                        "extraction": {"extraction_mode": "highlights"}}
                if arm.endswith("_core"):
                    body["knowledge"] = "core"
                with patch.object(news, "_http", return_value={"ok": True, "response": payload}) as call:
                    hits, _ = news.call_endpoint(arm, "Unchanged question?", {})
                self.assertEqual(call.call_count, 1)
                self.assertEqual(call.call_args.kwargs["body"], body)
                self.assertEqual(call.call_args.kwargs["url"], "https://ydc-index.io/v1/search")
                self.assertEqual(hits[0]["snippet"], "Relevant evidence")
                self.assertEqual(news._parse_endpoints(arm), [arm])
                self.assertIn(arm, score.ENDPOINTS)

    def test_retired_plain_search_not_in_roster(self):
        with self.assertRaises(SystemExit):
            news._parse_endpoints("you")


if __name__ == "__main__":
    unittest.main()
