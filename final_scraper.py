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
# DEFAULT_BASE_URL = (
#     "https://www.amazon.es/-/en/s?k=smart+phones&i=electronics&rh=n%3A599370031%2C"
#     "p_123%3A110955%257C338933%257C370584%257C46655%2Cp_n_condition-type%3A15144009031%2C"
#     "p_n_g-1003469290111%3A33554297031%2Cp_6%3AA1AT7YVPFBWXBL&dc&language=en&crid=1EWSHUM5LF9U5&"
#     "qid=1777531808&rnid=831275031&sprefix=smart+phones%2Celectronics%2C340&xpid=FS6kjNux89TFu&ref=sr_pg_1"
# )

DEFAULT_BASE_URL = "https://www.amazon.es/s?i=electronics&rh=n%3A934197031%2Cp_123%3A110955%257C146762%257C338933%257C370584%257C46655%2Cp_n_condition-type%3A15144009031%2Cp_6%3AA1AT7YVPFBWXBL&dc&language=pt&ds=v1%3AzD%2BOqrlr6eYuV0oLTHhj2rHn2OhmLBAgirek7r8pQvA&qid=1778064745&rnid=33554282031&xpid=_cicKTlqSsHek&ref=sr_nr_p_n_g-1003469290111_3"


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
]

PRICE_RE = re.compile(rf"(?:(?:{chr(8364)}|\$|\u00a3)\s?\d[\d.,]*|\d[\d.,]*\s?(?:{chr(8364)}|\$|\u00a3))")
STORAGE_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:GB|TB)\b", re.IGNORECASE)
RAM_STORAGE_RE = re.compile(
    r"\b(?P<ram>\d+(?:[.,]\d+)?)\s*(?:GB|TB|G|T)?\s*\+\s*(?P<storage>\d+(?:[.,]\d+)?)\s*(?P<unit>GB|TB|G|T)?\b",
    re.IGNORECASE,
)
HEX_COLOR_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")

COLOR_SWATCH_MAP = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "silver": (192, 192, 192),
    "blue": (0, 102, 204),
    "light blue": (102, 178, 255),
    "dark blue": (24, 52, 88),
    "green": (34, 139, 34),
    "red": (204, 51, 51),
    "orange": (255, 140, 0),
    "yellow": (240, 210, 64),
    "gold": (212, 175, 55),
    "pink": (235, 153, 171),
    "purple": (128, 0, 128),
    "brown": (120, 72, 32),
    "beige": (216, 196, 164),
}

NOISE_TOKENS = (
    "smartphone",
    "mobile phone",
    "- free android",
    "pixelsnap case",
    "battery",
    "camera",
    "sensor",
    "charger",
    "warranty",
    "version",
    "amoled",
    "display",
    "screen",
    "processor",
    "dimensity",
    "snapdragon",
    "year extra warranty",
)

KNOWN_COLOR_WORDS = (
    "black",
    "white",
    "blue",
    "light blue",
    "dark blue",
    "green",
    "red",
    "orange",
    "yellow",
    "gold",
    "pink",
    "purple",
    "brown",
    "gray",
    "grey",
    "silver",
    "beige",
    "preto",
    "branco",
    "azul",
    "verde",
    "vermelho",
    "amarelo",
    "rosa",
    "roxo",
    "cinzento",
    "cinza",
    "prata",
    "dourado",
    "lilas",
    "lilás",
    "violeta",
    "grafite",
    "titânio",
    "titanio",
    "turquesa",
    "lavanda",
    "obsidiana",
    "porcelana",
    "glaciar",
    "índigo",
    "indigo",
)

UNWANTED_TITLE_KEYWORDS = (
    "pixelsnap charger",
    "pixelsnap",
    "buds pro 2",
    "pixel buds",
    "turbopower charger",
    "turbopower 33w charger",
    " e carregador",
    "+ carregador",
    " com carregador",
    " with charger",
    "+ charger",
    " charger bundle",
    " includes charger",
    " incl. charger",
    " free charger",
)

ACCESSORY_SPLIT_RE = re.compile(
    r"\s*(?:\+|/)\s*.*\b(?:capa|case|cover|magsafe|adapter|charger|power adapter)\b.*$",
    re.IGNORECASE,
)
IPHONE_FAMILY_RE = re.compile(
    r"\b(apple\s+iphone\s+\d{1,2}(?:\s+(?:plus|pro\s*max|pro|max|mini|e))?)\b",
    re.IGNORECASE,
)


