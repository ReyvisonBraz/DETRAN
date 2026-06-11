from bs4 import BeautifulSoup


def _extract_table_data(soup: BeautifulSoup) -> list[dict]:
    rows = []
    for table in soup.find_all("table"):
        headers = []
        for th in table.find_all("th"):
            headers.append(th.get_text(strip=True))
        for tr in table.find_all("tr"):
            cells = tr.find_all("td")
            if not cells:
                continue
            row = {}
            for i, td in enumerate(cells):
                key = headers[i] if i < len(headers) else f"col_{i}"
                row[key] = td.get_text(strip=True)
            if row:
                rows.append(row)
    return rows


def _extract_key_value_pairs(soup: BeautifulSoup) -> dict:
    result = {}
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) == 2:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if key and value and len(key) < 100:
                result[key] = value
    for div in soup.find_all(["div", "p", "span"]):
        text = div.get_text(strip=True)
        if ":" in text and len(text) < 200:
            parts = text.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key and value:
                    result[key] = value
    return result


def parse_pontuacao_cnh(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Consulta Pontuação CNH",
        "dados": {},
        "html": html,
    }
    result["dados"].update(_extract_key_value_pairs(soup))
    tables = _extract_table_data(soup)
    if tables:
        result["pontos"] = tables
    for alert in soup.find_all("div", class_="alert"):
        alert_text = alert.get_text(strip=True)
        if alert_text:
            result["alerta"] = alert_text
    return result


def parse_portal_condutor(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Portal Condutor / Boletos CNH",
        "dados": {},
        "html": html,
    }
    result["dados"].update(_extract_key_value_pairs(soup))
    tables = _extract_table_data(soup)
    if tables:
        result["tabelas"] = tables
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link_text = a.get_text(strip=True).lower()
        if any(kw in href.lower() or kw in link_text for kw in ["pdf", "boleto", "impressao", "download"]):
            if href.startswith("/"):
                href = f"https://sistemas-renach.detran.pa.gov.br{href}"
            result.setdefault("links", []).append({"text": a.get_text(strip=True), "href": href})
    return result