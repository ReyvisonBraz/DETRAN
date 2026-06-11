import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.jsf_session import JsfSession
from services.captcha_solver import CaptchaSolver
from config import ENDPOINTS, RENACH_BASE
from parsers.renach_parser import parse_pontuacao_cnh, parse_portal_condutor
import requests


class RenachService:
    def __init__(self, captcha_solver: CaptchaSolver = None):
        self.jsf = JsfSession()
        self.captcha = captcha_solver or CaptchaSolver()

    def _get_captcha_image(self) -> bytes:
        jsessionid = self.jsf.get_jsessionid()
        url = ENDPOINTS["renach_imagem_captcha"]
        resp = self.jsf.session.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content

    def consulta_pontuacao_cnh(self, cpf: str) -> dict:
        url = ENDPOINTS["cnh_pontuacao"]
        html, soup = self.jsf.get_page(url)
        view_state = self.jsf.extract_viewstate(html)

        form_action = self.jsf.extract_form_action(soup, "formJSF")
        if not form_action:
            from services.jsf_session import JsfSession as J
            form_action = J.extract_form_action_from_html(html, "formJSF")

        if form_action and not form_action.startswith("http"):
            form_action = f"https://sistemas-renach.detran.pa.gov.br{form_action}"

        captcha_image = self._get_captcha_image()
        captcha_text = self.captcha.solve_image_captcha(captcha_image, maxlength=5)

        data = {
            "formJSF": "formJSF",
            "formJSF:cpf": cpf,
            "formJSF:senha": captcha_text,
            "javax.faces.ViewState": view_state,
            "formJSF:j_id_jsp_1697595030_8": "Confirmar",
        }
        html, soup = self.jsf.submit_form(form_action or url, data)
        return parse_pontuacao_cnh(html, soup)

    def portal_condutor(self, cpf: str, registro: str) -> dict:
        url = ENDPOINTS["portal_condutor"]
        html, soup = self.jsf.get_page(url)
        view_state = self.jsf.extract_viewstate(html)

        form_action = self.jsf.extract_form_action(soup, "formJSF")
        if form_action and not form_action.startswith("http"):
            form_action = f"https://sistemas-renach.detran.pa.gov.br{form_action}"

        captcha_image = self._get_captcha_image()
        captcha_text = self.captcha.solve_image_captcha(captcha_image, maxlength=5)

        data = {
            "formJSF": "formJSF",
            "formJSF:cpf": cpf,
            "formJSF:registro": registro,
            "formJSF:senha": captcha_text,
            "javax.faces.ViewState": view_state,
            "formJSF:j_id_jsp_1059182716_10": "Confirmar",
        }
        html, soup = self.jsf.submit_form(form_action or url, data)
        return parse_portal_condutor(html, soup)

    def certidao_negativa(self, cpf: str, modo: str = "emitir") -> dict:
        url = ENDPOINTS["certidao_negativa"]
        html, soup = self.jsf.get_page(url)
        view_state = self.jsf.extract_viewstate(html)

        form_action = self.jsf.extract_form_action(soup, "formJSF")
        if form_action and not form_action.startswith("http"):
            form_action = f"https://sistemas-renach.detran.pa.gov.br{form_action}"

        valor = "0" if modo == "emitir" else "1"

        data_etapa1 = {
            "formJSF": "formJSF",
            "formJSF:j_id_jsp_1898215000_4": valor,
            "javax.faces.ViewState": view_state,
            "formJSF:j_id_jsp_1898215000_7": "Confirmar",
        }
        html, soup = self.jsf.submit_form(form_action or url, data_etapa1)

        if modo == "emitir":
            captcha_image = self._get_captcha_image()
            captcha_text = self.captcha.solve_image_captcha(captcha_image, maxlength=5)

            view_state_2 = self.jsf.extract_viewstate(html)
            form_action_2 = self.jsf.extract_form_action(soup, "formJSF")
            if form_action_2 and not form_action_2.startswith("http"):
                form_action_2 = f"https://sistemas-renach.detran.pa.gov.br{form_action_2}"

            data_etapa2 = {
                "formJSF": "formJSF",
                "formJSF:cpf": cpf,
                "formJSF:senha": captcha_text,
                "javax.faces.ViewState": view_state_2,
                "formJSF:j_id_jsp_1898215000_7": "Confirmar",
            }
            html, soup = self.jsf.submit_form(form_action_2 or url, data_etapa2)

        return {"tipo": "Certidão Negativa", "html": html, "dados": {}}