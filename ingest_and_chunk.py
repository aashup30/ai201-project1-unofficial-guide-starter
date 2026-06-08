#!/usr/bin/env python3
"""
Georgia Tech Restaurant RAG — Ingestion & Chunking Pipeline
============================================================
Sources   : 10 (Reddit threads, blogs, Yelp/TripAdvisor manual fallback)
Chunk size: 200 characters
Overlap   : 50 characters
Output    : documents/<name>_raw.txt
            documents/<name>_clean.txt
            chunks/all_chunks.json

Dependencies: stdlib only (urllib, html.parser, json, re, pathlib)
              No third-party packages needed for this milestone.

Usage:
    python ingest_and_chunk.py

For sources that block automated access (Yelp, TripAdvisor, and Reddit
threads that return 403), manually copy the page text and save it to
documents/<source_name>.txt — the script picks these up automatically.

Source names for manual fallback:
    documents/yelp_campus_food.txt
    documents/tripadvisor_near_gt.txt
    documents/reddit_best_food_on_campus.txt
    documents/reddit_best_eat_drink.txt
    documents/reddit_must_eat.txt
"""

import json
import re
import time
from dataclasses import dataclass
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
from typing import Optional
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen

# ── Configuration ─────────────────────────────────────────────────────────────

CHUNK_SIZE    = 400   # characters (from planning.md)
CHUNK_OVERLAP = 50    # characters (from planning.md)

