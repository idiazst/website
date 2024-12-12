import bibtexparser
import re

def replace_latex_with_html(text):
    text = text.replace("{\\'a}", "á").replace("{\\'i}", "í")
    text = text.replace("\\'a", "á").replace("\\'i", "í")
    text = re.sub(r"\$\^\{\\dagger\}\$|\$\^\\dagger\$|\$\^\{\\star\}\$|\$\^\\star\$", "", text)
    text = re.sub(r"\\underline\{([^}]*)\}", r"<u>\1</u>", text)
    return text

def format_harvard_citation(entry):
    """Formats a single entry in Harvard-style citation."""
    authors = replace_latex_with_html(entry.get('author', 'Unknown Authors'))
    year = entry.get('year', 'Unknown Year')
    title = replace_latex_with_html(entry.get('title', 'No Title'))
    journal = replace_latex_with_html(entry.get('journal', ''))
    volume = entry.get('volume', '')
    issue = entry.get('number', '')  # BibTeX often uses "number" for issue
    pages = entry.get('pages', '')

    citation = f"{authors} ({year}). {title}. <em>{journal}</em>, {volume}"
    if issue:
        citation += f"({issue})"
    if pages:
        citation += f", {pages}"
        citation += "."
    return citation

def generate_publications_html(bibfile_path, output_path):
    with open(bibfile_path) as bibfile:
        bib_database = bibtexparser.load(bibfile)

    stats_entries = []
    clinical_entries = []

    for entry in bib_database.entries:
        keywords = entry.get('keywords', '').lower()
        if 'stats' in keywords:
            stats_entries.append(entry)
        if 'clinical' in keywords:
            clinical_entries.append(entry)

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Publications - Iván Díaz</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            line-height: 1.6;
            background-color: #ffffff;
            color: #222;
        }
        nav {
            display: flex;
            justify-content: center;
            background-color: #004080;
            padding: 10px 0;
        }
        nav a {
            color: #fff;
            text-decoration: none;
            margin: 0 15px;
            font-weight: bold;
        }
        nav a:hover {
            text-decoration: underline;
        }
        main {
            max-width: 900px;
            margin: 30px auto;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h2 {
            margin-top: 20px;
        }
        ul {
            list-style-type: none;
            padding: 0;
        }
        li {
            margin: 10px 0;
        }
        a {
            color: #005c99;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <nav>
        <a href="index.html">Home</a>
        <a href="publications.html">Publications</a>
        <a href="team.html">Team</a>
        <a href="software.html">Software</a>
    </nav>
    <main>
    """
    html += "        <h2>Publications Related to Statistical Methodology</h2>\n"
    html += "        <ul style='list-style-type: disc; padding-left: 20px;'>\n"  # Ensure bullets are displayed
    for entry in stats_entries:
        citation = format_harvard_citation(entry)
        html += f"            <li>{citation}</li>\n"
    html += "        </ul>\n"

    html += "        <h2>Publications Related to Clinical Applications</h2>\n"
    html += "        <ul style='list-style-type: disc; padding-left: 20px;'>\n"  # Ensure bullets are displayed
    for entry in clinical_entries:
        citation = format_harvard_citation(entry)
        html += f"            <li>{citation}</li>\n"
    html += "        </ul>\n"

    html += """
    </main>
</body>
</html>
"""

    with open(output_path, 'w') as html_file:
        html_file.write(html)

# Generate the publications.html file
generate_publications_html('assets/publications.bib', 'publications.html')