@dataclass
class SearchCard:
    asin: str
    title: str
    url: str
    price: str = ""
    discounted_price: str = ""
    availability: str = ""
    storage: str = ""
    color: str = ""


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", unescape(value)).strip()


def normalize_whitespace(value: str) -> str:
    return clean_text(value).replace(" ,", ",")


def normalize_availability(value: str) -> str:
    text = clean_text(value)
    lowered = text.lower()
    if not text:
        return ""
    if "delivery" in lowered and "unavailable" not in lowered and "out of stock" not in lowered:
        return "In stock"
    return text


def format_price(value: str) -> str:
    text = clean_text(value)
    text = text.replace(chr(8364), "\u20ac")
    text = text.replace(chr(163), "\u00a3")
    text = text.replace("???", "\u20ac")
    text = text.replace("??", "\u00a3")
    text = re.sub(r"\s*([.,])\s*", r"\1", text)
    text = re.sub(r"(\u20ac|\$|\u00a3)\s*", r"\1", text)
    text = re.sub(r"\s*(\u20ac|\$|\u00a3)", r"\1", text)
    match = PRICE_RE.search(text)
    if not match:
        return ""
    price = clean_text(match.group(0))
    trailing_currency = re.match(rf"(?P<number>\d[\d.,]*)(?P<currency>{chr(8364)}|\$|\u00a3)$", price)
    if trailing_currency:
        return f"{trailing_currency.group('currency')}{trailing_currency.group('number')}"
    return price


def parse_price_number(value: str) -> float | None:
    text = format_price(value)
    if not text:
        return None
    text = text.replace("\u20ac", "").replace("\u00a3", "").replace("$", "").strip()
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def extract_meta_refresh_url(html: str) -> str | None:
    match = re.search(r'http-equiv="refresh"\s+content="\d+;\s*URL=\'([^\']+)\'"', html, flags=re.IGNORECASE)
    return urljoin(BASE_DOMAIN, unescape(match.group(1))) if match else None


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
    html = ""
    for _ in range(3):
        response = session.get(current_url, timeout=timeout)
        response.raise_for_status()
        if not response.encoding or response.encoding.lower() == "iso-8859-1":
            response.encoding = response.apparent_encoding or "utf-8"
        html = response.text
        refresh_url = extract_meta_refresh_url(html)
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


def normalize_field(value: str | None) -> str:
    return clean_text(value).casefold()


def is_unwanted_product_title(title: str) -> bool:
    normalized_title = normalize_field(title)
    return any(keyword in normalized_title for keyword in UNWANTED_TITLE_KEYWORDS)


def is_filtered_bundle_title(title: str) -> bool:
    normalized_title = normalize_field(title)
    if not normalized_title:
        return False

    if is_unwanted_product_title(normalized_title):
        return True

    bundle_patterns = (
        r"\b(?:with|includes?|incl\.?|free|comes with)\s+(?:a\s+)?(?:pixel\s+buds|buds|charger)\b",
        r"\b(?:com|inclui)\s+(?:os\s+)?(?:pixel\s+buds|buds|carregador)\b",
        r"(?:^|\s)\+\s*(?:pixel\s+buds|buds|charger|carregador)\b",
        r"\be\s+carregador(?:\s+de\s+\d+\s*w)?\b",
        r"\bcarregador(?:\s+de\s+\d+\s*w)?\b",
    )
    return any(re.search(pattern, normalized_title, flags=re.IGNORECASE) for pattern in bundle_patterns)


def is_sponsored_card(card: Tag) -> bool:
    badge_text = clean_text(card.get_text(" ", strip=True)).lower()
    if "sponsored" in badge_text:
        return True
    return card.select_one('[aria-label*="Sponsored"], [data-component-type="sp-sponsored-result"]') is not None


def first_text(node: Tag | BeautifulSoup | None, selectors: list[str]) -> str:
    if not node:
        return ""
    for selector in selectors:
        for element in node.select(selector):
            value = clean_text(element.get("content") if element.has_attr("content") else element.get_text(" ", strip=True))
            if value:
                return value
    return ""


def normalize_storage_token(value: str) -> str:
    return re.sub(r"\s+", "", clean_text(value)).upper()


