"""Free, keyless headline monitoring using GDELT and official central-bank RSS.

Headlines are context only. These feeds are NOT a complete economic calendar,
and their output is deliberately marked impact=unknown so it cannot authorize
a trade. Attribute GDELT and link back to original publishers.
"""
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from urllib import error, parse, request
from xml.etree import ElementTree

from bigbulls_ai.news import NewsEvent

GDELT_ENDPOINT = "https://api.gdeltproject.org/api/v2/doc/doc"
DEFAULT_QUERY = (
    '("Federal Reserve" OR "central bank" OR forex OR currency OR inflation '
    'OR "interest rate" OR gold OR oil OR "employment report")'
)
DEFAULT_RSS_FEEDS = {
    "Federal Reserve": ("https://www.federalreserve.gov/feeds/press_all.xml", "USD"),
    "European Central Bank": ("https://www.ecb.europa.eu/rss/press.html", "EUR"),
}


def _parse_datetime(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        if len(text) == 16 and "T" in text and text.endswith("Z"):
            return datetime.strptime(text, "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC)
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        try:
            parsed = parsedate_to_datetime(text)
        except (TypeError, ValueError, OverflowError):
            return None
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)


def _event_id(source: str, url: str, title: str) -> str:
    raw = f"{source}|{url}|{title}".encode()
    return hashlib.sha256(raw).hexdigest()[:24]


class GDELTNewsProvider:
    """Free GDELT DOC API client; no key required. Respect the provider's limits."""

    def __init__(self, query: str = DEFAULT_QUERY, max_records: int = 50) -> None:
        if not query.strip():
            raise ValueError("GDELT query cannot be empty")
        if not 1 <= max_records <= 250:
            raise ValueError("max_records must be between 1 and 250")
        self.query = query
        self.max_records = max_records

    def fetch_events(self, since: datetime, until: datetime) -> list[NewsEvent]:
        if since.tzinfo is None or until.tzinfo is None or until < since:
            raise ValueError("since/until must be ordered timezone-aware timestamps")
        params = parse.urlencode({
            "query": self.query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": self.max_records,
            "sort": "datedesc",
            "startdatetime": since.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
            "enddatetime": until.astimezone(UTC).strftime("%Y%m%d%H%M%S"),
        })
        http_request = request.Request(
            f"{GDELT_ENDPOINT}?{params}",
            headers={"Accept": "application/json", "User-Agent": "BIGBULLS-AI/0.1 (GDELT attribution)"},
        )
        try:
            with request.urlopen(http_request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("GDELT request failed") from exc
        if not isinstance(payload, dict):
            raise TypeError("Unexpected GDELT response")
        articles = payload.get("articles", [])
        if not isinstance(articles, list):
            raise TypeError("Unexpected GDELT articles payload")
        events: list[NewsEvent] = []
        for article in articles:
            if not isinstance(article, dict):
                continue
            title = str(article.get("title") or "").strip()
            url = str(article.get("url") or "").strip()
            published = _parse_datetime(article.get("seendate") or article.get("date"))
            if not title or not url or published is None:
                continue
            if not since.astimezone(UTC) <= published <= until.astimezone(UTC):
                continue
            events.append(NewsEvent(
                event_id=_event_id("GDELT", url, title),
                title=title,
                currency="UNKNOWN",
                scheduled_at=published,
                published_at=published,
                impact="unknown",
                source="GDELT Project",
                source_url=url,
            ))
        return events


class OfficialCentralBankRSSProvider:
    """Free public RSS feeds from the Federal Reserve and European Central Bank."""

    def __init__(self, feeds: dict[str, tuple[str, str]] | None = None) -> None:
        self.feeds = dict(DEFAULT_RSS_FEEDS if feeds is None else feeds)

    def fetch_events(self, since: datetime, until: datetime) -> list[NewsEvent]:
        if since.tzinfo is None or until.tzinfo is None or until < since:
            raise ValueError("since/until must be ordered timezone-aware timestamps")
        events: list[NewsEvent] = []
        for source, (feed_url, currency) in self.feeds.items():
            http_request = request.Request(
                feed_url,
                headers={"Accept": "application/rss+xml, application/atom+xml, application/xml"},
            )
            try:
                with request.urlopen(http_request, timeout=20) as response:
                    root = ElementTree.fromstring(response.read())
            except (error.URLError, TimeoutError, ElementTree.ParseError) as exc:
                raise RuntimeError(f"{source} RSS request failed") from exc
            for item in root.iter():
                if item.tag.rsplit("}", 1)[-1] not in {"item", "entry"}:
                    continue
                children = {child.tag.rsplit("}", 1)[-1]: child for child in item}
                title_node = children.get("title")
                link_node = children.get("link")
                date_node = children.get("pubDate") or children.get("published") or children.get("updated")
                if title_node is None or link_node is None:
                    continue
                title = (title_node.text or "").strip()
                link = (link_node.text or link_node.attrib.get("href") or "").strip()
                published = _parse_datetime(date_node.text if date_node is not None else None)
                if not title or not link or published is None:
                    continue
                if not since.astimezone(UTC) <= published <= until.astimezone(UTC):
                    continue
                events.append(NewsEvent(
                    event_id=_event_id(source, link, title),
                    title=title,
                    currency=currency,
                    scheduled_at=published,
                    published_at=published,
                    impact="unknown",
                    source=source,
                    source_url=link,
                ))
        return events


class FreeNewsAggregator:
    """Combine keyless global headlines and official central-bank RSS feeds."""

    def __init__(
        self,
        gdelt: GDELTNewsProvider | None = None,
        rss: OfficialCentralBankRSSProvider | None = None,
    ) -> None:
        self.gdelt = gdelt or GDELTNewsProvider()
        self.rss = rss or OfficialCentralBankRSSProvider()

    def fetch_events(self, since: datetime, until: datetime) -> list[NewsEvent]:
        combined = self.gdelt.fetch_events(since, until) + self.rss.fetch_events(since, until)
        unique = {event.event_id: event for event in combined}
        return sorted(unique.values(), key=lambda event: event.published_at, reverse=True)
