import argparse
import json
import random
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass
from html import unescape
from typing import Iterable
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag


BASE_DOMAIN = "https://www.amazon.es"
DEFAULT_BASE_URL = (
    "https://www.amazon.es/s?k=smart+phones&i=electronics&rh=n%3A599370031%2C"
    "p_123%3A110955%257C338933%257C370584%257C46655%2Cp_n_condition-type%3A15144009031%2C"
    "p_n_g-1003469290111%3A33554297031%2Cp_6%3AA1AT7YVPFBWXBL%257CA2EL6K6KDM9FO1&dc&"
    "language=en&crid=1EWSHUM5LF9U5&rnid=831275031&sprefix=smart+phones%2Celectronics%2C340&"
    "xpid=FS6kjNux89TFu"
)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
]
PRICE_RE = re.compile(r"[\u20ac$\u00a3]\s?\d[\d.,]*")
STORAGE_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:GB|TB)\b", re.IGNORECASE)


@dataclass
class SearchCard:
    asin: str
    title: str
    url: str


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", unescape(value)).strip()


def extract_meta_refresh_url(html: str, current_url: str) -> str | None:
    match = re.search(r'http-equiv="refresh"\s+content="\d+;\s*URL=\'([^\']+)\'"', html, flags=re.IGNORECASE)
    if not match:
        return None
    return urljoin(BASE_DOMAIN, unescape(match.group(1)))


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    )
    return session


def polite_sleep(min_seconds: float = 1.0, max_seconds: float = 2.0) -> None:
    time.sleep(random.uniform(min_seconds, max_seconds))


def fetch_html(session: requests.Session, url: str, timeout: int = 45) -> str:
    current_url = url
    for _ in range(3):
        response = session.get(current_url, timeout=timeout)
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        html = response.text
        refresh_url = extract_meta_refresh_url(html, current_url)
        if not refresh_url:
            return html
        current_url = refresh_url
    return html


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def normalize_url(url: str) -> str:
    absolute = urljoin(BASE_DOMAIN, url)
    parsed = urlparse(absolute)
    return urlunparse(parsed._replace(fragment=""))


def canonical_dp_url(url: str, asin: str | None = None) -> str:
    if asin:
        return f"{BASE_DOMAIN}/dp/{asin}"
    if not url or url.startswith("javascript:"):
        return ""
    normalized = normalize_url(url)
    match = re.search(r"/dp/([A-Z0-9]{10})", normalized)
    if match:
        return f"{BASE_DOMAIN}/dp/{match.group(1)}"
    return normalized


def is_sponsored_card(card: Tag) -> bool:
    badge_text = clean_text(card.get_text(" ", strip=True)).lower()
    if "sponsored" in badge_text:
        return True
    return card.select_one('[aria-label*="Sponsored"], [data-component-type="sp-sponsored-result"]') is not None


def extract_search_cards(soup: BeautifulSoup) -> list[SearchCard]:
    cards: list[SearchCard] = []
    seen_asins: set[str] = set()

    for card in soup.select('div[data-component-type="s-search-result"][data-asin]'):
        asin = clean_text(card.get("data-asin"))
        if not asin or asin in seen_asins or is_sponsored_card(card):
            continue

        title_heading = card.select_one("a.a-link-normal h2")
        anchor = title_heading.find_parent("a") if title_heading else card.select_one("a.a-link-normal[href]")
        title = clean_text(title_heading.get_text(" ", strip=True) if title_heading else "")
        href = anchor.get("href") if anchor else None
        if not title or not href:
            continue

        seen_asins.add(asin)
        cards.append(SearchCard(asin=asin, title=title, url=canonical_dp_url(href, asin)))

    return cards


def is_valid_search_page(soup: BeautifulSoup) -> bool:
    if soup.select('div[data-component-type="s-search-result"][data-asin]'):
        return True
    text = clean_text(soup.get_text(" ", strip=True)).lower()
    return "results for" in text and "smart phones" in text


def get_next_page_url(soup: BeautifulSoup) -> str | None:
    next_link = soup.select_one('a.s-pagination-next[href]')
    if not next_link:
        return None
    return normalize_url(next_link["href"])


def extract_total_pages(soup: BeautifulSoup) -> int | None:
    page_numbers: list[int] = []
    for element in soup.select(".s-pagination-container a.s-pagination-item, .s-pagination-container span.s-pagination-item"):
        value = clean_text(element.get_text(" ", strip=True))
        if value.isdigit():
            page_numbers.append(int(value))
    return max(page_numbers) if page_numbers else None


