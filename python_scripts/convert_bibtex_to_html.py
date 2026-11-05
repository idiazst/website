"""Render the website bibliography from assets/publications.bib.

Run from any directory:
    python python_scripts/convert_bibtex_to_html.py
"""

import argparse
from html import escape
from pathlib import Path
import re
import unicodedata
from urllib.parse import quote, urlsplit

import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text


ROOT = Path(__file__).resolve().parents[1]
LATEX = LatexNodes2Text()
SECTIONS = (
    ("stats", "statistics", "Statistics and Causal Inference Methodology"),
    ("tech", "preprints", "Preprints"),
    ("clinical", "clinical", "Clinical and Population Health Research"),
)
CATEGORIES = ("stats", "clinical", "tech", "book", "discuss", "reports")


def plain_text(value):
    """Remove CV-only author annotations and decode LaTeX as plain Unicode."""
    value = re.sub(r"\$\^\{?\\(?:star|dagger)\}?\$", "", value)
    if re.search(r"[\\{}]", value):
        value = LATEX.latex_to_text(value)
    value = unicodedata.normalize("NFC", re.sub(r"\s+", " ", value).strip())
    return value


def split_authors(value):
    """Split BibTeX's 'and' separator without splitting braced institutions."""
    authors = []
    start = depth = i = 0
    while i < len(value):
        char = value[i]
        if char == "{" and (i == 0 or value[i - 1] != "\\"):
            depth += 1
        elif char == "}" and (i == 0 or value[i - 1] != "\\"):
            depth -= 1
        match = re.match(r"\s+and\s+", value[i:]) if depth == 0 else None
        if match:
            authors.append(value[start:i].strip())
            i += match.end()
            start = i
        else:
            i += 1
    authors.append(value[start:].strip())
    return [author for author in authors if author]


def keywords(entry):
    return {word.strip().lower() for word in entry.get("keywords", "").split(",")}


def category(entry):
    tags = keywords(entry)
    if "cvsuperseded" in tags:
        return None
    for tag in CATEGORIES:
        if tag in tags:
            return tag
    return None


def section_category(entry):
    tag = category(entry)
    return "stats" if tag in {"book", "discuss", "reports"} else tag


def select_entries(entries):
    """Omit unclassified/superseded records and merge duplicate citation IDs."""
    selected = {}
    for entry in entries:
        if not category(entry):
            continue
        previous = selected.get(entry["ID"])
        if previous is None:
            selected[entry["ID"]] = dict(entry)
        else:
            # Keep the complete citation when the same paper occurs twice.
            for field, value in entry.items():
                if field not in previous or len(value) > len(previous[field]):
                    previous[field] = value
    return list(selected.values())


def publication_url(entry):
    doi = entry.get("doi", "").strip()
    if doi:
        doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.I)
        return "https://doi.org/" + quote(doi, safe="/:().;_+-")
    arxiv = re.search(r"arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)",
                      entry.get("journal", ""), flags=re.I)
    if arxiv:
        return "https://arxiv.org/abs/" + arxiv.group(1)
    url = entry.get("url", "").strip()
    return url if urlsplit(url).scheme in {"https", "http"} else ""


def format_authors(entry):
    raw = entry["author"]
    authors = [raw] if category(entry) == "reports" else split_authors(raw)
    rendered = []
    for author in authors:
        author = plain_text(author)
        label = escape(author)
        if re.fullmatch(r"D[ií]az,\s*(?:Iv[aá]n|I\.?)|Iv[aá]n D[ií]az", author, flags=re.I):
            label = "<strong>" + label + "</strong>"
        rendered.append(label)
    return "; ".join(rendered)


def format_harvard_citation(entry):
    title = escape(plain_text(entry["title"]).rstrip("."))
    url = publication_url(entry)
    if url:
        title = '<a href="' + escape(url, quote=True) + '">' + title + "</a>"
    citation = (format_authors(entry) + " (" +
                escape(entry.get("year", "n.d.")) + "). " + title + ".")
    venue = entry.get("journal") or entry.get("booktitle") or ""
    if venue:
        citation += " <em>" + escape(plain_text(venue)) + "</em>"
    elif entry.get("publisher"):
        citation += " " + escape(plain_text(entry["publisher"]))

    volume = plain_text(entry.get("volume", ""))
    number = plain_text(entry.get("number", ""))
    pages = plain_text(entry.get("pages", "")).replace("--", "–")
    if volume and volume != "0":
        citation += ", " + escape(volume)
        if number and number != "0":
            citation += "(" + escape(number) + ")"
    if pages:
        citation += ", " + escape(pages)
    return citation.rstrip(".") + "."


def generate_publications_html(bibfile_path, output_path):
    with Path(bibfile_path).open(encoding="utf-8") as bibfile:
        entries = select_entries(bibtexparser.load(bibfile).entries)
    entries.sort(key=lambda entry: -int(entry.get("year", "0")))
    template = Path(output_path).read_text(encoding="utf-8")
    prefix, main = template.split("<main>", 1)
    _, suffix = main.split("</main>", 1)

    parts = [
        "",
        "        <h1>Publications</h1>",
        '        <nav class="publication-sections" aria-label="Publication sections">',
    ]
    for tag, anchor, heading in SECTIONS:
        if any(section_category(entry) == tag for entry in entries):
            label = heading
            parts.append('            <a href="#' + anchor + '">' + label + "</a>")
    parts.append("        </nav>")
    for tag, anchor, heading in SECTIONS:
        group = [entry for entry in entries if section_category(entry) == tag]
        if not group:
            continue
        parts.extend([
            '        <section aria-labelledby="' + anchor + '">',
            '            <h2 id="' + anchor + '">' + heading + "</h2>",
            "            <ul>",
        ])
        for entry in group:
            parts.append('                <li data-citation-id="' +
                         escape(entry["ID"], quote=True) + '">' +
                         format_harvard_citation(entry) + "</li>")
        parts.extend(["            </ul>", "        </section>"])
    parts.append("    ")
    Path(output_path).write_text(
        prefix + "<main>" + "\n".join(parts) + "</main>" + suffix,
        encoding="utf-8",
    )
    return len(entries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bib", type=Path, default=ROOT / "assets/publications.bib")
    parser.add_argument("--output", type=Path, default=ROOT / "publications.html")
    args = parser.parse_args()
    count = generate_publications_html(args.bib, args.output)
    print(f"Rendered {count} publications to {args.output}")

