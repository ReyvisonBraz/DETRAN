import time
import base64
import requests
from config import TWOCAPTCHA_API_KEY, RECAPTCHA_SITE_KEY, CAPTCHA_TIMEOUT


class CaptchaSolver:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or TWOCAPTCHA_API_KEY
        self.base_url = "https://2captcha.com"

    def solve_recaptcha_v2(self, page_url: str, site_key: str = None) -> str:
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