def normalize_storage_unit(unit: str | None) -> str:
    normalized = clean_text(unit).upper()
    if normalized == "G":
        return "GB"
    if normalized == "T":
        return "TB"
    return normalized or "GB"


def extract_storage_from_text(text: str) -> str:
    normalized = normalize_whitespace(text)
    for match in RAM_STORAGE_RE.finditer(normalized):
        trailing_context = normalized[match.end() : match.end() + 24].lower()
        if "ram boost" in trailing_context or trailing_context.strip().startswith("ram"):
            continue
        storage = clean_text(match.group("storage"))
        unit = normalize_storage_unit(match.group("unit"))
        return normalize_storage_token(f"{storage}{unit}")

    matches = list(STORAGE_RE.finditer(normalized))
    if not matches:
        return ""
    return normalize_storage_token(matches[-1].group(0))


def simplify_device_name(device_name: str) -> str:
    name = normalize_whitespace(device_name)
    if not name:
        return ""

    name = re.sub(r"\([^)]*\)", "", name)
    name = ACCESSORY_SPLIT_RE.sub("", name)

    iphone_match = IPHONE_FAMILY_RE.search(name)
    if iphone_match:
        return clean_text(iphone_match.group(1)).replace("Pro Max", "Pro Max")

    cut_positions: list[int] = []

    for pattern in (RAM_STORAGE_RE, STORAGE_RE):
        match = pattern.search(name)
        if match:
            cut_positions.append(match.start())

    lower_name = name.lower()
    for token in NOISE_TOKENS:
        position = lower_name.find(token)
        if position > 0:
            cut_positions.append(position)

    comma_position = name.find(",")
    if comma_position > 0:
        cut_positions.append(comma_position)

    if cut_positions:
        name = name[: min(cut_positions)]

    name = re.sub(r"\b(5g|4g)\b.*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\bsmartphone\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"[\-,:/]+$", "", name)
    return clean_text(name)


def infer_manufacturer(title: str, soup: BeautifulSoup) -> str:
    for selector in (
        "#bylineInfo",
        "#productOverview_feature_div td.a-span9 span",
        "#poExpander .po-brand .po-break-word",
        "tr.po-brand td.a-span9 span",
    ):
        element = soup.select_one(selector)
        value = clean_text(element.get_text(" ", strip=True) if element else "")
        if value:
            value = re.sub(r"^(Visit the|Brand:)\s+", "", value, flags=re.IGNORECASE)
            value = re.sub(r"\s+Store$", "", value, flags=re.IGNORECASE)
            return value
    return clean_text(title.split()[0] if title else "")


def title_case_color(value: str) -> str:
    value = clean_text(value)
    if not value:
        return ""
    slash_parts = [part.strip() for part in value.split("/") if part.strip()]
    if len(slash_parts) > 1:
        return "/".join(title_case_color(part) for part in slash_parts)
    return " ".join(part.capitalize() for part in value.split())


def looks_like_invalid_color_label(value: str) -> bool:
    normalized = normalize_field(value)
    if not normalized:
        return True

    invalid_patterns = (
        r"\bunknown\b",
        r"\bother colours?/patterns?\b",
        r"\boutras cores/padr[oõ]es\b",
        r"\bsem carregador\b",
        r"\bcarregador n[aã]o inclu[ií]do\b",
        r"\bcharger\b",
        r"\bcarregador\b",
        r"\bbuds?\b",
        r"\bversion\b",
        r"\bsmartphone\b",
        r"\bcase\b",
        r"^\+\s*",
        r"^\d+\s*[-:]",
    )
    return any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in invalid_patterns)


