import time
import struct
import hashlib
import base64
import re
import requests
from config import TWOCAPTCHA_API_KEY, RECAPTCHA_SITE_KEY, CAPTCHA_TIMEOUT

MCAPTCHA_BASE_URL = "https://mcaptcha.detran.pa.gov.br"


class ManualCaptchaRequired(RuntimeError):
    def __init__(self, captcha_type: str, site_key: str | None, page_url: str):
        self.captcha_type = captcha_type
        self.site_key = site_key
        self.page_url = page_url
        detail = f" sitekey={site_key}" if site_key else ""
        super().__init__(
            f"{captcha_type} exige validacao humana no navegador.{detail} url={page_url}"
        )


class CaptchaSolver:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TWOCAPTCHA_API_KEY
        self.base_url = "https://2captcha.com"

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

    def solve_for_page(self, page_url: str, html: str) -> tuple[str, str]:
        if "mcaptcha__token" in html or "mcaptcha.detran.pa.gov.br" in html:
            site_key = self.extract_mcaptcha_sitekey(html)
            token = self.solve_mcaptcha(site_key or "pLmK1r0kfDWi26GT845rxZBaqdFo168p")
            return "mcaptcha__token", token

        site_key = self.extract_recaptcha_sitekey(html) or RECAPTCHA_SITE_KEY
        return "g-recaptcha-response", self.solve_recaptcha_v2(page_url, site_key)

    def solve_mcaptcha(self, site_key: str) -> str:
        config_resp = requests.post(
            f"{MCAPTCHA_BASE_URL}/api/v1/pow/config",
            json={"key": site_key},
            timeout=30,
            verify=False,
        )
        config_resp.raise_for_status()
        config = config_resp.json()

        challenge = config["string"]
        difficulty_factor = config["difficulty_factor"]
        salt = config["salt"]

        prefix = salt.encode("utf-8") + struct.pack("<Q", len(challenge.encode("utf-8"))) + challenge.encode("utf-8")

        threshold = (2**128 - 1) - (2**128 - 1) // difficulty_factor

        nonce = 0
        result_int = 0
        while nonce < 500_000_000:
            nonce += 1
            hash_bytes = hashlib.sha256(prefix + str(nonce).encode("utf-8")).digest()
            hash_int = int.from_bytes(hash_bytes[:16], "big")
            if hash_int >= threshold:
                result_int = hash_int
                break

        if result_int == 0:
            raise RuntimeError("mCaptcha: nonce nao encontrado dentro do limite")

        verify_resp = requests.post(
            f"{MCAPTCHA_BASE_URL}/api/v1/pow/verify",
            json={
                "key": site_key,
                "string": challenge,
                "nonce": nonce,
                "result": str(result_int),
                "difficulty_factor": difficulty_factor,
            },
            timeout=30,
            verify=False,
        )
        verify_resp.raise_for_status()
        data = verify_resp.json()
        token = data.get("token")
        if not token:
            raise RuntimeError(f"mCaptcha: erro na verificacao: {verify_resp.text}")
        return token

    def solve_recaptcha_v2(self, page_url: str, site_key: str = None) -> str:
        if not self.api_key:
            raise RuntimeError("TWOCAPTCHA_API_KEY nao configurada para resolver reCAPTCHA")
        sitekey = site_key or RECAPTCHA_SITE_KEY
        resp = requests.post(f"{self.base_url}/in.php", data={
            "key": self.api_key,
            "method": "userrecaptcha",
            "googlekey": sitekey,
            "pageurl": page_url,
            "json": 1,
        }, timeout=30)
        result = resp.json()
        if result.get("status") != 1:
            raise RuntimeError(f"2Captcha submit error: {result.get('request', 'unknown')}")
        task_id = result["request"]
        return self._poll_result(task_id)

    def solve_image_captcha(self, image_bytes: bytes, maxlength: int = 5) -> str:
        if not self.api_key:
            raise RuntimeError("TWOCAPTCHA_API_KEY nao configurada para resolver CAPTCHA de imagem")
        b64 = base64.b64encode(image_bytes).decode()
        resp = requests.post(f"{self.base_url}/in.php", data={
            "key": self.api_key,
            "method": "base64",
            "body": b64,
            "maxlength": maxlength,
            "numeric": 0,
            "json": 1,
        }, timeout=30)
        result = resp.json()
        if result.get("status") != 1:
            raise RuntimeError(f"2Captcha submit error: {result.get('request', 'unknown')}")
        task_id = result["request"]
        return self._poll_result(task_id)

    def solve_image_captcha_from_url(self, url: str, cookies: dict = None, maxlength: int = 5) -> str:
        session = requests.Session()
        if cookies:
            for name, value in cookies.items():
                session.cookies.set(name, value)
        resp = session.get(url, timeout=30)
        resp.raise_for_status()
        return self.solve_image_captcha(resp.content, maxlength)

    def _poll_result(self, task_id: str) -> str:
        start = time.time()
        while time.time() - start < CAPTCHA_TIMEOUT:
            time.sleep(5)
            resp = requests.get(f"{self.base_url}/res.php", params={
                "key": self.api_key,
                "action": "get",
                "id": task_id,
                "json": 1,
            }, timeout=30)
            result = resp.json()
            if result.get("status") == 1:
                return result["request"]
            if result.get("request") != "CAPCHA_NOT_READY":
                raise RuntimeError(f"2Captcha solve error: {result.get('request', 'unknown')}")
        raise TimeoutError("2Captcha solve timed out")
