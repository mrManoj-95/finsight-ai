"""Split a 10-K/10-Q HTML document into labeled Items using regex on Item headers."""
import re
from bs4 import BeautifulSoup

ITEM_PATTERN = re.compile(r"item\s+(\d+[a-c]?)\.?\s*[-–—]?\s*", re.IGNORECASE)

def extract_text(html_path) -> str:
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")


def split_into_items(raw_text: str) -> dict:
    """Returns {item_number: text} e.g. {'1A': '...', '7': '...'}"""
    matches = list(ITEM_PATTERN.finditer(raw_text))
    sections = {}
    for i, m in enumerate(matches):
        item_num = m.group(1).upper()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        chunk = raw_text[start:end].strip()
        if len(chunk) > 200:  # filter noise/TOC entries
            sections.setdefault(item_num, "")
            sections[item_num] += "\n" + chunk
    return sections