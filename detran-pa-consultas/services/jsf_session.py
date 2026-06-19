import re
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib.parse import urljoin
from urllib3.util.retry import Retry
from config import HEADERS, REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT, REQUEST_RETRIES
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JsfSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.verify = False
        retry = Retry(
            total=REQUEST_RETRIES,
            connect=REQUEST_RETRIES,
            read=REQUEST_RETRIES,
            status=REQUEST_RETRIES,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET", "HEAD", "OPTIONS"]),
            backoff_factor=1.5,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=8, pool_maxsize=8)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    @staticmethod
    def _timeout(read_timeout: float | None = None):
        return (REQUEST_CONNECT_TIMEOUT, read_timeout or REQUEST_READ_TIMEOUT)

    def _request(self, method: str, url: str, *, read_timeout: float | None = None, **kwargs):
        resp = self.session.request(
            method,
            url,
            timeout=self._timeout(read_timeout),
            **kwargs,
        )
        resp.raise_for_status()
        return resp

    @staticmethod
    def _build(resp) -> tuple[str, BeautifulSoup]:
        # O DETRAN-PA serve o HTML em UTF-8 (acentos como bytes UTF-8 e/ou
        # entidades HTML como &iacute;). Fixar explicitamente evita o fallback
        # latin-1 do requests quando algum endpoint nao manda charset no header.
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        # Remove glifos de icone (material-icons/symbols) que poluem o texto
        # extraido dos titulos de secao (ex: "personInformacoes do Proprietario").
        for icon in soup.select("i.material-icons, i.material-symbols-outlined, span.material-icons"):
            icon.decompose()
        return str(soup), soup

    def get_page(self, url: str) -> tuple[str, BeautifulSoup]:
        resp = self._request("GET", url)
        return self._build(resp)

    def submit_form(self, url: str, data: dict) -> tuple[str, BeautifulSoup]:
        resp = self._request("POST", url, data=data)
        return self._build(resp)

    @staticmethod
    def extract_viewstate(html: str) -> str | None:
        match = re.search(
            r'name="javax\.faces\.ViewState"[^>]*value="([^"]*)"', html
        )
        if not match:
            match = re.search(r'id="javax\.faces\.ViewState[^"]*"[^>]*value="([^"]*)"', html)
        return match.group(1) if match else None

    @staticmethod
    def extract_all_viewstates(html: str) -> list[str]:
        return re.findall(
            r'name="javax\.faces\.ViewState"[^>]*value="([^"]*)"', html
        )

    @staticmethod
    def extract_form_action(soup: BeautifulSoup, form_id: str) -> str | None:
        form = soup.find("form", {"id": form_id})
        if form:
            return form.get("action")
        return None

    @staticmethod
    def extract_form_action_from_html(html: str, form_id: str) -> str | None:
        soup = BeautifulSoup(html, "lxml")
        return JsfSession.extract_form_action(soup, form_id)

    def get_jsessionid(self) -> str | None:
        for cookie in self.session.cookies:
            if cookie.name == "JSESSIONID":
                return cookie.value
        return None

    def is_error_page(self, html: str) -> bool:
        return "Erro na Consulta" in html or "Ops! Ocorreu um Erro" in html

    def get_error_messages(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        messages = []
        for li in soup.select(".alert-messages li"):
            msg = li.get_text(strip=True)
            if msg:
                detail = li.find("span", class_="detail")
                if detail:
                    messages.append(detail.get_text(strip=True))
                else:
                    messages.append(msg)
        if not messages:
            # PrimeFaces error/warning detail messages
            for el in soup.select(".ui-messages-error-detail, .ui-messages-warn-detail"):
                msg = el.get_text(strip=True)
                if msg:
                    messages.append(msg)
        if not messages:
            for p in soup.select(".alert-title"):
                messages.append(p.get_text(strip=True))
        return messages

    def check_recaptcha_error(self, html: str) -> bool:
        return "Verifica" in html and "reCAPTCHA" in html and "inv" in html

    @staticmethod
    def extract_mcaptcha_sitekey(html: str) -> str | None:
        patterns = [
            r"mcaptcha\.detran\.pa\.gov\.br/widget\?sitekey=([^\"'&<>\s]+)",
            r"[?&]sitekey=([^\"'&<>\s]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def extract_recaptcha_sitekey(html: str) -> str | None:
        patterns = [
            r'data-sitekey=["\']([^"\']+)["\']',
            r'googlekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'sitekey["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, html, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @staticmethod
    def has_mcaptcha(html: str) -> bool:
        return "mcaptcha__token" in html or "mcaptcha.detran.pa.gov.br" in html

    def save_pdf(self, url: str, filepath: str, data: dict = None) -> bool:
        def persist(resp) -> bool:
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" in content_type.lower() or resp.content[:4] == b"%PDF":
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                return True
            return False

        if data:
            resp = self._request("POST", url, data=data, read_timeout=120)
        else:
            resp = self._request("GET", url, read_timeout=120)
        if persist(resp):
            return True

        # Alguns fluxos JSF retornam uma pagina intermediaria com link, iframe,
        # embed ou object apontando para o PDF real.
        content_type = resp.headers.get("Content-Type", "")
        if "html" not in content_type.lower() and b"<html" not in resp.content[:1024].lower():
            return False

        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        candidates: list[str] = []
        for tag in soup.find_all(["a", "iframe", "embed", "object"], href=True):
            candidates.append(tag.get("href"))
        for tag in soup.find_all(["iframe", "embed", "object"], src=True):
            candidates.append(tag.get("src"))
        for tag in soup.find_all("form", action=True):
            action = tag.get("action")
            text = tag.get_text(" ", strip=True).lower()
            if any(k in text for k in ("pdf", "boleto", "imprimir", "salvar")):
                candidates.append(action)

        seen: set[str] = set()
        for candidate in candidates:
            if not candidate:
                continue
            absolute = urljoin(resp.url, candidate)
            if absolute in seen:
                continue
            seen.add(absolute)
            if not any(k in absolute.lower() for k in ("pdf", "boleto", "impress", "download", "gerar")):
                continue
            try:
                pdf_resp = self._request("GET", absolute, read_timeout=120)
                if persist(pdf_resp):
                    return True
            except requests.RequestException:
                continue
        return False