def extract_color_from_title(text: str) -> str:
    normalized = normalize_whitespace(text)
    normalized = re.sub(r"\([^)]*\)", "", normalized)
    normalized = RAM_STORAGE_RE.sub("", normalized)
    normalized = STORAGE_RE.sub("", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip(" -,/")
    segments = [segment.strip() for segment in normalized.split(",") if segment.strip()]
    if not segments:
        segments = [normalized]

    candidate = segments[-1].lower()
    candidate = re.sub(r"\bes version\b", "", candidate, flags=re.IGNORECASE).strip(" -")
    if not candidate:
        return ""

    for color in sorted(KNOWN_COLOR_WORDS, key=len, reverse=True):
        if candidate == color or candidate.endswith(f" {color}"):
            return title_case_color(color)

    freeform_candidate = title_case_color(candidate)
    if freeform_candidate and re.search(r"[A-Za-z]", freeform_candidate):
        words = freeform_candidate.split()
        if len(words) <= 3 and not any(re.search(r"\d", word) for word in words):
            if not STORAGE_RE.search(freeform_candidate) and not RAM_STORAGE_RE.search(freeform_candidate):
                if not re.search(r"\b(android|smartphone|display|camera|battery|charger|warranty|version)\b", freeform_candidate, flags=re.IGNORECASE):
                    return freeform_candidate

    hyphen_match = re.search(r"-\s*([A-Za-z][A-Za-z\s/]{1,40})$", normalized)
    if hyphen_match:
        trailing = title_case_color(hyphen_match.group(1))
        words = trailing.split()
        if 1 <= len(words) <= 3 and not any(re.search(r"\d", word) for word in words):
            if not re.search(r"\b(android|smartphone|display|camera|battery|charger|warranty|version|case)\b", trailing, flags=re.IGNORECASE):
                return trailing

    if freeform_candidate and re.search(r"[A-Za-z]", freeform_candidate):
        words = freeform_candidate.split()
        if len(words) <= 3 and not any(re.search(r"\d", word) for word in words):
            if not STORAGE_RE.search(freeform_candidate) and not RAM_STORAGE_RE.search(freeform_candidate):
                if not re.search(r"\b(android|smartphone|display|camera|battery|charger|warranty|version)\b", freeform_candidate, flags=re.IGNORECASE):
                    return freeform_candidate
    return ""


def strip_color_from_device_name(device_name: str, color: str) -> str:
    name = clean_text(device_name)
    resolved_color = clean_text(color)
    if not name or not resolved_color:
        return name

    patterns = [
        rf"\s*-\s*{re.escape(resolved_color)}$",
        rf"\s+{re.escape(resolved_color)}$",
        rf"\s*\(\s*{re.escape(resolved_color)}\s*\)$",
    ]
    for pattern in patterns:
        name = re.sub(pattern, "", name, flags=re.IGNORECASE)

    name = re.sub(r"[\-,:/]+$", "", name)
    return clean_text(name)


def normalize_color_name(color: str, raw_title: str = "") -> str:
    value = clean_text(color)
    value = re.sub(r"^(colour|color)\s*:\s*", "", value, flags=re.IGNORECASE).strip()
    title_color = extract_color_from_title(raw_title)

    if title_color and (not value or "/" in value):
        return title_color

    if looks_like_invalid_color_label(value):
        return title_color or ""

    lowered = value.lower()
    for color_name in sorted(KNOWN_COLOR_WORDS, key=len, reverse=True):
        if lowered == color_name or lowered.endswith(f" {color_name}"):
            return title_case_color(color_name)

    normalized_label = title_case_color(value)
    if normalized_label and not looks_like_invalid_color_label(normalized_label):
        return normalized_label
    if title_color:
        return title_color
    return ""


def rgb_from_hex(hex_color: str) -> tuple[int, int, int] | None:
    match = HEX_COLOR_RE.search(hex_color or "")
    if not match:
        return None
    value = match.group(0).lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def nearest_color_name(hex_color: str) -> str:
    rgb = rgb_from_hex(hex_color)
    if not rgb:
        return ""
    best_name = ""
    best_distance = None
    for name, target in COLOR_SWATCH_MAP.items():
        distance = sum((channel - sample) ** 2 for channel, sample in zip(rgb, target))
        if best_distance is None or distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name.title()


def extract_color_from_style(style_value: str) -> str:
    match = HEX_COLOR_RE.search(style_value or "")
    return nearest_color_name(match.group(0)) if match else ""


def extract_card_color(card: Tag, title: str = "") -> str:
    for selector in (
        ".a-section.a-spacing-none.a-spacing-top-mini.s-color-swatch-container-list-view .s-color-swatch-outer-circle-selected",
        ".s-color-swatch-container-list-view .s-color-swatch-outer-circle-selected",
        ".s-color-swatch-outer-circle-selected",
        ".s-color-swatch-inner-circle-fill",
        ".s-color-swatch-inner-circle-border",
        ".s-color-swatch-container span",
        "[class*='swatch'] span",
    ):
        for element in card.select(selector):
            anchor = element.find_parent("a", attrs={"aria-label": True})
            if anchor:
                label = clean_text(anchor.get("aria-label", ""))
                if label:
                    return normalize_color_name(label, title)

    for selector in (
        ".s-color-swatch-container a[aria-label]",
        "[class*='swatch'] a[aria-label]",
    ):
        for element in card.select(selector):
            label = clean_text(element.get("aria-label", ""))
            if label:
                return normalize_color_name(label, title)

    selectors = (
        ".s-color-swatch-inner-circle-fill[style]",
        ".s-color-swatch-inner-circle-border[style]",
        ".s-color-swatch-container [style*='background-color']",
        "[class*='swatch'] [style*='background-color']",
    )

    for selector in selectors:
        for element in card.select(selector):
            color = extract_color_from_style(element.get("style", ""))
            if color:
                return normalize_color_name(color, title)

    return normalize_color_name("", title)


def extract_device_name_from_soup(soup: BeautifulSoup) -> str:
    for selector in ("#productTitle", "#title #productTitle", "meta[property='og:title']"):
        element = soup.select_one(selector)
        if not element:
            continue
        value = clean_text(element.get("content") if element.has_attr("content") else element.get_text(" ", strip=True))
        if value:
            return value
    return ""


def extract_selected_dimension(soup: BeautifulSoup, dimension: str) -> str:
    for selector in (
        f"#inline-twister-expanded-dimension-text-{dimension}",
        f"#inline-twister-row-{dimension} .a-button-selected .swatch-title-text-display",
        f"#inline-twister-row-{dimension} .a-button-selected img[alt]",
        f"#variation_{dimension} .selection",
    ):
        element = soup.select_one(selector)
        if not element:
            continue
        value = clean_text(element.get("alt") if element.has_attr("alt") else element.get_text(" ", strip=True))
        if value:
            return value

    if dimension == "color_name":
        for selector in (
            "#inline-twister-row-color_name .a-button-selected [style]",
            "#inline-twister-row-color_name .a-button-selected span[style]",
            "#inline-twister-row-color_name .a-button-selected i[style]",
        ):
            element = soup.select_one(selector)
            if element:
                color = extract_color_from_style(element.get("style", ""))
                if color:
                    return color
    return ""


def extract_availability(soup: BeautifulSoup) -> str:
    for selector in ("#availability .primary-availability-message", "#availability span", "#twisterAvailability"):
        element = soup.select_one(selector)
        value = normalize_availability(element.get_text(" ", strip=True) if element else "")
        if value:
            return value
    return ""


def first_price_from_scope(node: Tag | BeautifulSoup, selectors: Iterable[str]) -> str:
    for selector in selectors:
        for element in node.select(selector):
            value = element.get("content") if element.has_attr("content") else element.get_text(" ", strip=True)
            price = format_price(value)
            if price:
                return price
    return ""


def first_price_from_attributes(node: Tag | BeautifulSoup, attributes: Iterable[str]) -> str:
    for element in node.select("*"):
        for attribute in attributes:
            raw_value = element.get(attribute)
            if not raw_value:
                continue
            price = format_price(str(raw_value))
            if price:
                return price
    return ""


def extract_structured_price(node: Tag | BeautifulSoup, selectors: Iterable[str]) -> str:
    for selector in selectors:
        for container in node.select(selector):
            direct_price = format_price(container.get_text(" ", strip=True))
            if direct_price:
                return direct_price

            whole = clean_text(first_text(container, [".a-price-whole"]))
            fraction = clean_text(first_text(container, [".a-price-fraction"]))
            symbol = clean_text(first_text(container, [".a-price-symbol"]))
            if not whole:
                continue

            whole = whole.rstrip(".,")
            symbol = symbol or chr(8364)
            combined = f"{symbol}{whole}"
            if fraction:
                combined = f"{combined},{fraction}"
            price = format_price(combined)
            if price:
                return price
    return ""


def extract_price_bundle(node: Tag | BeautifulSoup) -> tuple[str, str]:
    current_selectors = (
        ".a-price.aok-align-center .a-offscreen",
        ".a-price .a-offscreen",
        ".s-price-instructions-style .a-price",
        ".s-price-instructions-style a span",
        "div[data-cy='price-recipe'] .a-price",
        "div[data-cy='secondary-offer-recipe'] .a-price",
        "[data-a-price] .a-price",
        "#corePriceDisplay_desktop_feature_div .priceToPay .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .priceToPay",
        "#corePrice_feature_div .a-price .a-offscreen",
        "#price_inside_buybox",
        "#newBuyBoxPrice",
    )
    structured_current_selectors = (
        ".s-price-instructions-style .a-price",
        "div[data-cy='price-recipe'] .a-price",
        "div[data-cy='secondary-offer-recipe'] .a-price",
        ".priceToPay",
        ".a-price",
    )
    compare_selectors = (
        ".a-price.a-text-price .a-offscreen",
        ".basisPrice .a-offscreen",
        ".priceBlockStrikePriceString",
        "span[data-a-strike='true'] .a-offscreen",
    )
    current_price = first_price_from_scope(node, current_selectors)
    if not current_price:
        current_price = extract_structured_price(node, structured_current_selectors)
    if not current_price:
        current_price = first_price_from_attributes(node, ("data-a-price", "data-price", "price"))
    compare_price = first_price_from_scope(node, compare_selectors)
    current_value = parse_price_number(current_price)
    compare_value = parse_price_number(compare_price)
    if compare_price == current_price:
        compare_price = ""
    elif current_value and compare_value:
        if compare_value <= current_value or compare_value > current_value * 1.6:
            compare_price = ""
    return current_price, compare_price


def extract_search_cards(soup: BeautifulSoup) -> list[SearchCard]:
    cards: list[SearchCard] = []
    seen_asins: set[str] = set()

    for card in soup.select('div[data-component-type="s-search-result"][data-asin]'):
        asin = clean_text(card.get("data-asin"))
        if not asin or asin in seen_asins or is_sponsored_card(card):
            continue

        title_node = card.select_one("h2 span") or card.select_one("h2")
        title = clean_text(title_node.get_text(" ", strip=True) if title_node else "")
        anchor = title_node.find_parent("a") if title_node else card.select_one("a[href]")
        href = anchor.get("href") if anchor else ""
        if not title or not href:
            continue
        if "pixelsnap case" in title.lower() or is_filtered_bundle_title(title):
            continue

        price, discounted_price = extract_price_bundle(card)
        color = extract_card_color(card, title)
        availability = "In stock"

        seen_asins.add(asin)
        cards.append(
            SearchCard(
                asin=asin,
                title=title,
                url=canonical_dp_url(href, asin),
                price=price,
                discounted_price="",
                availability=availability,
                storage=extract_storage_from_text(title),
                color=color,
            )
        )

    return cards


def is_valid_search_page(soup: BeautifulSoup) -> bool:
    if soup.select('div[data-component-type="s-search-result"][data-asin]'):
        return True
    text = clean_text(soup.get_text(" ", strip=True)).lower()
    return "results for" in text


def get_next_page_url(soup: BeautifulSoup) -> str | None:
    next_link = soup.select_one("a.s-pagination-next[href]")
    if not next_link:
        return None
    return normalize_url(next_link["href"])


def extract_total_pages(soup: BeautifulSoup) -> int | None:
    pages = []
    for element in soup.select(".s-pagination-container a.s-pagination-item, .s-pagination-container span.s-pagination-item"):
        value = clean_text(element.get_text(" ", strip=True))
        if value.isdigit():
            pages.append(int(value))
    return max(pages) if pages else None


def extract_variant_urls(soup: BeautifulSoup, current_url: str) -> list[str]:
    urls: set[str] = {canonical_dp_url(current_url)}

    for selector in (
        "#inline-twister-row-color_name a[href]",
        "#inline-twister-row-size_name a[href]",
        "#twister_feature_div a[href]",
        ".swatchAvailable a[href]",
        ".s-color-swatch-container a[href]",
        "a.maf-variation-options-link[href]",
    ):
        for anchor in soup.select(selector):
            href = anchor.get("href")
            normalized = canonical_dp_url(href) if href else ""
            if normalized:
                urls.add(normalized)

    for node in soup.select("#inline-twister-row-color_name li[data-asin], #inline-twister-row-size_name li[data-asin], li[data-defaultasin]"):
        classes = " ".join(node.get("class", []))
        if "a-button-unavailable" in classes:
            continue
        asin = clean_text(node.get("data-asin") or node.get("data-defaultasin"))
        if asin:
            urls.add(canonical_dp_url(current_url, asin))

    return sorted(url for url in urls if url)


def build_variant_from_card(card: SearchCard) -> dict:
    if is_filtered_bundle_title(card.title):
        return {}

    simplified_name = simplify_device_name(card.title)
    color = normalize_color_name(card.color, card.title)
    if not color:
        color = extract_color_from_title(card.title)
    if not color:
        color = extract_color_from_title(simplified_name)
    device_name = strip_color_from_device_name(simplified_name, color)
    manufacturer = clean_text(device_name.split()[0] if device_name else card.title.split()[0])
    return {
        "page_url": card.url,
        "device_name": device_name,
        "manufacturer": manufacturer,
        "retailer": "Amazon",
        "model": device_name,
        "color": color,
        "storage": card.storage,
        "price": card.price,
        "discounted_price": card.discounted_price,
        "availability": card.availability,
    }


def variant_identity_key(variant: dict) -> tuple[str, str, str]:
    return (
        normalize_field(variant.get("manufacturer")),
        clean_text(variant.get("page_url")),
        normalize_field(variant.get("storage")) or clean_text(variant.get("page_url")),
    )


def variant_quality_score(variant: dict) -> tuple[int, int, int, int]:
    fields = [
        clean_text(variant.get("price")),
        clean_text(variant.get("discounted_price")),
        clean_text(variant.get("availability")),
        clean_text(variant.get("color")),
        clean_text(variant.get("storage")),
    ]
    return (
        sum(bool(field) for field in fields),
        len(fields[0]),
        len(fields[1]),
        len(clean_text(variant.get("page_url"))),
    )


def unique_variants(variants: Iterable[dict]) -> list[dict]:
    best_by_key: dict[tuple[str, str, str], dict] = {}
    for variant in variants:
        filtered = {key: value for key, value in variant.items() if not key.startswith("_")}
        key = variant_identity_key(filtered)
        existing = best_by_key.get(key)
        if existing is None or variant_quality_score(filtered) > variant_quality_score(existing):
            best_by_key[key] = filtered
    return sorted(
        best_by_key.values(),
        key=lambda item: (
            normalize_field(item.get("storage")),
            normalize_field(item.get("color")),
            clean_text(item.get("page_url")),
        ),
    )


def product_identity_key(product: dict) -> tuple[str, str]:
    return (
        normalize_field(product.get("manufacturer")),
        family_signature(product.get("device_name", "")),
    )


def group_cards_into_products(cards: Iterable[SearchCard], job_id: str) -> list[dict]:
    grouped: dict[tuple[str, str], dict] = {}

    for card in cards:
        variant = build_variant_from_card(card)
        if not variant.get("device_name"):
            continue

        product = {
            "device_name": variant["device_name"],
            "manufacturer": variant["manufacturer"],
            "retailer": "Amazon",
            "url": variant["page_url"],
            "variants": [variant],
            "job_id": job_id,
        }
        key = product_identity_key(product)
        existing = grouped.get(key)

        if existing is None:
            grouped[key] = product
            continue

        existing["variants"] = unique_variants(existing["variants"] + [variant])

        if len(existing["variants"]) == 1:
            existing["url"] = existing["variants"][0].get("page_url", existing["url"])

    grouped_products = []
    for product in grouped.values():
        product["variants"] = unique_variants(product["variants"])
        if product["variants"]:
            product["url"] = product["variants"][0].get("page_url", product["url"])
        grouped_products.append(product)

    grouped_products.sort(
        key=lambda item: (
            normalize_field(item.get("manufacturer")),
            normalize_field(item.get("device_name")),
        )
    )
    return grouped_products


def family_signature(device_name: str) -> str:
    value = simplify_device_name(device_name).lower()
    value = re.sub(r"[^a-z0-9+]+", " ", value)
    return clean_text(value)


def parse_variant_page(html: str, url: str, seed_card: SearchCard | None = None) -> dict:
    soup = soupify(html)
    raw_title = extract_device_name_from_soup(soup) or (seed_card.title if seed_card else "")
    if is_filtered_bundle_title(raw_title):
        return {
            "page_url": canonical_dp_url(url),
            "device_name": "",
            "manufacturer": "",
            "retailer": "Amazon",
            "model": "",
            "color": "",
            "storage": "",
            "price": "",
            "discounted_price": "",
            "availability": "",
            "_variant_urls": [],
        }

    device_name = simplify_device_name(raw_title)
    manufacturer = infer_manufacturer(raw_title, soup) or clean_text(device_name.split()[0] if device_name else "")
    color = normalize_color_name(extract_selected_dimension(soup, "color_name"), raw_title)
    storage = extract_selected_dimension(soup, "size_name") or extract_storage_from_text(raw_title)
    price, discounted_price = extract_price_bundle(soup)
    availability = extract_availability(soup)

    if seed_card:
        if not storage:
            storage = seed_card.storage
        if not price:
            price = seed_card.price
        if not discounted_price:
            discounted_price = seed_card.discounted_price
        if not availability:
            availability = normalize_availability(seed_card.availability)
        color = normalize_color_name(color or seed_card.color, raw_title or seed_card.title)

    canonical = soup.select_one("link[rel='canonical']")
    page_url = canonical_dp_url(canonical.get("href"), None) if canonical and canonical.get("href") else canonical_dp_url(url)

    return {
        "page_url": page_url,
        "device_name": device_name,
        "manufacturer": manufacturer,
        "retailer": "Amazon",
        "model": device_name,
        "color": color,
        "storage": storage,
        "price": price,
        "discounted_price": "",
        "availability": availability,
        "_variant_urls": extract_variant_urls(soup, page_url),
    }


def is_valid_variant_payload(variant: dict) -> bool:
    return bool(variant.get("device_name") and variant.get("page_url"))


def fetch_variant_page(
    session: requests.Session,
    url: str,
    seed_card: SearchCard | None = None,
    retries: int = 3,
    base_delay: float = 1.5,
) -> dict:
    last_variant: dict | None = None
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            if attempt:
                session.headers["User-Agent"] = random.choice(USER_AGENTS)
                polite_sleep(base_delay * attempt, base_delay * attempt + 1.0)
            html = fetch_html(session, url)
            variant = parse_variant_page(html, url, seed_card=seed_card)
            last_variant = variant
            if is_valid_variant_payload(variant):
                return variant
        except requests.RequestException as exc:
            last_error = exc

    if last_variant:
        return last_variant
    if last_error:
        raise last_error
    return parse_variant_page("", url, seed_card=seed_card)


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


def scrape_product_variants(session: requests.Session, seed_card: SearchCard, delay: float) -> list[dict]:
    queue = deque([canonical_dp_url(seed_card.url)])
    seen_urls: set[str] = set()
    parsed_variants: list[dict] = [build_variant_from_card(seed_card)]
    seed_signature = family_signature(seed_card.title)

    while queue:
        url = queue.popleft()
        if url in seen_urls:
            continue
        seen_urls.add(url)

        variant = fetch_variant_page(session, url, seed_card=seed_card)
        if not is_valid_variant_payload(variant):
            continue

        current_signature = family_signature(variant.get("device_name", ""))
        if seed_signature and current_signature and current_signature != seed_signature:
            continue

        parsed_variants.append(variant)

        for next_url in variant.get("_variant_urls", []):
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
    started_at = time.time()

    search_cards = scrape_search_results(session, base_url, max_pages=max_pages, delay=delay)
    products = group_cards_into_products(search_cards, job_id=job_id)
    if max_products is not None:
        products = products[:max_products]

    elapsed = time.time() - started_at
    total_variants = sum(len(product.get("variants", [])) for product in products)
    print(
        f"Grouped {len(search_cards)} cards into {len(products)} products and {total_variants} variants "
        f"in {format_duration(elapsed)}"
    )

    return {"products": products}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrape Amazon.es smartphone listings and variants.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Amazon search results URL.")
    parser.add_argument("--max-pages", type=int, default=None, help="How many search result pages to scrape.")
    parser.add_argument("--max-products", type=int, default=None, help="Optional cap for products to expand.")
    parser.add_argument("--delay", type=float, default=1.2, help="Delay between requests in seconds.")
    parser.add_argument("--output", default="amazon_products.json", help="Path to output JSON file.")
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

    duration = format_duration(time.time() - started_at)
    print(f"Saved {len(data['products'])} products to {args.output} in {duration}")


if __name__ == "__main__":
    main()
