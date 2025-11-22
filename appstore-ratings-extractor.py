import argparse
import json
import re
import sys
from typing import Any, Dict, List, TypedDict

import requests
from requests import Response
from requests.exceptions import HTTPError, RequestException

PRODUCT_RATINGS_PATTERN = re.compile(
    r'"contentType":"productRatings","marker":null,"items":\[(\{.*?\})\]',
    re.DOTALL,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/129.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class RatingSummary(TypedDict):
    ratingAverage: float
    totalNumberOfRatings: int
    ratingCounts: List[int]


def fetch_product_ratings(app_id: str, country: str) -> RatingSummary:
    """
    Fetch the rating histogram from the public App Store product page.

    The `ratingCounts` array is ordered by descending star value (5 ➝ 1).
    """
    url = f"https://apps.apple.com/{country}/app/id{app_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except HTTPError as exc:  # pragma: no cover - network error passthrough
        raise RuntimeError(f"App Store page returned HTTP {exc.response.status_code}") from exc
    except RequestException as exc:  # pragma: no cover - network error passthrough
        raise RuntimeError(f"Failed to fetch App Store page: {exc}") from exc

    data = _extract_product_ratings(response)
    return {
        "ratingAverage": data["ratingAverage"],
        "totalNumberOfRatings": data["totalNumberOfRatings"],
        "ratingCounts": data["ratingCounts"],
    }


def _extract_product_ratings(response: Response) -> Dict[str, Any]:
    match = PRODUCT_RATINGS_PATTERN.search(response.text)
    if not match:
        raise RuntimeError("productRatings block not found in HTML response")
    block = match.group(1)
    try:
        parsed = json.loads(f"[{block}]")[0]
    except json.JSONDecodeError as exc:  # pragma: no cover - unexpected payload
        raise RuntimeError(f"Failed to decode productRatings JSON: {exc}") from exc

    missing_keys = [key for key in ("ratingAverage", "totalNumberOfRatings", "ratingCounts") if key not in parsed]
    if missing_keys:
        raise RuntimeError(f"Missing expected keys in productRatings block: {', '.join(missing_keys)}")

    rating_counts = parsed["ratingCounts"]
    if not isinstance(rating_counts, list) or len(rating_counts) != 5:
        raise RuntimeError("ratingCounts must be a list of five integers (5★ ➝ 1★)")

    return parsed


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract App Store rating histogram (5★ ➝ 1★) from the publicly available product page HTML."
        )
    )
    parser.add_argument("app_id", help="Numeric App Store app identifier, e.g. 1234567890")
    parser.add_argument(
        "--country",
        default="ua",
        help="Two-letter storefront code (default: %(default)s). Examples: us, ua, gb.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output (indentation + trailing newline).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        summary = fetch_product_ratings(app_id=args.app_id, country=args.country)
    except Exception as exc:  # pragma: no cover - CLI error propagation
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None),
        end="\n" if args.pretty else "",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
