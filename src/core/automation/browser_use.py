"""
Optimized browser automation for restaurant booking.

Key improvements:
- Search via HTTP (SerpAPI / Google Custom Search / DuckDuckGo scrape) — NO browser cost
- Parallel search across multiple query strategies simultaneously
- In-memory + Redis cache so the same restaurant is never searched twice
- Browser-use only fires for the actual booking step
- Semaphore limits concurrent browser sessions to avoid runaway cloud spend
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import BaseModel, Field

# ── Browser-use (only needed at booking time) ─────────────────────────────────
try:
    from browser_use import Agent, Controller
    from browser_use.browser.browser import Browser

    BROWSER_USE_AVAILABLE = True
except ImportError:
    Agent = Controller = Browser = None
    BROWSER_USE_AVAILABLE = False

try:
    from browser_use_sdk.v3 import AsyncBrowserUse

    BROWSER_USE_CLOUD_AVAILABLE = True
except ImportError:
    BROWSER_USE_CLOUD_AVAILABLE = False

# ── Optional Redis cache ───────────────────────────────────────────────────────
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from ..metadata.storage import CallMetadata, metadata_storage

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Data models
# ─────────────────────────────────────────────────────────────────────────────


class RestaurantSearchResult(BaseModel):
    name: str
    url: str
    booking_url: Optional[str] = None
    platform: Optional[str] = None  # OpenTable, Resy, Tock, Direct, …
    rating: Optional[str] = None
    cuisine: Optional[str] = None
    location: Optional[str] = None
    source_query: Optional[str] = None  # which query found this


class BookingResult(BaseModel):
    success: bool
    booking_reference: Optional[str] = None
    confirmation_details: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    steps_completed: List[str] = Field(default_factory=list)
    time_taken_seconds: float = 0.0
    search_results_found: int = 0
    booking_attempts_made: int = 0
    search_time_seconds: float = 0.0  # new: how long search phase took
    search_source: Optional[str] = None  # new: which search backend was used


class RestaurantBookingSite(BaseModel):
    name: str
    url: str
    booking_path: str
    platform: Optional[str] = None
    selectors: Dict[str, str] = Field(default_factory=dict)
    requires_login: bool = False
    login_credentials: Optional[Dict[str, str]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Simple in-process cache (falls back to Redis when available)
# ─────────────────────────────────────────────────────────────────────────────


class SearchCache:
    """
    Two-tier cache:
      L1 — in-process dict (instant, lost on restart)
      L2 — Redis (optional, survives restarts, shared across workers)

    TTL: 6 hours.  Restaurant booking pages don't change that fast.
    """

    TTL = 60 * 60 * 6  # 6 hours in seconds

    def __init__(self):
        self._memory: Dict[str, Tuple[float, List[RestaurantSearchResult]]] = {}
        self._redis: Optional[Any] = None

    async def _get_redis(self):
        if not REDIS_AVAILABLE:
            return None
        if self._redis is None:
            url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                self._redis = await aioredis.from_url(url, decode_responses=True)
                await self._redis.ping()
            except Exception:
                self._redis = None
        return self._redis

    @staticmethod
    def _key(restaurant_name: str, location: str) -> str:
        raw = f"{restaurant_name.lower().strip()}|{location.lower().strip()}"
        return "rsearch:" + hashlib.md5(raw.encode()).hexdigest()

    async def get(
        self, restaurant_name: str, location: str
    ) -> Optional[List[RestaurantSearchResult]]:
        key = self._key(restaurant_name, location)

        # L1
        entry = self._memory.get(key)
        if entry and (time.time() - entry[0]) < self.TTL:
            logger.debug(f"[CACHE L1 HIT] {restaurant_name}")
            return entry[1]

        # L2
        r = await self._get_redis()
        if r:
            try:
                raw = await r.get(key)
                if raw:
                    data = json.loads(raw)
                    results = [RestaurantSearchResult(**d) for d in data]
                    self._memory[key] = (time.time(), results)  # warm L1
                    logger.debug(f"[CACHE L2 HIT] {restaurant_name}")
                    return results
            except Exception as e:
                logger.warning(f"[CACHE] Redis read error: {e}")

        return None

    async def set(
        self, restaurant_name: str, location: str, results: List[RestaurantSearchResult]
    ):
        key = self._key(restaurant_name, location)
        self._memory[key] = (time.time(), results)

        r = await self._get_redis()
        if r:
            try:
                payload = json.dumps([res.dict() for res in results])
                await r.setex(key, self.TTL, payload)
            except Exception as e:
                logger.warning(f"[CACHE] Redis write error: {e}")


search_cache = SearchCache()


# ─────────────────────────────────────────────────────────────────────────────
# HTTP-based search backends  (zero browser cost)
# ─────────────────────────────────────────────────────────────────────────────

BOOKING_PLATFORMS = {
    "opentable.com": "OpenTable",
    "resy.com": "Resy",
    "tock.com": "Tock",
    "exploretock.com": "Tock",
    "sevenrooms.com": "SevenRooms",
    "yelp.com": "Yelp",
    "covermanager.com": "CoverManager",
    "quandoo.com": "Quandoo",
    "bookatable.com": "Bookatable",
    "fork.com": "Fork",
    "zomato.com": "Zomato",
    "thefork.com": "TheFork",
}


def _identify_platform(url: str) -> str:
    url_lower = url.lower()
    for domain, name in BOOKING_PLATFORMS.items():
        if domain in url_lower:
            return name
    return "Direct"


def _is_booking_url(url: str) -> bool:
    keywords = [
        "reserv",
        "booking",
        "book-a-table",
        "reserve",
        "opentable",
        "resy",
        "tock",
        "sevenrooms",
        "quandoo",
        "thefork",
    ]
    url_lower = url.lower()
    return any(k in url_lower for k in keywords)


def _extract_results_from_serp(items: List[Dict]) -> List[RestaurantSearchResult]:
    """Parse raw SERP items into RestaurantSearchResult objects."""
    results = []
    seen_urls = set()

    for item in items:
        url = item.get("link") or item.get("url", "")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        # Skip pure delivery apps
        if any(d in url for d in ["doordash.com", "ubereats.com", "grubhub.com"]):
            continue

        platform = _identify_platform(url)
        booking_url = url if _is_booking_url(url) else None

        results.append(
            RestaurantSearchResult(
                name=item.get("title", "Unknown"),
                url=url,
                booking_url=booking_url,
                platform=platform,
                rating=str(item.get("rating", "")) if item.get("rating") else None,
                cuisine=item.get("cuisine"),
                location=item.get("address"),
            )
        )

    return results


async def _search_serper(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """Serper.dev - Google search API. Set SERPER_API_KEY to use."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        return []

    try:
        # Serper.dev uses POST request with JSON body
        payload = {"q": query}
        headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

        resp = await client.post(
            "https://google.serper.dev/search",
            json=payload,
            headers=headers,
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        # Serper.dev returns different structure - adapt it
        items = []
        if "organic" in data:
            items = data["organic"]
        elif "results" in data:
            items = data["results"]

        logger.debug(f"[SERPER] {len(items)} results for: {query}")
        return _extract_results_from_serp(items)
    except Exception as e:
        logger.warning(f"[SERPER] Failed: {e}")
        return []


async def _search_serpapi(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """SerpAPI — paid but very reliable.  Set SERPAPI_KEY to use."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    try:
        resp = await client.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": api_key, "num": 10, "engine": "google"},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()
        items = data.get("organic_results", [])
        logger.debug(f"[SERPAPI] {len(items)} results for: {query}")
        return _extract_results_from_serp(items)
    except Exception as e:
        logger.warning(f"[SERPAPI] Failed: {e}")
        return []


async def _search_google_cse(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """Google Custom Search JSON API — 100 free queries/day."""
    cx = os.getenv("GOOGLE_CSE_ID")
    key = os.getenv("GOOGLE_API_KEY")
    if not cx or not key:
        return []

    try:
        resp = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"q": query, "cx": cx, "key": key, "num": 10},
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        logger.debug(f"[GOOGLE CSE] {len(items)} results for: {query}")
        return _extract_results_from_serp(items)
    except Exception as e:
        logger.warning(f"[GOOGLE CSE] Failed: {e}")
        return []


async def _search_bing(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """
    Bing Web Search API - free tier available through Azure.
    Set BING_API_KEY to use.
    """
    api_key = os.getenv("BING_API_KEY")
    if not api_key:
        return []

    try:
        resp = await client.get(
            "https://api.bing.microsoft.com/v7.0/search",
            params={"q": query, "count": 10},
            headers={"Ocp-Apim-Subscription-Key": api_key},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        items = []
        for item in data.get("webPages", {}).get("value", []):
            items.append({"link": item.get("url", ""), "title": item.get("name", "")})
        results = _extract_results_from_serp(items)
        logger.debug(f"[BING] {len(results)} results for: {query}")
        return results
    except Exception as e:
        logger.warning(f"[BING] Failed: {e}")
        return []


async def _search_duckduckgo(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """DuckDuckGo - placeholder for future implementation"""
    # DuckDuckGo API is currently blocked/redirected in Docker
    # For now, just return empty and rely on paid APIs
    logger.debug(
        f"[DUCKDUCKGO] Skipped - use SERPER_API_KEY or BING_API_KEY for search"
    )
    return []

    try:
        resp = await client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={"q": query, "cx": cx, "key": key, "num": 10},
            timeout=8,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        logger.debug(f"[GOOGLE CSE] {len(items)} results for: {query}")
        return _extract_results_from_serp(items)
    except Exception as e:
        logger.warning(f"[GOOGLE CSE] Failed: {e}")
        return []


async def _search_duckduckgo(
    query: str, client: httpx.AsyncClient
) -> List[RestaurantSearchResult]:
    """
    DuckDuckGo search using the JSON API - free and reliable.
    Falls back to basic web scraping if API returns redirect.
    """
    try:
        # Use DuckDuckGo instant answer API
        resp = await client.get(
            "https://api.duckduckgo.com/",
            params={
                "q": query,
                "format": "json",
                "no_html": 1,
                "skip_disambig": 1,
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            },
            timeout=15,
            follow_redirects=False,  # Don't follow redirects - 202 means we got redirected
        )

        if resp.status_code == 200 and "application/json" in resp.headers.get(
            "content-type", ""
        ):
            data = resp.json()
            items = []

            for topic in data.get("RelatedTopics", []):
                if isinstance(topic, dict) and "FirstURL" in topic:
                    url = topic.get("FirstURL", "")
                    if any(
                        x in url.lower()
                        for x in [
                            "restaurant",
                            "reservation",
                            "booking",
                            "menu",
                            "yelp",
                            "opentable",
                            "resy",
                            "tock",
                            "table",
                        ]
                    ):
                        items.append({"link": url, "title": topic.get("Text", "")})

            if items:
                results = _extract_results_from_serp(items[:10])
                logger.debug(f"[DUCKDUCKGO API] {len(results)} results for: {query}")
                return results

        # Fallback: try basic web scraping with different approach
        logger.debug(
            f"[DUCKDUCKGO] API returned {resp.status_code}, trying scrape fallback"
        )

        # Try using textise dot iitty version
        try:
            resp = await client.get(
                "https://www.textise dot iitty.com/showcloud.aspx",
                params={"url": f"https://duckduckgo.com/?q={query}"},
                timeout=10,
            )
        except Exception:
            pass

        # Return empty - no working free search available
        logger.debug(f"[DUCKDUCKGO] No results for: {query}")
        return []
    except Exception as e:
        logger.warning(f"[DUCKDUCKGO API] Failed: {e}")
        return []

        data = resp.json()
        items = []

        # Get related topics that are URLs
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and "FirstURL" in topic:
                url = topic.get("FirstURL", "")
                # Filter out non-relevant results
                if any(
                    x in url.lower()
                    for x in [
                        "restaurant",
                        "reservation",
                        "booking",
                        "menu",
                        "yelp",
                        "opentable",
                        "resy",
                        "tock",
                        "table",
                    ]
                ):
                    items.append({"link": url, "title": topic.get("Text", "")})

        if items:
            results = _extract_results_from_serp(items[:10])
            logger.debug(f"[DUCKDUCKGO API] {len(results)} results for: {query}")
            return results

        # Fallback: no results from API
        logger.debug(f"[DUCKDUCKGO API] No results for: {query}")
        return []
    except Exception as e:
        logger.warning(f"[DUCKDUCKGO API] Failed: {e}")
        return []

        data = resp.json()
        items = []

        # Get related topics that are URLs
        for topic in data.get("RelatedTopics", []):
            if "FirstURL" in topic:
                url = topic.get("FirstURL", "")
                # Filter out non-relevant results
                if any(
                    x in url.lower()
                    for x in [
                        "restaurant",
                        "reservation",
                        "booking",
                        "menu",
                        "yelp",
                        "opentable",
                        "resy",
                    ]
                ):
                    items.append({"link": url, "title": topic.get("Text", "")})

        if items:
            results = _extract_results_from_serp(items[:10])
            logger.debug(f"[DUCKDUCKGO API] {len(results)} results for: {query}")
            return results

        # Fallback: no results from API
        logger.debug(f"[DUCKDUCKGO API] No results for: {query}")
        return []
    except Exception as e:
        logger.warning(f"[DUCKDUCKGO API] Failed: {e}")
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Parallel search orchestrator
# ─────────────────────────────────────────────────────────────────────────────


class RestaurantSearcher:
    """
    Runs multiple search queries in parallel across whichever search backends
    are configured, deduplicates results, and returns them ranked by how
    booking-friendly the URL looks.

    Cost: $0 for DuckDuckGo / Google CSE free tier.
          ~$0.001 per query for SerpAPI.
    Browser: never opened here.
    """

    def __init__(self):
        self._http = httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; RestoBot/1.0)"},
            follow_redirects=True,
        )

    async def close(self):
        await self._http.aclose()

    def _build_queries(self, restaurant_name: str, location: str) -> List[str]:
        """
        Multiple query strategies run in parallel — increases recall without
        extra latency because they fire concurrently.
        """
        base = f"{restaurant_name} {location}".strip()
        return [
            f"{base} restaurant reservation booking",
            f"{base} restaurant OpenTable OR Resy OR Tock",
            f"{base} restaurant official website",
        ]

    async def _run_single_query(self, query: str) -> List[RestaurantSearchResult]:
        """Run one query across all available backends and return merged results."""
        tasks = [
            _search_serper(query, self._http),  # Use Serper.dev first
            _search_google_cse(query, self._http),
            _search_bing(query, self._http),
            _search_duckduckgo(query, self._http),
        ]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        merged: List[RestaurantSearchResult] = []
        seen_urls: set = set()
        for batch in batches:
            if isinstance(batch, Exception):
                continue
            for r in batch:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    r.source_query = query
                    merged.append(r)
        return merged

    @staticmethod
    def _rank(results: List[RestaurantSearchResult]) -> List[RestaurantSearchResult]:
        """
        Score and sort results so browser-use tries the most promising URLs first.
        Higher score = try earlier.
        """

        def score(r: RestaurantSearchResult) -> int:
            s = 0
            if r.platform and r.platform != "Direct":
                s += 10  # Known booking platform is gold
            if r.booking_url:
                s += 5
            if r.rating:
                s += 2
            # Penalise pure aggregators that don't allow booking
            if any(
                d in r.url for d in ["yelp.com", "tripadvisor.com", "google.com/maps"]
            ):
                s -= 3
            return s

        return sorted(results, key=score, reverse=True)

    async def search(
        self, restaurant_name: str, location: str = ""
    ) -> List[RestaurantSearchResult]:
        """
        Full parallel search with cache.
        Typical latency: 300 – 800 ms (IO-bound, all queries fire at once).
        """
        # Check cache first
        cached = await search_cache.get(restaurant_name, location)
        if cached:
            logger.info(
                f"[SEARCH] Cache hit for '{restaurant_name}' — skipping HTTP calls"
            )
            return cached

        t0 = time.time()
        queries = self._build_queries(restaurant_name, location)
        logger.info(
            f"[SEARCH] Running {len(queries)} queries in parallel for '{restaurant_name}'"
        )

        # All queries across all backends — fully parallel
        query_tasks = [self._run_single_query(q) for q in queries]
        all_batches = await asyncio.gather(*query_tasks, return_exceptions=True)

        merged: List[RestaurantSearchResult] = []
        seen_urls: set = set()
        for batch in all_batches:
            if isinstance(batch, Exception):
                logger.warning(f"[SEARCH] Query batch failed: {batch}")
                continue
            for r in batch:
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    merged.append(r)

        ranked = self._rank(merged)
        elapsed = time.time() - t0
        logger.info(f"[SEARCH] Found {len(ranked)} unique results in {elapsed:.2f}s")

        await search_cache.set(restaurant_name, location, ranked)
        return ranked


# ─────────────────────────────────────────────────────────────────────────────
# Browser automation  (only used for the actual booking step)
# ─────────────────────────────────────────────────────────────────────────────

# Hard cap: never open more than N cloud browser sessions at once
_BROWSER_SEMAPHORE = asyncio.Semaphore(int(os.getenv("MAX_BROWSER_SESSIONS", "2")))


class BrowserBooker:
    """
    Thin wrapper around browser-use that only handles the booking step.
    The search step is handled by RestaurantSearcher (no browser needed).
    """

    def __init__(self):
        self.use_cloud = os.getenv("BROWSER_USE_CLOUD", "false").lower() == "true"
        self._browser: Optional[Any] = None
        self._controller: Optional[Any] = None
        self._cloud_client: Optional[Any] = None
        self._initialized = False

    async def _ensure_initialized(self):
        if self._initialized:
            return

        if self.use_cloud and BROWSER_USE_CLOUD_AVAILABLE:
            api_key = os.getenv("BROWSER_USE_API_KEY")
            if not api_key:
                raise ValueError("BROWSER_USE_API_KEY is required for cloud mode")
            self._cloud_client = AsyncBrowserUse(api_key=api_key)
            logger.info("[BOOKER] Browser Use Cloud ready")

        elif BROWSER_USE_AVAILABLE:
            cdp_url = os.getenv("BROWSER_USE_CDP_URL")
            self._browser = Browser(cdp_url=cdp_url) if cdp_url else Browser()
            self._controller = Controller()
            logger.info("[BOOKER] Local browser ready")

        else:
            raise RuntimeError(
                "No browser automation library found. pip install browser-use"
            )

        self._initialized = True

    async def cleanup(self):
        if self._cloud_client:
            await self._cloud_client.close()
        if self._browser:
            await self._browser.close()
        self._initialized = False

    async def check_availability(
        self, candidate: RestaurantSearchResult, date: str, time: str, party_size: int
    ) -> Dict[str, Any]:
        """Check availability at a single restaurant using browser-use"""

        await self._ensure_initialized()

        if self.use_cloud and self._cloud_client:
            instruction = f"""
GOAL: Check table availability at {candidate.name}

RESTAURANT: {candidate.name}
PLATFORM: {candidate.platform}
URL: {candidate.url}

CHECK AVAILABILITY FOR:
- Date: {date}
- Time: {time}
- Party size: {party_size}

STEPS:
1. Navigate to {candidate.url}
2. Find the reservation/booking page
3. Check availability for the requested date/time
4. If not available, find the closest available times (±2 hours)
5. Document what times ARE available

RULES:
- Do NOT book anything - just check availability
- Look for time slots around the requested time
- Note any special requirements or restrictions

EXPECTED OUTPUT:
- Is requested time available? (yes/no)
- List of 3-5 alternative times if not available
- Any booking notes or requirements
"""

            cloud_result = await self._cloud_client.run(
                instruction,
                proxy_country_code="us",
                max_cost_usd=0.20,
                keep_alive=False,
            )

            if cloud_result.status == "stopped":
                return self._parse_availability_response(str(cloud_result.output), time)

        elif self._browser and self._controller:
            instruction = f"""
Check availability at {candidate.name} for {date} at {time} for {party_size} people.
Find the booking page and check if that time is available.
If not, find the closest available times.
"""

            llm = self._get_llm()
            agent = Agent(
                task=instruction,
                llm=llm,
                browser=self._browser,
                controller=self._controller,
            )

            agent_result = await agent.run()

            if agent_result:
                return self._parse_availability_response(str(agent_result), time)

        return {
            "requested_time_available": False,
            "alternative_times": [],
            "notes": "Could not check availability",
        }

    def _get_llm(self):
        try:
            from browser_use.llm.openai import OpenAIChat

            return OpenAIChat(
                model="llama-3.1-8b-instant",
                api_key=os.getenv("GROQ_API_KEY"),
                base_url="https://api.groq.com/openai/v1",
            )
        except Exception:
            return getattr(self._controller, "llm", None)

    @staticmethod
    def _extract_ref(text: str) -> Optional[str]:
        patterns = [
            r"confirmation[_\s]*(?:reference|number|id|#)?[:\s]+([A-Z0-9\-]{4,20})",
            r"reference[:\s]+([A-Z0-9\-]{4,20})",
            r"booking[:\s]+([A-Z0-9\-]{4,20})",
            r"#([A-Z0-9]{6,})",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1)
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Top-level orchestrator
# ─────────────────────────────────────────────────────────────────────────────


class BrowserAutomation:
    """
    Replaces the original BrowserAutomation class with the optimised pipeline:

      1. search_restaurants()  →  pure HTTP, parallel, cached  (fast + free)
      2. process_booking()     →  browser-use only for booking  (expensive but necessary)
    """

    def __init__(self):
        self.searcher = RestaurantSearcher()
        self.booker = BrowserBooker()

    async def initialize(self):
        # Searcher needs no init; booker lazily initialises on first use.
        pass

    async def cleanup(self):
        await self.searcher.close()
        await self.booker.cleanup()

    async def search_restaurants(
        self,
        restaurant_name: str,
        location: str = "",
    ) -> List[RestaurantSearchResult]:
        """Pure HTTP search — no browser opened."""
        return await self.searcher.search(restaurant_name, location)

    async def check_availability(
        self,
        restaurant_name: str,
        location: str,
        requested_date: str,
        requested_time: str,
        party_size: int,
    ) -> Dict[str, Any]:
        """
        Check availability at restaurants and return options
        Returns: {
            "available": bool,
            "requested_time_available": bool,
            "alternatives": [{"time": "19:00", "restaurant": "Name"}],
            "best_option": {"time": "19:00", "restaurant": "Name"},
            "message": "Response for Vapi"
        }
        """
        logger.info(
            f"[AVAILABILITY] Checking {restaurant_name} {location} for {requested_date} at {requested_time} for {party_size}"
        )

        # Search for restaurants
        candidates = await self.searcher.search(restaurant_name, location)

        if not candidates:
            return {
                "available": False,
                "requested_time_available": False,
                "alternatives": [],
                "best_option": None,
                "message": f"I couldn't find any restaurants for {restaurant_name} in {location}",
            }

        availability_results = []

        # Check availability at each restaurant using browser-use
        for candidate in candidates[:3]:  # Check top 3
            try:
                availability = await self.booker.check_availability(
                    candidate, requested_date, requested_time, party_size
                )
                availability_results.append(
                    {
                        "restaurant": candidate.name,
                        "platform": candidate.platform,
                        "url": candidate.url,
                        **availability,
                    }
                )
            except Exception as e:
                logger.warning(f"[AVAILABILITY] Failed to check {candidate.name}: {e}")
                continue

        # Analyze results
        requested_time_available = any(
            r["requested_time_available"] for r in availability_results
        )

        # Find alternatives
        alternatives = []
        for result in availability_results:
            for alt_time in result.get("alternative_times", []):
                alternatives.append(
                    {
                        "time": alt_time,
                        "restaurant": result["restaurant"],
                        "platform": result["platform"],
                    }
                )

        # Sort alternatives by time
        alternatives.sort(key=lambda x: x["time"])

        # Create message for Vapi
        if requested_time_available:
            available_restaurants = [
                r["restaurant"]
                for r in availability_results
                if r["requested_time_available"]
            ]
            message = f"Yes! {requested_date} at {requested_time} is available at {', '.join(available_restaurants)}. Would you like me to book one of these?"
        else:
            if alternatives:
                # Group alternatives by time
                time_groups = {}
                for alt in alternatives[:5]:  # Show top 5
                    time_groups.setdefault(alt["time"], []).append(alt["restaurant"])

                alt_message_parts = []
                for time, restaurants in list(time_groups.items())[
                    :3
                ]:  # Show top 3 times
                    if len(restaurants) <= 2:
                        alt_message_parts.append(f"{time} at {', '.join(restaurants)}")
                    else:
                        alt_message_parts.append(f"{time} at several restaurants")

                message = f"{requested_date} at {requested_time} is not available. But I found these options: {', '.join(alt_message_parts)}. Which would you prefer?"
            else:
                message = f"I'm sorry, {requested_date} at {requested_time} is not available at any restaurants. Would you like to try a different date or time?"

        return {
            "available": len(availability_results) > 0,
            "requested_time_available": requested_time_available,
            "alternatives": alternatives,
            "best_option": alternatives[0] if alternatives else None,
            "message": message,
            "search_results": availability_results,
        }

    async def _check_single_restaurant_availability(
        self, candidate: RestaurantSearchResult, date: str, time: str, party_size: int
    ) -> Dict[str, Any]:
        """Check availability at a single restaurant using browser-use"""

        if self.use_cloud and BROWSER_USE_CLOUD_AVAILABLE:
            # Use cloud SDK
            instruction = f"""
GOAL: Check table availability at {candidate.name}

RESTAURANT: {candidate.name}
PLATFORM: {candidate.platform}
URL: {candidate.url}

CHECK AVAILABILITY FOR:
- Date: {date}
- Time: {time}
- Party size: {party_size}

STEPS:
1. Navigate to {candidate.url}
2. Find the reservation/booking page
3. Check availability for the requested date/time
4. If not available, find the closest available times (±2 hours)
5. Document what times ARE available

RULES:
- Do NOT book anything - just check availability
- Look for time slots around the requested time
- Note any special requirements or restrictions

EXPECTED OUTPUT:
- Is requested time available? (yes/no)
- List of 3-5 alternative times if not available
- Any booking notes or requirements
"""

            cloud_result = await self.cloud_client.run(
                instruction,
                proxy_country_code="us",
                max_cost_usd=0.20,
                keep_alive=False,
            )

            if cloud_result.status == "stopped":
                return self._parse_availability_response(cloud_result.output, time)

        elif BROWSER_USE_AVAILABLE:
            # Use local browser
            instruction = f"""
Check availability at {candidate.name} for {date} at {time} for {party_size} people.
Find the booking page and check if that time is available.
If not, find the closest available times.
"""

            llm = self._get_llm()
            agent = Agent(
                task=instruction,
                llm=llm,
                browser=self.browser,
                controller=self.controller,
            )

            agent_result = await agent.run()

            if agent_result:
                return self._parse_availability_response(str(agent_result), time)

        # Fallback
        return {
            "requested_time_available": False,
            "alternative_times": [],
            "notes": "Could not check availability",
        }

    def _parse_availability_response(
        self, response: str, requested_time: str
    ) -> Dict[str, Any]:
        """Parse the availability check response"""

        # Simple parsing - in production, you'd use more sophisticated NLP
        response_lower = response.lower()

        # Check if requested time is available
        requested_available = any(
            phrase in response_lower
            for phrase in [
                f"{requested_time} is available",
                f"{requested_time} available",
                "time is available",
                "available at that time",
                "can book that time",
            ]
        )

        # Extract alternative times (simple regex)
        import re

        time_patterns = [
            r"(\d{1,2}:\d{2}\s*(?:am|pm)?)",
            r"(\d{1,2}\s*(?:am|pm)?)",
        ]

        alternative_times = []
        for pattern in time_patterns:
            matches = re.findall(pattern, response_lower)
            alternative_times.extend(matches)

        # Clean up and deduplicate
        alternative_times = list(
            set(
                [
                    t.strip()
                    for t in alternative_times
                    if t.strip() and t.strip() != requested_time.lower()
                ]
            )
        )[:5]  # Keep only first 5

        return {
            "requested_time_available": requested_available,
            "alternative_times": alternative_times,
            "notes": response[:200] + "..." if len(response) > 200 else response,
        }

    async def process_booking(self, call_metadata: CallMetadata) -> BookingResult:
        t0 = datetime.utcnow()
        final = BookingResult(success=False)

        booking = call_metadata.booking_request
        name = booking.get("restaurant_name", "")
        location = booking.get("location", "")

        # ── Phase 1: search (HTTP only, parallel, cached) ────────────────────
        search_t0 = time.time()
        candidates = await self.searcher.search(name, location)
        final.search_time_seconds = round(time.time() - search_t0, 2)
        final.search_results_found = len(candidates)

        if not candidates:
            final.error_message = f"No results found for '{name}' in '{location}'"
            return final

        logger.info(
            f"[PIPELINE] {len(candidates)} candidates found in "
            f"{final.search_time_seconds}s — starting booking attempts"
        )

        # ── Phase 2: booking (browser-use, sequential through ranked list) ───
        for i, candidate in enumerate(candidates[:5]):  # cap at top-5
            logger.info(
                f"[PIPELINE] Attempt {i + 1}/{min(len(candidates), 5)}: "
                f"{candidate.name} ({candidate.platform})"
            )
            final.booking_attempts_made += 1

            result = await self.booker.book(candidate, booking)

            if result.success:
                final.success = True
                final.booking_reference = result.booking_reference
                final.confirmation_details = result.confirmation_details
                final.steps_completed = result.steps_completed
                final.search_source = candidate.platform
                logger.info(f"[PIPELINE] Booked! ref={result.booking_reference}")
                break
            else:
                final.steps_completed.append(
                    f"Failed at {candidate.name}: {result.error_message}"
                )

        if not final.success:
            final.error_message = (
                f"Booking failed after {final.booking_attempts_made} attempts. "
                "Consider calling the restaurant directly."
            )

        final.time_taken_seconds = (datetime.utcnow() - t0).total_seconds()
        return final


# ─────────────────────────────────────────────────────────────────────────────
# Processing loop (unchanged interface, improved internals)
# ─────────────────────────────────────────────────────────────────────────────


class BookingProcessor:
    def __init__(self):
        self.automation = BrowserAutomation()
        # Only 1 concurrent browser session by default (override with MAX_BROWSER_SESSIONS)
        self._sem = asyncio.Semaphore(int(os.getenv("MAX_BROWSER_SESSIONS", "2")))

    async def start_processing_loop(self):
        logger.info("Booking processing loop started")
        while True:
            try:
                pending = await metadata_storage.get_pending_calls(limit=10)
                if not pending:
                    await asyncio.sleep(5)
                    continue
                await asyncio.gather(
                    *[self._process(call) for call in pending],
                    return_exceptions=True,
                )
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"[LOOP] Unexpected error: {e}")
                await asyncio.sleep(5)

    async def _process(self, call_metadata: CallMetadata):
        async with self._sem:
            try:
                await metadata_storage.move_to_processing(call_metadata.call_id)
                result = await self.automation.process_booking(call_metadata)
                if result.success:
                    await metadata_storage.move_to_completed(
                        call_metadata.call_id, result.dict()
                    )
                    logger.info(f"[LOOP] ✓ {call_metadata.call_id}")
                else:
                    await metadata_storage.move_to_failed(
                        call_metadata.call_id,
                        result.error_message or "unknown",
                    )
                    logger.error(
                        f"[LOOP] ✗ {call_metadata.call_id}: {result.error_message}"
                    )
            except Exception as e:
                logger.error(f"[LOOP] Exception for {call_metadata.call_id}: {e}")
                await metadata_storage.move_to_failed(call_metadata.call_id, str(e))

    async def cleanup(self):
        await self.automation.cleanup()


# singleton
_processor: Optional[BookingProcessor] = None


def get_booking_processor() -> BookingProcessor:
    global _processor
    if _processor is None:
        _processor = BookingProcessor()
    return _processor