def infer_manufacturer(title: str, soup: BeautifulSoup) -> str:
    brand_selectors = [
        "#bylineInfo",
        "#productOverview_feature_div td.a-span9 span",
        "#poExpander .po-brand .po-break-word",
        "tr.po-brand td.a-span9 span",
    ]
    for selector in brand_selectors:
        element = soup.select_one(selector)
        value = clean_text(element.get_text(" ", strip=True) if element else "")
        if value:
            value = re.sub(r"^(Visit the|Brand:)\s+", "", value, flags=re.IGNORECASE)
            value = re.sub(r"\s+Store$", "", value, flags=re.IGNORECASE)
            return value
    return clean_text(title.split(" - ", 1)[0].split()[0] if title else "")


def extract_device_name(soup: BeautifulSoup) -> str:
    selectors = [
        "#productTitle",
        "#title #productTitle",
        "meta[property='og:title']",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if not element:
            continue
        value = clean_text(element.get("content") if element.has_attr("content") else element.get_text(" ", strip=True))
        if value:
            return value
    return ""


def simplify_device_name(device_name: str) -> str:
    name = clean_text(device_name)
    if not name:
        return ""
    name = re.sub(r"\s*-\s.*$", "", name)
    name = re.sub(r"\s+\d+\+\d+(?:GB|TB)\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+\d+(?:[.,]\d+)?\s?(?:GB|TB)\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r",.*$", "", name)
    name = re.sub(r"\s+Smartphone$", "", name, flags=re.IGNORECASE)
    return clean_text(name)


def family_signature(device_name: str) -> str:
    value = clean_text(device_name).lower()
    value = value.replace("smartphone", " ")
    value = value.replace("mobile phone", " ")
    value = value.replace("free android", " ")
    value = re.sub(r"\s+\d+\+\d+(?:gb|tb)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+\d+(?:[.,]\d+)?\s?(?:gb|tb)\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"\s*-\s.*$", "", value)
    value = re.sub(r"[^a-z0-9+]+", " ", value)
    return clean_text(value)


def extract_selected_dimension(soup: BeautifulSoup, dimension: str) -> str:
    selectors = [
        f"#inline-twister-expanded-dimension-text-{dimension}",
        f"#inline-twister-row-{dimension} .a-button-selected .swatch-title-text-display",
        f"#inline-twister-row-{dimension} .a-button-selected img[alt]",
        f"#variation_{dimension} .selection",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        if not element:
            continue
        value = clean_text(element.get("alt") if element.has_attr("alt") else element.get_text(" ", strip=True))
        if value:
            return value
    return ""


def extract_availability(soup: BeautifulSoup) -> str:
    selectors = [
        "#availability .primary-availability-message",
        "#availability span",
        "#twisterAvailability",
    ]
    for selector in selectors:
        element = soup.select_one(selector)
        value = clean_text(element.get_text(" ", strip=True) if element else "")
        if value:
            return value
    return ""


def first_matching_price(text: str) -> str:
    normalized = clean_text(text)
    normalized = re.sub(r"\s*([.,])\s*", r"\1", normalized)
    normalized = re.sub(r"([€$£])\s*", r"\1", normalized)
    match = PRICE_RE.search(normalized)
    return clean_text(match.group(0)) if match else ""


def first_price_from_selectors(soup: BeautifulSoup, selectors: list[str]) -> str:
    for selector in selectors:
        for element in soup.select(selector):
            text = element.get("content") if element.has_attr("content") else element.get_text(" ", strip=True)
            price = first_matching_price(text)
            if price:
                return price
    return ""


def extract_price_bundle(soup: BeautifulSoup) -> tuple[str, str]:
    current_selectors = [
        "#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center.aok-relative.apex-core-price-identifier > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay.apex-pricetopay-value",
        "#corePriceDisplay_desktop_feature_div .apex-core-price-identifier .priceToPay",
        "#corePriceDisplay_desktop_feature_div .a-price .a-offscreen",
        "#corePrice_feature_div .a-price .a-offscreen",
        "#apex_desktop .a-price .a-offscreen",
        "#price_inside_buybox",
        "#newBuyBoxPrice",
        "#tp_price_block_total_price_ww .a-offscreen",
    ]
    compare_selectors = [
        "#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-small.aok-align-center > span > span.aok-relative > span.a-size-small.a-color-secondary.aok-align-center.basisPrice > span",
        "#corePriceDisplay_desktop_feature_div .basisPrice .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .basisPrice span",
        "#corePriceDisplay_desktop_feature_div .priceBlockStrikePriceString",
    ]

    current_price = first_price_from_selectors(soup, current_selectors)
    compare_price = first_price_from_selectors(soup, compare_selectors)

    if compare_price == current_price:
        compare_price = ""

    return current_price, compare_price


def extract_variant_urls(soup: BeautifulSoup, current_url: str) -> list[str]:
    urls: set[str] = set()
    urls.add(canonical_dp_url(current_url))

    for anchor in soup.select(
        "#inline-twister-row-color_name a[href], "
        "#inline-twister-row-size_name a[href], "
        ".s-color-swatch-container a[href], "
        "a.maf-variation-options-link[href]"
    ):
        href = anchor.get("href")
        if href:
            normalized = canonical_dp_url(href)
            if normalized:
                urls.add(normalized)

    for node in soup.select("#inline-twister-row-color_name li[data-asin], #inline-twister-row-size_name li[data-asin]"):
        classes = " ".join(node.get("class", []))
        if "a-button-unavailable" in classes:
            continue
        style = clean_text(node.get("style", ""))
        if "display: none" in style.lower():
            continue
        asin = clean_text(node.get("data-asin"))
        if asin:
            urls.add(canonical_dp_url(current_url, asin))

    return sorted(urls)


def normalize_family_name(device_name: str, manufacturer: str) -> str:
    name = clean_text(device_name)
    manu = clean_text(manufacturer)
    if manu and name.lower().startswith(manu.lower()):
        name = clean_text(name[len(manu) :])
    name = STORAGE_RE.sub("", name)
    for separator in (" - ", ","):
        if separator in name:
            left, right = name.split(separator, 1)
            if STORAGE_RE.search(right) or any(word in right.lower() for word in ("black", "blue", "white", "silver", "green", "obsidian", "jade", "moonstone", "porcelain")):
                name = left
    return clean_text(name.strip(" -,:"))


def extract_storage_from_name(device_name: str) -> str:
    match = STORAGE_RE.search(device_name)
    return clean_text(match.group(0)) if match else ""


def parse_variant_page(html: str, url: str) -> dict:
    soup = soupify(html)
    raw_device_name = extract_device_name(soup)
    device_name = simplify_device_name(raw_device_name)
    manufacturer = infer_manufacturer(raw_device_name, soup)
    color = extract_selected_dimension(soup, "color_name")
    storage = extract_selected_dimension(soup, "size_name") or extract_storage_from_name(raw_device_name)
    price, discounted_price = extract_price_bundle(soup)
    availability = extract_availability(soup)

    canonical = soup.select_one("link[rel='canonical']")
    page_url = canonical_dp_url(canonical.get("href"), None) if canonical and canonical.get("href") else canonical_dp_url(url)
    model = normalize_family_name(raw_device_name, manufacturer)

    return {
        "page_url": page_url,
        "device_name": device_name,
        "manufacturer": manufacturer,
        "retailer": "Amazon",
        "model": model,
        "color": color,
        "storage": storage,
        "price": price,
        "discounted_price": discounted_price,
        "availability": availability,
        "_variant_urls": extract_variant_urls(soup, page_url),
    }


def is_valid_variant_payload(variant: dict) -> bool:
    return bool(variant.get("device_name") and variant.get("page_url"))


def fetch_variant_page(session: requests.Session, url: str, retries: int = 3, base_delay: float = 1.5) -> dict:
    last_variant: dict | None = None
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            if attempt:
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
                polite_sleep(base_delay * attempt, base_delay * attempt + 1.0)
            html = fetch_html(session, url)
            variant = parse_variant_page(html, url)
            last_variant = variant
            if is_valid_variant_payload(variant):
                return variant
        except requests.RequestException as exc:
            last_error = exc

    if last_variant:
        return last_variant
    if last_error:
        raise last_error
    return parse_variant_page("", url)


def fetch_search_soup(session: requests.Session, url: str, retries: int = 3, base_delay: float = 1.5) -> BeautifulSoup:
    last_soup: BeautifulSoup | None = None
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            if attempt:
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
                polite_sleep(base_delay * attempt, base_delay * attempt + 1.0)
            html = fetch_html(session, url)
            soup = soupify(html)
            last_soup = soup
            if is_valid_search_page(soup):
                return soup
        except requests.RequestException as exc:
            last_error = exc

    if last_soup is not None:
        return last_soup
    if last_error:
        raise last_error
    return soupify("")


def unique_variants(variants: Iterable[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for variant in variants:
        key = (
            clean_text(variant.get("page_url")),
            clean_text(variant.get("color")),
            clean_text(variant.get("storage")),
        )
        if key in seen:
            continue
        seen.add(key)
        filtered = {k: v for k, v in variant.items() if not k.startswith("_")}
        deduped.append(filtered)
    return deduped


def scrape_product_variants(session: requests.Session, seed_url: str, delay: float) -> list[dict]:
    queue = deque([canonical_dp_url(seed_url)])
    seen_urls: set[str] = set()
    parsed_variants: list[dict] = []
    seed_signature = ""

    while queue:
        url = queue.popleft()
        if url in seen_urls:
            continue
        seen_urls.add(url)

        variant = fetch_variant_page(session, url)
        if not is_valid_variant_payload(variant):
            continue

        current_signature = family_signature(variant.get("device_name", ""))
        if not seed_signature:
            seed_signature = current_signature
        elif current_signature and current_signature != seed_signature:
            continue

        parsed_variants.append(variant)

        for next_url in variant["_variant_urls"]:
            if next_url not in seen_urls:
                queue.append(next_url)

        polite_sleep(delay, delay + 0.8)

    return unique_variants(parsed_variants)


def format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {secs}s"
    if minutes:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def scrape_search_results(session: requests.Session, start_url: str, max_pages: int | None, delay: float) -> list[SearchCard]:
    cards: list[SearchCard] = []
    seen_asins: set[str] = set()
    url = normalize_url(start_url)
    page_count = 0
    total_pages: int | None = None

    while url and (max_pages is None or page_count < max_pages):
        soup = fetch_search_soup(session, url)
        if total_pages is None:
            total_pages = extract_total_pages(soup)

        for card in extract_search_cards(soup):
            if card.asin in seen_asins:
                continue
            seen_asins.add(card.asin)
            cards.append(card)

        page_count += 1
        progress_total = total_pages if max_pages is None and total_pages else max_pages or total_pages or "?"
        print(f"Fetched search page {page_count}/{progress_total} | products found so far: {len(cards)}")

        next_url = get_next_page_url(soup)
        url = next_url if next_url and next_url != url else None
        if url:
            polite_sleep(delay, delay + 0.8)

    return cards


def scrape_amazon(base_url: str, max_pages: int | None = None, max_products: int | None = None, delay: float = 1.2) -> dict:
    session = make_session()
    job_id = str(uuid.uuid4())
    products: list[dict] = []
    started_at = time.time()

    search_cards = scrape_search_results(session, base_url, max_pages=max_pages, delay=delay)
    if max_products is not None:
        search_cards = search_cards[:max_products]

    for index, card in enumerate(search_cards, start=1):
        try:
            variants = scrape_product_variants(session, card.url, delay=delay)
            if len(variants) <= 1:
                retry_session = make_session()
                variants_retry = scrape_product_variants(retry_session, card.url, delay=max(delay, 1.8))
                if len(variants_retry) > len(variants):
                    variants = variants_retry
        except requests.RequestException as exc:
            print(f"Skipping product {index} after request error: {card.url} ({exc})")
            continue

        if not variants:
            continue

        first_variant = variants[0]
        products.append(
            {
                "device_name": first_variant.get("device_name", card.title),
                "manufacturer": first_variant.get("manufacturer", ""),
                "retailer": "Amazon",
                "url": first_variant.get("page_url", card.url),
                "variants": variants,
                "job_id": job_id,
            }
        )

        elapsed = time.time() - started_at
        average = elapsed / index
        eta = average * max(0, len(search_cards) - index)
        print(
            f"Scraped product {index}/{len(search_cards)} | variants: {len(variants)} | "
            f"elapsed: {format_duration(elapsed)} | eta: {format_duration(eta)} | {card.title}"
        )

    return {"products": products}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape Amazon.es smartphone listings and variant combinations.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Amazon search results URL.")
    parser.add_argument("--max-pages", type=int, default=None, help="How many search result pages to scrape. Default: all pages.")
    parser.add_argument("--max-products", type=int, default=None, help="Optional cap for products to expand.")
    parser.add_argument("--delay", type=float, default=1.2, help="Delay between requests in seconds.")
    parser.add_argument("--output", default="amazon_products.json", help="Path to the output JSON file.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    started_at = time.time()

    data = scrape_amazon(
        base_url=args.base_url,
        max_pages=args.max_pages,
        max_products=args.max_products,
        delay=args.delay,
    )

    with open(args.output, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    total_elapsed = time.time() - started_at
    print(f"Saved {len(data['products'])} products to {args.output} in {format_duration(total_elapsed)}")


if __name__ == "__main__":
    main()
