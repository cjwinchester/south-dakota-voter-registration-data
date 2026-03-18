"""
Scraper for SD Secretary of State – Registered Voters by County PDF links.
- Written mostly by Claude Sonnet 4.6

URL: https://sdsos.gov/elections-voting/upcoming-elections/voter-registration-totals/voter-registration-by-county.aspx

Returns a list of dicts, one per report link found in the section, in page order:

    [
        {
            "url":      "https://sdsos.gov/…/StatewideVotersByCounty_3.2.2026.pdf",
            "date":     "2026-03-02",   # ISO-8601, or None if unparseable
            "filename": "StatewideVotersByCounty_3.2.2026.pdf",
        },
        …
    ]

Robustness notes
----------------
* Uses only stdlib + requests + beautifulsoup4 (no Selenium / JS engine needed;
  the page renders all content server-side).
* Scopes collection to anchors that follow the "Registered Voters by County"
  heading, stopping at the next same-or-higher-level heading, so site nav links
  are never captured.  Falls back to a URL-pattern scan if the heading moves.
* Extracts dates from link text via a month-name regex – avoids misreading
  SDCL legal citation numbers (e.g. "12-5-1.5") as dates.
* `date` is None (not an error) for the handful of links whose text is a legal
  notice rather than a plain date (e.g. the SDCL 12-5-1.5 entry).
* URL-encodes spaces that appear in a few older filenames.
* `filename` is always the basename of the resolved URL, so it reflects the
  actual file on disk regardless of how the link text is worded.
* Raises informative exceptions on HTTP failure or a completely empty result.
"""

import re
import logging
from datetime import datetime
from urllib.parse import urljoin, unquote, urlparse
from posixpath import basename
from pathlib import Path
import os

import requests
from bs4 import BeautifulSoup, Tag
from slack_sdk.webhook import WebhookClient

# ── constants ────────────────────────────────────────────────────────────────

PAGE_URL = (
    "https://sdsos.gov/elections-voting/upcoming-elections/"
    "voter-registration-totals/voter-registration-by-county.aspx"
)
BASE_URL = "https://sdsos.gov"
SKIP = [
    "2018-11-14", # notice of party losing status
]

# Matches "Month D(D), YYYY" anywhere in a string.
# Anchoring on the month name intentionally ignores bare numeric strings so
# SDCL citations like "12-5-1.5" are never mistaken for a date.
_DATE_RE = re.compile(
    r"\b(January|February|March|April|May|June|July|August|September|"
    r"October|November|December)\s+(\d{1,2}),\s+(\d{4})\b",
    re.IGNORECASE,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def _get_parsed_report_dates() -> list[str]:
    return [x.stem for x in Path('data').glob('*.csv')]


def _parse_date(text: str) -> str | None:
    """
    Return the first ISO-8601 date found in *text*, or None.

    Only recognises "Month DD, YYYY" form.  The deliberate narrowness prevents
    numeric citation strings from being parsed as dates.
    """
    m = _DATE_RE.search(text)
    if not m:
        return None
    try:
        dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}", "%B %d %Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def _resolve_url(href: str) -> str:
    """
    Produce a fully-qualified, space-free URL from a raw href attribute value.
    Handles both absolute and root-relative paths.
    """
    return urljoin(BASE_URL, href.replace(" ", "%20"))


def _filename_from_url(url: str) -> str:
    """
    Extract the bare filename (e.g. 'StatewideVotersByCounty_3.2.2026.pdf')
    from a fully-qualified URL, decoding any percent-encoding.
    """
    path = urlparse(url).path          # '/elections-voting/…/Report%20Name.pdf'
    return unquote(basename(path))     # 'Report Name.pdf'


def _find_section_links(soup: BeautifulSoup) -> list[Tag]:
    """
    Return every <a href="….pdf"> inside the <section class="centerer"> element,
    which is the content container for the "Registered Voters by County" section.

    Falls back to a URL-pattern scan across the whole document if that element
    cannot be found, so the function degrades gracefully if the site restructures
    its markup.
    """
    container = soup.find("section", class_="centerer")

    if container is None:
        logging.warning(
            "section.centerer not found – falling back to global URL-pattern scan."
        )
        return soup.find_all(
            "a",
            href=re.compile(r"StatewideVotersBy?County", re.IGNORECASE),
        )

    return container.find_all(
        "a", href=lambda h: h and h.lower().endswith(".pdf")
    )


# ── public API ───────────────────────────────────────────────────────────────

def get_voter_registration_pdfs(
    *,
    url: str = PAGE_URL,
    timeout: int = 30,
    headers: dict | None = None,
) -> list[dict]:
    """
    Scrape the SD SOS "Registered Voters by County" page and return every
    PDF link in the section as a list of dicts, in page order (newest first).

    Parameters
    ----------
    url : str
        Page URL.  Override for testing or if the site ever changes its path.
    timeout : int
        HTTP request timeout in seconds.
    headers : dict | None
        Optional additional HTTP headers to merge into the request (e.g. a
        custom User-Agent for your organisation).

    Returns
    -------
    list[dict]
        Each dict has exactly three keys:

        ``url``  (str)
            Fully-qualified, percent-encoded PDF URL.

        ``date``  (str | None)
            ISO-8601 date parsed from the link text, e.g. ``"2026-03-02"``.
            ``None`` for the handful of links whose text is a legal notice
            rather than a plain date (e.g. the SDCL 12-5-1.5 entry).

        ``filename``  (str)
            Bare filename extracted from the URL, e.g.
            ``"StatewideVotersByCounty_3.2.2026.pdf"``.  Always reflects the
            actual file on disk regardless of how the link text is worded.

    Raises
    ------
    requests.HTTPError
        If the server returns a non-2xx status code.
    ValueError
        If no PDF links are found at all (likely a page-structure change).
    """

    _headers = {
        "User-Agent": (
            "Mozilla/5.0 (compatible; SDScraper/2.0; "
            "+https://github.com/example/sd-voter-data)"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if headers:
        _headers.update(headers)

    resp = requests.get(url, headers=_headers, timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    tags = _find_section_links(soup)

    if not tags:
        raise ValueError(
            "No PDF links found under the 'Registered Voters by County' section. "
            "The page structure may have changed – inspect the live HTML."
        )

    results: list[dict] = []
    for tag in tags:
        link_text = tag.get_text(strip=True)
        full_url  = _resolve_url(tag["href"])
        date = _parse_date(link_text)

        if date in SKIP:
            continue

        results.append(
            {
                "url": full_url,
                "date": date,
                "filename": _filename_from_url(full_url),
            }
        )

    return results


def get_new_reports() -> list[dict]:
    dates_already_parsed = _get_parsed_report_dates()
    live_reports = get_voter_registration_pdfs()
    live_dates = [x.get("date") for x in live_reports]

    new_dates = set(live_dates).difference(set(dates_already_parsed))
    return [x for x in live_reports if x.get("date") in new_dates]



# ── CLI convenience ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    new_reports = get_new_reports()

    if not new_reports:
        print("No new reports ...")
    else:
        WEBHOOK = WebhookClient(
            os.environ.get('SLACK_HOOK_STATE_ELECTIONS')
        )

        response = WEBHOOK.send(
            text=f'''
                New voter registration reports ({len(new_reports)}): {" | ".join([x.get("url") for x in new_reports])}''',
            blocks=[
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "New S.D. voter registration data"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": '\n'.join(
                            [f'- <{x.get("url")}|{x.get("date")}>' for x in new_reports]
                        )
                    }
                }
            ]
        )