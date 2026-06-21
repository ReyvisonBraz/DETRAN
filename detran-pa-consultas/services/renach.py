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

    @staticmethod
    def _find_submit_name(soup, form_id: str, submit_text: str = "Confirmar") -> str:
        """Localiza o name do botao submit dentro de um form JSF pelo texto ou value.
        
        Procura por <input type=submit> e <a> (links mojarra) com o texto desejado.
        Retorna o atributo 'name' do elemento encontrado, ou o JSP ID antigo como fallback.
        """
        form = soup.find("form", {"id": form_id})
        if form:
            for el in form.find_all(["input", "button", "a"]):
                if el.get("type") == "submit" or el.get("value") == submit_text or (el.name == "a" and submit_text in el.get_text()):
                    name = el.get("name") or el.get("id")
                    if name:
                        return name
        # Fallback: buscar no HTML inteiro
        for el in soup.find_all(["input", "button"]):
            if el.get("value") == submit_text:
                name = el.get("name") or el.get("id")
                if name:
                    return name
        return None

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

        # Localizar botao submit dinamicamente por value="Confirmar"
        submit_name = self._find_submit_name(soup, "formJSF", "Confirmar")
        if not submit_name:
            submit_name = "formJSF:j_id_jsp_1697595030_8"

        captcha_image = self._get_captcha_image()
        captcha_text = self.captcha.solve_image_captcha(captcha_image, maxlength=5)

        data = {
            "formJSF": "formJSF",
            "formJSF:cpf": cpf,
            "formJSF:senha": captcha_text,
            "javax.faces.ViewState": view_state,
            submit_name: "Confirmar",
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

        submit_name = self._find_submit_name(soup, "formJSF", "Confirmar")
        if not submit_name:
            submit_name = "formJSF:j_id_jsp_1059182716_10"

        data = {
            "formJSF": "formJSF",
            "formJSF:cpf": cpf,
            "formJSF:registro": registro,
            "formJSF:senha": captcha_text,
            "javax.faces.ViewState": view_state,
            submit_name: "Confirmar",
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

        # Localizar radio e submit da etapa 1 dinamicamente
        radio_name = None
        for radio in soup.find_all("input", {"type": "radio"}):
            radio_val = radio.get("value", "")
            if radio_val in ("0", "1"):
                radio_name = radio.get("name")
                break
        if not radio_name:
            radio_name = "formJSF:j_id_jsp_1898215000_4"

        submit_name_etapa1 = None
        form = soup.find("form", {"id": "formJSF"})
        if form:
            for el in form.find_all(["input", "button", "a"]):
                txt = el.get("value", "") or el.get_text(strip="")
                if "Confirmar" in txt:
                    submit_name_etapa1 = el.get("name") or el.get("id")
                    break
        if not submit_name_etapa1:
            submit_name_etapa1 = "formJSF:j_id_jsp_1898215000_7"

        data_etapa1 = {
            "formJSF": "formJSF",
            radio_name: valor,
            "javax.faces.ViewState": view_state,
            submit_name_etapa1: "Confirmar",
        }
        html, soup = self.jsf.submit_form(form_action or url, data_etapa1)

        if modo == "emitir":
            captcha_image = self._get_captcha_image()
            captcha_text = self.captcha.solve_image_captcha(captcha_image, maxlength=5)

            view_state_2 = self.jsf.extract_viewstate(html)
            form_action_2 = self.jsf.extract_form_action(soup, "formJSF")
            if form_action_2 and not form_action_2.startswith("http"):
                form_action_2 = f"https://sistemas-renach.detran.pa.gov.br{form_action_2}"

            submit_name_etapa2 = self._find_submit_name(soup, "formJSF", "Confirmar")
            if not submit_name_etapa2:
                submit_name_etapa2 = "formJSF:j_id_jsp_1898215000_7"

            data_etapa2 = {
                "formJSF": "formJSF",
                "formJSF:cpf": cpf,
                "formJSF:senha": captcha_text,
                "javax.faces.ViewState": view_state_2,
                submit_name_etapa2: "Confirmar",
            }
            html, soup = self.jsf.submit_form(form_action_2 or url, data_etapa2)

        return {"tipo": "Certidão Negativa", "html": html, "dados": {}}