import re
import logging
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.data_ingestion.common.exceptions import ScraperParsingError

logger = logging.getLogger("marinex.ingestion.parsers.html")

class HTMLTableParser:
    """
    Robust HTML parser specifically designed for extracting tabular observations,
    coastal weather station data, and marine bulletin text from official government portals.
    """

    @staticmethod
    def parse_tables(html_content: str) -> List[List[Dict[str, str]]]:
        """
        Extracts all HTML tables in a document into lists of dictionary rows.
        First row or <th> elements are used as dictionary keys.
        """
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            result = []

            for tbl in tables:
                rows = tbl.find_all("tr")
                if not rows:
                    continue

                headers: List[str] = []
                first_row = rows[0]
                th_cells = first_row.find_all(["th", "td"])
                for th in th_cells:
                    header_text = th.get_text(strip=True).lower()
                    # Clean header: remove non-alphanumeric except underscore
                    clean_hdr = re.sub(r"[^\w\s]", "", header_text).replace(" ", "_")
                    headers.append(clean_hdr or f"col_{len(headers)}")

                table_data: List[Dict[str, str]] = []
                for tr in rows[1:]:
                    td_cells = tr.find_all(["td", "th"])
                    if not td_cells:
                        continue
                    row_dict = {}
                    for idx, td in enumerate(td_cells):
                        key = headers[idx] if idx < len(headers) else f"col_{idx}"
                        val = td.get_text(strip=True)
                        row_dict[key] = val
                    if row_dict:
                        table_data.append(row_dict)

                if table_data:
                    result.append(table_data)

            return result
        except Exception as e:
            logger.error(f"[HTMLTableParser] Failed to parse HTML tables: {e}")
            raise ScraperParsingError("HTML-Table", str(e))

    parse_all_tables = parse_tables

    @staticmethod

    def extract_bulletin_sections(html_content: str) -> Dict[str, str]:
        """
        Extracts standard coastal bulletin sections (e.g. Synoptic Situation, Weather Forecast,
        Warning / Squall / Gale, Sea Area Bulletin) from official portals.
        """
        if not html_content:
            return {}

        soup = BeautifulSoup(html_content, "html.parser")
        sections: Dict[str, str] = {}

        # Look for headers (h1, h2, h3, h4, strong, b) followed by paragraphs
        elements = soup.find_all(["h1", "h2", "h3", "h4", "strong", "b", "p", "div"])
        current_section = "general"

        for el in elements:
            txt = el.get_text(strip=True)
            if not txt:
                continue

            lower = txt.lower()
            if any(term in lower for term in ["synoptic", "situation", "weather forecast", "warning", "cyclone", "squall", "fishermen", "ports"]):
                current_section = re.sub(r"[^\w\s]", "", lower).replace(" ", "_")[:32]
                sections[current_section] = ""
            elif current_section:
                existing = sections.get(current_section, "")
                if txt not in existing:
                    sections[current_section] = (existing + "\n" + txt).strip()

        return sections

    @staticmethod
    def clean_text(text: Optional[str]) -> str:
        """Strips HTML tags, collapses whitespace, and cleans unprintable characters."""
        if not text:
            return ""
        clean = re.sub(r"<[^>]+>", "", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean
