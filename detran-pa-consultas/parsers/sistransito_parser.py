from bs4 import BeautifulSoup
import re


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
    for div in soup.find_all(["div", "p", "span"]):
        text = div.get_text(strip=True)
        if ":" in text and len(text) < 200:
            parts = text.split(":", 1)
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                if key and value:
                    result[key] = value
    for row in soup.find_all("tr"):
        cells = row.find_all(["td", "th"])
        if len(cells) == 2:
            key = cells[0].get_text(strip=True)
            value = cells[1].get_text(strip=True)
            if key and value and len(key) < 100:
                result[key] = value
    return result


def parse_veiculo_detalhada(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Consulta Veiculo Detalhada",
        "dados": {},
        "secoes": {},
        "html": html,
    }

    for section in soup.find_all("div", class_="section-card"):
        header = section.find("div", class_="section-header")
        if not header:
            continue
        section_name = header.get_text(strip=True)
        section_data = {}
        for item in section.find_all("div", class_="data-item"):
            label_el = item.find("div", class_="data-label")
            value_el = item.find("div", class_="data-value")
            if label_el and value_el:
                key = label_el.get_text(strip=True)
                val = value_el.get_text(strip=True)
                if key:
                    result["dados"][key] = val
                    section_data[key] = val
        if section_data:
            result["secoes"][section_name] = section_data

    nada_consta = []
    for h4 in soup.find_all("h4"):
        text = h4.get_text(strip=True)
        if "NADA CONSTA" in text or "SEM REGISTRO" in text:
            section = h4.find_parent("div", class_="section-card")
            if section:
                header = section.find("div", class_="section-header")
                section_name = header.get_text(strip=True) if header else "Desconhecido"
                result["dados"][section_name] = text
            else:
                nada_consta.append(text)
    if nada_consta:
        result["nada_consta"] = nada_consta

    error = soup.find("div", class_="error-alert")
    if error:
        result["erro"] = error.get_text(strip=True)
    return result


def parse_infracoes(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Consulta Infrações",
        "dados": {},
        "infracoes": [],
        "html": html,
    }
    result["dados"].update(_extract_key_value_pairs(soup))
    tables = _extract_table_data(soup)
    if tables:
        result["infracoes"] = tables
    for div in soup.find_all("div", class_=["result-field", "infracao-item"]):
        label = div.find("div", class_=["result-label", "infracao-label"])
        value = div.find("div", class_=["result-value", "infracao-value"])
        if label and value:
            result["dados"][label.get_text(strip=True)] = value.get_text(strip=True)
    error = soup.find("div", class_="error-alert")
    if error:
        result["erro"] = error.get_text(strip=True)
    return result


def parse_licenciamento(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Licenciamento / Boleto",
        "dados": {},
        "html": html,
    }
    result["dados"].update(_extract_key_value_pairs(soup))
    tables = _extract_table_data(soup)
    if tables:
        result["tabelas"] = tables
    for div in soup.find_all("div", class_=["result-field", "boleto-info"]):
        label = div.find("div", class_=["result-label", "info-label"])
        value = div.find("div", class_=["result-value", "info-value"])
        if label and value:
            result["dados"][label.get_text(strip=True)] = value.get_text(strip=True)
    pdf_link = None
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link_text = a.get_text(strip=True).lower()
        if any(kw in href.lower() or kw in link_text for kw in ["pdf", "boleto", "impressao", "download", "gerar"]):
            pdf_link = href if href.startswith("http") else f"https://sistemas-renavam.detran.pa.gov.br{href}"
            break
    if pdf_link:
        result["pdf_link"] = pdf_link
    barcode = soup.find("img", src=re.compile(r"barcode|codigoBarras|boleto", re.I))
    if barcode:
        result["barcode_src"] = barcode.get("src", "")
    error = soup.find("div", class_="error-alert")
    if error:
        result["erro"] = error.get_text(strip=True)
    return result


def parse_acompanha_documento(html: str, soup: BeautifulSoup) -> dict:
    result = {
        "tipo": "Acompanhe seu Documento",
        "dados": {},
        "html": html,
    }
    result["dados"].update(_extract_key_value_pairs(soup))
    tables = _extract_table_data(soup)
    if tables:
        result["tabelas"] = tables
    for div in soup.find_all("div", class_=["result-field", "documento-info"]):
        label = div.find("div", class_=["result-label", "info-label"])
        value = div.find("div", class_=["result-value", "info-value"])
        if label and value:
            result["dados"][label.get_text(strip=True)] = value.get_text(strip=True)
    error = soup.find("div", class_="error-alert")
    if error:
        result["erro"] = error.get_text(strip=True)
    return result