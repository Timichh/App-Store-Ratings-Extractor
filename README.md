# App-Store-Ratings-Extractor
A simple Python script for obtaining the distribution of app ratings in the App Store (5★ → 1★), the average rating, and the total number of ratings per country — without API and without authorisation.

Usage: python extract_rating_histogram_from_html.py {app-id} --country {ISO-2} --pretty

Example: python extract_rating_histogram_from_html.py 544007664 --country ua --pretty

Result: { "ratingAverage": 4.7, "totalNumberOfRatings": 1377603, "ratingCounts": [ 1166268, 111184, 40179, 17331, 42641 ] }

Arguments: app_id Numeric App Store app identifier (e.g. 544007664) --country Two-letter country code (default: ua). Examples: us, gb, de. --pretty Pretty-print JSON output with indentation