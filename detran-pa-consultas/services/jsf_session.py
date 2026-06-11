import re
import requests
from bs4 import BeautifulSoup
from config import HEADERS
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JsfSession:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.session.verify = False

    def get_page(self, url: str) -> tuple[str, BeautifulSoup]:
        resp = self.session.get(url, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return resp.text, soup

    def submit_form(self, url: str, data: dict) -> tuple[str, BeautifulSoup]:
        resp = self.session.post(url, data=data, timeout=60)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return resp.text, soup

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
            for p in soup.select(".alert-title"):
                messages.append(p.get_text(strip=True))
        return messages

    def check_recaptcha_error(self, html: str) -> bool:
        return "Verifica" in html and "reCAPTCHA" in html and "inv" in html

    def save_pdf(self, url: str, filepath: str, data: dict = None) -> bool:
        if data:
            resp = self.session.post(url, data=data, timeout=60)
        else:
            resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if "pdf" in content_type or resp.content[:4] == b"%PDF":
            with open(filepath, "wb") as f:
                f.write(resp.content)
            return True
        return False