RAW_DIR    = Path("documents")
CHUNKS_DIR = Path("chunks")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json,*/*;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
}

SOURCES = [
    {
        "id": 1, "type": "reddit", "name": "reddit_best_food_on_campus",
        "url": "https://www.reddit.com/r/gatech/comments/sitg69/"
               "what_are_all_the_best_food_places_on_campus/",
    },
    {
        "id": 2, "type": "blog", "name": "atlanta_eats",
        "url": "https://www.atlantaeats.com/blog/restaurants-near-georgia-tech-atlanta/",
    },
    {
        "id": 3, "type": "js_heavy", "name": "yelp_campus_food",
        "url": "https://www.yelp.com/search?find_desc=Campus+Food"
               "&find_loc=Georgia+Tech%2C+Atlanta%2C+GA",
    },
    {
        "id": 4, "type": "blog", "name": "odyssey_best_places",
        "url": "https://www.theodysseyonline.com/best-places-to-eat-around-georgia-tech",
    },
    {
        "id": 5, "type": "blog", "name": "infatuation_near_gt",
        "url": "https://www.theinfatuation.com/atlanta/guides/where-to-eat-near-georgia-tech",
    },
    {
        "id": 6, "type": "js_heavy", "name": "tripadvisor_near_gt",
        "url": "https://www.tripadvisor.com/ShowTopic-g60898-i104-k14737543"
               "-Good_restaurants_near_Georgia_Tech-Atlanta_Georgia.html",
    },
    {
        "id": 7, "type": "reddit", "name": "reddit_best_eat_drink",
        "url": "https://www.reddit.com/r/gatech/comments/n9zo4l/"
               "what_are_the_best_places_near_campus_to_eatdrink/",
    },
    {
        "id": 8, "type": "blog", "name": "rambler_atlanta",
        "url": "https://rambleratlanta.com/resources/top-restaurants-near-campus/",
    },
    {
        "id": 9, "type": "reddit", "name": "reddit_must_eat",
        "url": "https://www.reddit.com/r/gatech/comments/9ajrqb/must_eat_restaurants/",
    },
    {
        "id": 10, "type": "blog", "name": "eater_midtown",
        "url": "https://atlanta.eater.com/maps/best-restaurants-bars-midtown-atlanta",
    },
]

# ── Embedded Reddit data (scraped 2026-06-08) ────────────────────────────────
# Hardcoded directly to avoid Reddit API 403 errors.

REDDIT_DATA = {
    "reddit_best_food_on_campus": [
        "Cheba hut, right behind the CRC. Awesome subs. Have been there 10+ times.",
        "Trying out Cheba tomorrow now! What are some of your favorites?",
        "I get something different every time since they have a big menu, so they're all my favorites. The most recent one I got had chicken, bacon, and ranch as the main.",
        "Kali mist 100%",
        "Cheba hut is insanely good",
        "Wing-fucking-nuts",
        "Is it really that good though? I've been there 3 times and each time it was just... sad.",
        "It is sad and expensive.",
        "Thats a place to go when your day goes to shit and you need something to comfort you.",
        "I think for most people once you find your flavor that's it. Jamaican jerk was it for me.",
        "I dont think its that good. Pretty mid.",
        "Nah, hear me out. You buy a shirt from them, $10 and it’s pretty comfy, and only go on Wednesdays. You get a sizable amount of food, and a free brownie when you wear their shirt there. Adds up if you go semi-often. In addition, those meals are indeed ~$15, but it’s only expensive if you eat all that in one sitting (kudos if you can lol). I turn that into 3 meals easy, so $5 each. All how you spin it honestly. Hard to find a place that’ll give you 1 1/2 pounds chicken, a ton of fries, and a drink for that price. Also, chipotle ranch is meta tbh",
        "Food Terminal and Firehouse were my favorites",
        "Wagaya is a yummy Japanese restaurant and there’s a cute lil Japanese grocery store next to it!",
        "JR CRICKETS get the lemon pepper wet wings, you will not regret it",
        "Atwoods pizza is amazing, right across the street from Scheller. Blue donkey not bad, but it's always packed. Wingnuts is fire, the Korean fried chicken place near the UPS around 8th street is really good. Ponko chicken is amazing. Publix has really good subs, but the one near tech square is a little more expensive than the one near north ave. Qdoba is really really good, far better than chipotle. The pho spots around campus are honestly not that good, service takes a long time, broth is ok. Avoid rays pizza. Tea corner is pretty decent. Park 27 kbbq is extremely overpriced, meat quality is decent at best. If you have a car, there are much better places you can go to. Have heard really good things about Antico.",
        "Midtown (right next to GT): Momonoki Ramen pretty close by, and it's a great ramen place, highly recommend. Halal guys is generally very nice too, they offer takeout, and they're open very late (somedays till 1am). Waffle House. Tin Drum (sometimes this place is understaffed). Ray's Pizza (super popular place for takeout/dine-in, their pizza is really good). Gyro Bros (worse than Halal guys imo, but cheaper). In terms of dining halls: Brittain: probably the best place on East, generally has a variety of food. Nav: the only place on East open on weekends; rather consistent with its food. Willage: great all-around, the only place on West.",
        "Rays pizza is not it. You go in there to wait 20 minutes for a slice of pizza, and the cheese is soggy, sauce has no flavor, crust and bread is soggy. It's such a hit or miss spot, would rather just go to atwoods across the street",
        "Scoville fried chicken sandwiches are really good, there’s one not too far from tech driving distance.",
        "On Wednesdays, Marrakech express (near exhibition hall) has really good lamb and chicken",
        "I second this place. It’s tastes amazing and it’s cheaper than what they sell on the food trucks. Better than gyro bros imo.",
        "Totally agree! I am blown away by how much lamb he gives for $12",
        "Wingnuts and Satto being in the same spot always makes my life difficult. They’re both so good",
        "Blue Donkey",
        "It's wingnut Wednesday",
        "Not top tier itself, but twisted taco queso in the exhibition hall hits different after a hard day",
        "Check out the ig account @gt_food_review. Also best place for milkshakes is cookout!",
        "I love gyro bros in time square, they have meal deals and it’s a bunch of food and a drink for like $9. Ponko chicken is also a favorite of mine. A little further away is McAlister’s which is a Panera-like chain and it’s my favorite lunch spot.",
        "+1 on gyro Bros, I go there at least once every few weeks. Price is pretty good, food is amazing, and right across the street from my classes",
        "Wok Chi",
        "O-ku is great, especially when they have their roll happy hours.",
        "Thumbs Up diner next to the right of cheba hut. Very much recommend but bring cash because they only take cash!!",
        "If you’re willing to go off campus and spend a little money for a night out, I really enjoy Bartaco off west. It’s quality Mexican. Their guacamole is something special.",
        "I liked Umma's House a lot. Especially when the free miso soup didn't run out.",
        "Ponko Chicken (Japanese-American) and Ahns Kitchen (Vietnamese) are both on Peachtree Street. Ahns is close to Scheller, Ponko is close to the Publix.",
        "Ponko chicken is so good",
        "AVIVA at the Coda building!!!! Amazing, healthy food! Also, Vietvana is dope too.",
        "Moe's (in Tech Square) has any burrito for like $6ish+tax on Monday. You can also get chips and salsa with it for free.",
        "Do (all) the food trucks on campus take dining dollars? Or is it buzzfunds?",
        "They take both dining and buzzfunds!",
        "Atwood’s, Antico for pizza. Halal Guys, Mamoun’s Falafel for Mediterranean. 26 Thai. Rreal Tacos, Tin Lizzy’s.",
        "For some spots a little further from campus: Fellini’s Pizza is probably my favorite pizza place. Good quality and relatively cheap compared to Antico’s. They sell pizza by the slice and usually 2 slices is pretty filling. Velvet Taco is a Mexican fusion restaurant offering some pretty unique tacos. 26 Thai is def the best Thai near campus. It’s definitely better than Satto. Tabla is really good for Indian food, but good luck finding a table.",
        "I really like Blue India for Indian which is closeish to tech square!",
        "Choongman Chicken for good chicken very messy though",
        "Tin Drum (in Tech Square) is fire",
        "Talkin Tacos is a new concept on Piedmont Road NE. We will be offering student discounts. Our customers’ favorite items are: Caribbean tacos, Cali burrito, Chicken Achiote, Birria Tacos, Street Corn. About 2-3 miles from campus, available on Uber Eats.",
    ],
    "reddit_must_eat": [
        "Alma cocina (Mexican), la mei zi (Taiwanese), mamak (Malaysian), las delicias de la abuela (Colombian), ecco (Italian), la tavola (Italian), brush sushi (Japanese), desta (Ethiopian), chai pani (Indian), Sufis (Persian), Nam phuong (vietnamese)... I think these should be enough to start with haha",
        "This is a really solid list. I regularly went to Chai Pani and Desta in particular. To add a few more of my favorites: Lee’s Bakery for banh mi (pho isn’t bad either), Purnima (Bangladeshi), and Food Terminal is a newer SE Asian/Malaysian place on Buford Highway.",
        "For Banh Mi I STRONGLY recommend Quoc Huong Banh Mi on Buford Hwy, but for pho I recommend Pho Bac instead.",
        "I second Quoc Huong for Bahn mi. It is perfection. Just remember they are a cash only business",
        "As an Indian, chai pani is just okay, try Gokul Sweets or Zyka instead",
        "For sushi, I would recommend trying Kuroshio here in midtown. I went to brush 2 weeks ago and found it generally overpriced and all around meh.",
        "Kuroshio runs a half off all sushi special every Wednesday from 5-7pm",
        "Rumi's > Sufi's IMO",
        "This is an amazing list. For Indian I would recommend Chat Patti instead because its less expensive and in the area for similar quality.",
        "What kind of food do you like? If you haven't been over to Buford Hwy yet I would strongly recommend it as there's tons of authentic restaurants for just about any cuisine you can imagine. Just take MARTA to the chamblee stop and you can walk over like a block to get on a stretch of Buford Highway that's just restaurant after restaurant and for the most part they're very affordable. Some of my favorites: Chong Qing Hot Pot (authentic chinese food, has delicious and huge hotpots), Food Terminal (owned by owners of Sweet Hut, very modern with tons of malaysian food options), El Rey Del Taco (mexican restaurant with delicious homemade corn tortillas), Tempo Doeloe (hole in the wall type place with good cheap indonesian food), Yet Tuh (sort of hidden small korean restaurant with delicious seafood pancakes), Quoc Huong (cheap and delicious Banh mi). Other great restaurants: Zyka (best indian food in Atlanta imo, I love their chicken 65), Antico (close to campus, authentic neopolitan type pizza with ingredients shipped in from italy), Desta Ethiopian.",
        "lemon pepper wings - doesn't matter where from, just get them",
        "You're from Atlanta aren't you?",
        "yeah, honestly i don't even like wings that much but lemon pepper wings are undeniably atlanta's staple food",
        "Very solid list! Tempo doeloe is very authentic and delicious Indonesian food. Almost all the dishes taste like they do at home.",
        "I think they have a great beef rendang. Each time I go I just get their lunch combo. If you do a la carte you can go for the Indonesian staples of Nasi Goreng (fried rice) or Nasi Padang.",
        "check out west village",
        "Great Japanese at Wa Ga Ya on 14th, I go there for ramen once a week.",
        "Jinya is also awesome",
        "Jinya is great but it's a national chain so I wouldn't exactly call it an Atlanta staple.",
    ],
    "reddit_best_eat_drink": [
        "If you like boba, I highly recommend Tea Corner! It's on the corner of North Ave and Peachtree St. It's a relatively new place (opened in fall 2020), but it's really good. It's also owned and run by just two people, who are both super nice.",
        "Ding Tea just opened off west on the way to West egg, another good food area.",
        "Ding tea was really good. Kinda pricy (around where sweethut prices are) but good",
        "Boba is a commodity, it's always gonna be kinda pricey. But at least ding tea is good where as sweethut's milk tea is widely considered to be better than nothing but worse than anything else.",
        "Cypress Street Pint and Plate, Antico, and Bone Lick BBQ were some of my favorite places. Unfortunately Bone Lick is no longer in West Midtown. Antico is the best pizza I've ever had. Cypress Street has the best chicken fingers I've ever had, and they have great burgers as well.",
        "You know you're from the South when Antico's is the best pizza you've ever had",
        "I mean it regularly appears on lists of best pizza in the state and the country, so it isn't just me that thinks so.",
        "I’ve lived all over the country including NYC — Antico and Amazzas are two of the best pizzas I’ve ever had.",
        "Ditto. I'm from NY. Antico's is still some of the best pizza I've ever had. Junior's is the best NY style pizza I've had in Atlanta. And their sicilian is like genuinely A+ tier usually.",
        "What kind of pizza do you like? I really like Antico.",
        "Circle Poké is just off campus, and it was basically my favorite restaurant while I was a student. I've graduated, but I'm still living in Atlanta, and any time I'm nearby Tech, I always always go back",
        "This 100000%",
        "seconded!!",
        "Nothing will ever beat cookout at 2 am when you’re crying over CS homework",
        "Atwood's Pizza just off of Tech Square is great",
        "Their cheese is great, and it's not super expensive like Antico. Underrated imo.",
        "And as far as I know their owner doesn’t abuse his employees!",
        "Exactly why I try to go to Veruni Napoli when I have an Antico's craving.",
        "Atwood's is a close #2 to Antico's imo, both are way better than Ray's",
    ],
}

# Lines containing these phrases are stripped
BOILERPLATE_PHRASES = [
    "read more", "share this", "follow us", "subscribe here", "sign up",
    "cookie policy", "privacy policy", "terms of service", "all rights reserved",
    "advertisement", "sponsored content", "related articles",
    "you might also like", "comments are closed", "leave a comment",
    "click here", "javascript is required", "enable javascript",
    "skip to content", "skip to main", "back to top",
    # CMS / Odyssey nav fragments
    "create account", "create one", "forgot password", "log in", "log out",
    "sign in", "sign up for", "already have an account", "don't have an account",
    "report this", "report abuse", "flag this", "share on", "tweet this",
    "facebook", "instagram", "twitter", "newsletter", "get the latest",
    "trending now", "most popular", "more stories", "next article",
    "previous article", "written by", "cover image credit",
    "powered by", "top creators", "best of", "keep reading",
    "show less", "load more", "view all", "see all",
]

# When any of these appear in a line, truncate the document at that point.
# Everything after (unrelated articles, sidebars, footers) is discarded.
TRUNCATION_MARKERS = [
    "this article has not been reviewed",
    "subscribe to our newsletter",
    "recommended for you",
    "you might also like",
    "more from odyssey",
    "keep reading...show less",
    "related searches",
    "can't find the business",
    "adding a business to yelp",
    "got search feedback",
    "browse all",
    "browse forums",
    "what are forum guidelines",
    "this topic has been closed",
    "write your email",
    "top creators",
    "word usage:",
]

# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Document:
    source_id: int
    source_name: str
    source_type: str
    url: str
    raw_text: str
    clean_text: str = ""


@dataclass
class Chunk:
    chunk_id: str
    source_id: int
    source_name: str
    url: str
    text: str
    char_start: int
    char_end: int

# ── HTML text extractor (stdlib html.parser) ──────────────────────────────────

# Tags whose content should be skipped entirely
_SKIP_TAGS = {
    "script", "style", "noscript", "iframe", "nav", "header",
    "footer", "aside", "form", "button", "svg", "figure",
}


class _TextExtractor(HTMLParser):
    """Lightweight HTML → plain-text converter using stdlib only."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        # Block-level tags add a newline for readability
        if tag in {"p", "div", "li", "h1", "h2", "h3", "h4", "h5", "br", "tr"}:
            self._parts.append("\n")

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._parts.append(data)

    def get_text(self) -> str:
        return "".join(self._parts)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()

# ── HTTP helper ───────────────────────────────────────────────────────────────

def fetch_url(url: str, timeout: int = 15) -> Optional[str]:
    """Fetch a URL and return the response body as a string."""
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=timeout) as resp:
            charset = "utf-8"
            ct = resp.headers.get_content_charset()
            if ct:
                charset = ct
            return resp.read().decode(charset, errors="replace")
    except HTTPError as e:
        print(f"  ⚠  HTTP {e.code} for {url}")
    except URLError as e:
        print(f"  ⚠  URL error for {url}: {e.reason}")
    except Exception as e:
        print(f"  ⚠  Fetch failed for {url}: {e}")
    return None

# ── Loaders ───────────────────────────────────────────────────────────────────

def load_reddit(source: dict) -> Optional[str]:
    """
    Return Reddit thread text from the hardcoded REDDIT_DATA dict.
    Data was scraped on 2026-06-08 and embedded directly to avoid
    Reddit API 403 errors.
    """
    comments = REDDIT_DATA.get(source["name"])
    if not comments:
        print(f"  ⚠  No embedded data found for {source['name']}")
        return None
    print(f"  ✓  Using embedded data ({len(comments)} comments)")
    return "\n\n".join(comments)


def load_blog(source: dict) -> Optional[str]:
    """
    Fetch a blog/article URL and convert to plain text using the
    stdlib HTMLParser. Boilerplate tags (nav, header, footer, etc.)
    are stripped before text extraction.
    """
    raw_html = fetch_url(source["url"])
    if raw_html is None:
        return None
    return html_to_text(raw_html)


def load_js_heavy(source: dict) -> Optional[str]:
    """
    Yelp and TripAdvisor block automated scraping (JavaScript rendering
    + bot detection). Falls back to a manually saved .txt file.

    To provide data:
        1. Open the URL in your browser.
        2. Select and copy all relevant text (names, reviews, ratings).
        3. Paste into documents/<source_name>.txt and save.
    """
    fallback = RAW_DIR / f"{source['name']}.txt"
    if fallback.exists():
        print(f"  ✓  Manual fallback found: {fallback}")
        return fallback.read_text(encoding="utf-8")

    # Create an empty placeholder so the user can paste directly into it
    fallback.write_text("", encoding="utf-8")
    print(
        f"  ⚠  {source['name']} requires manual extraction.\n"
        f"     URL : {source['url']}\n"
        f"     Created empty file — paste the page text into:\n"
        f"     {fallback.resolve()}\n"
        f"     Then re-run the script."
    )
    return None


def load_source(source: dict) -> Optional[str]:
    t = source["type"]
    if t == "reddit":
        return load_reddit(source)
    elif t == "js_heavy":
        return load_js_heavy(source)
    else:
        return load_blog(source)

# ── Cleaning ──────────────────────────────────────────────────────────────────

def clean_text(raw: str) -> str:
    """
    Remove everything that isn't substantive restaurant content.

    Removes : residual HTML tags, HTML entities, URLs, boilerplate lines
              (nav text, cookie banners, share buttons, footers, short
              navigation artifacts), and all content after truncation markers
              (unrelated articles, sidebars, recommended content).
    Keeps   : Restaurant names, reviews, opinions, ratings, descriptions,
              and context like location or course references.
    """
    # 1. Strip any residual HTML tags
    text = re.sub(r"<[^>]+>", " ", raw)

    # 2. Decode HTML entities
    text = unescape(text)

    # 3. Remove URLs
    text = re.sub(r"https?://\S+", "", text)

    # 4. Truncate at end-of-article markers — drop everything after
    lines = text.splitlines()
    truncated_lines = []
    for line in lines:
        lower = line.strip().lower()
        if any(marker in lower for marker in TRUNCATION_MARKERS):
            break  # stop here, discard the rest of the document
        truncated_lines.append(line)
    lines = truncated_lines

    # 5. Drop boilerplate lines and nav artifacts
    clean_lines = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()

        if not stripped:
            clean_lines.append("")
            continue

        # Skip lines containing boilerplate phrases
        if any(phrase in lower for phrase in BOILERPLATE_PHRASES):
            continue

        # Skip very short non-numeric lines (navigation artifacts)
        if len(stripped.split()) < 3 and not re.search(r"\d", stripped):
            continue

        clean_lines.append(stripped)

    text = "\n".join(clean_lines)

    # 6. Collapse whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()

# ── Chunking ──────────────────────────────────────────────────────────────────

MIN_CHUNK_LEN = 50  # drop chunks shorter than this (nav artifacts, tail fragments)


def _fixed_size_chunks(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Split a single block of text into fixed-size chunks with overlap.
    Used as a fallback when a paragraph exceeds chunk_size.
    """
    chunks = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        at_end = end == length

        if not at_end:
            boundary = text.rfind(".", start + chunk_size // 2, end)
            if boundary != -1:
                end = boundary + 1
            else:
                space = text.rfind(" ", start + chunk_size // 2, end)
                if space != -1:
                    end = space

        chunk = text[start:end].strip()
        if len(chunk) >= MIN_CHUNK_LEN:
            chunks.append(chunk)

        if at_end:
            break

        next_start = end - overlap
        if next_start <= start:
            next_start = start + max(1, chunk_size - overlap)
        start = next_start

    return chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE,
               overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Paragraph-aware chunking with fixed-size fallback.

    1. Split on paragraph breaks (blank lines) and single line breaks.
    2. If a paragraph fits within chunk_size, keep it as one chunk.
    3. If a paragraph is too long, apply fixed-size chunking with overlap.
    4. Drop anything shorter than MIN_CHUNK_LEN (nav fragments, etc.).

    This respects natural document structure (Reddit comments, blog entries,
    review paragraphs) and only subdivides text that genuinely needs it.
    """
    # Split on blank lines first, then on single newlines within each block
    paragraphs = re.split(r"\n{2,}", text)
    chunks = []

    for para in paragraphs:
        # Further split on single line breaks (e.g. bullet lists, forum posts)
        lines = [l.strip() for l in para.splitlines() if l.strip()]
        para_text = " ".join(lines).strip()

        if not para_text or len(para_text) < MIN_CHUNK_LEN:
            continue

        if len(para_text) <= chunk_size:
            chunks.append(para_text)
        else:
            chunks.extend(_fixed_size_chunks(para_text, chunk_size, overlap))

    return chunks

# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline():
    RAW_DIR.mkdir(exist_ok=True)
    CHUNKS_DIR.mkdir(exist_ok=True)

    documents: list[Document] = []
    all_chunks: list[Chunk] = []

    # ── Stage 1: Load ──────────────────────────────────────────────────────

    print("=" * 62)
    print("STAGE 1 — Loading documents")
    print("=" * 62)

    for source in SOURCES:
        print(f"\n[{source['id']:>2}/10] {source['name']}  ({source['type']})")
        raw = load_source(source)

        if raw is None:
            print("       → Skipped (no content available)")
            continue

        raw_path = RAW_DIR / f"{source['name']}_raw.txt"
        raw_path.write_text(raw, encoding="utf-8")
        print(f"       → Saved: {raw_path}  ({len(raw):,} chars)")

        documents.append(Document(
            source_id=source["id"],
            source_name=source["name"],
            source_type=source["type"],
            url=source["url"],
            raw_text=raw,
        ))

        time.sleep(1)   # polite delay between requests

    print(f"\n✓ Loaded {len(documents)}/10 documents")

    if not documents:
        print("\nNo documents loaded — nothing to chunk. Exiting.")
        return []

    # ── Stage 2: Clean ─────────────────────────────────────────────────────

    print("\n" + "=" * 62)
    print("STAGE 2 — Cleaning")
    print("=" * 62)

    for doc in documents:
        doc.clean_text = clean_text(doc.raw_text)
        clean_path = RAW_DIR / f"{doc.source_name}_clean.txt"
        clean_path.write_text(doc.clean_text, encoding="utf-8")
        reduction = (1 - len(doc.clean_text) / max(len(doc.raw_text), 1)) * 100
        print(f"  {doc.source_name:<35} "
              f"{len(doc.raw_text):>7,} → {len(doc.clean_text):>7,} chars  "
              f"({reduction:.0f}% removed)")

    # Spot-check: print first cleaned document
    print(f"\n── Spot-check: first 600 chars of '{documents[0].source_name}' (cleaned) ──")
    print(documents[0].clean_text[:600])
    print("─" * 62)
    print("ACTION: Read the output above. If you see nav text, leftover")
    print("        HTML, or boilerplate, add patterns to BOILERPLATE_PHRASES")
    print("        and re-run before continuing.")

    # ── Stage 3: Chunk ─────────────────────────────────────────────────────

    print("\n" + "=" * 62)
    print(f"STAGE 3 — Chunking  (size={CHUNK_SIZE} chars, overlap={CHUNK_OVERLAP} chars)")
    print("=" * 62)

    for doc in documents:
        doc_chunks = chunk_text(doc.clean_text)
        for i, text_content in enumerate(doc_chunks):
            char_start = max(0, i * (CHUNK_SIZE - CHUNK_OVERLAP))
            all_chunks.append(Chunk(
                chunk_id=f"{doc.source_name}_chunk_{i:04d}",
                source_id=doc.source_id,
                source_name=doc.source_name,
                url=doc.url,
                text=text_content,
                char_start=char_start,
                char_end=char_start + len(text_content),
            ))
        print(f"  {doc.source_name:<35} {len(doc_chunks):>4} chunks")

    print(f"\n✓ Total chunks: {len(all_chunks)}")

    chunks_path = CHUNKS_DIR / "all_chunks.json"
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {
                    "chunk_id":    c.chunk_id,
                    "source_id":   c.source_id,
                    "source_name": c.source_name,
                    "url":         c.url,
                    "text":        c.text,
                    "char_start":  c.char_start,
                    "char_end":    c.char_end,
                }
                for c in all_chunks
            ],
            f, indent=2, ensure_ascii=False,
        )
    print(f"✓ Chunks saved to {chunks_path}")

    print("=" * 62)
    print("Pipeline complete. Chunks saved to chunks/all_chunks.json.")
    print("=" * 62)

    return all_chunks


if __name__ == "__main__":
    run_pipeline()