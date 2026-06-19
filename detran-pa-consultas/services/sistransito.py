import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.jsf_session import JsfSession
from services.captcha_solver import CaptchaSolver
from config import ENDPOINTS
from parsers.sistransito_parser import (
    parse_veiculo_detalhada,
    parse_infracoes,
    parse_licenciamento,
    parse_acompanha_documento,
)
from bs4 import BeautifulSoup
import re


class SistransitoService:
    def __init__(self, captcha_solver: CaptchaSolver = None):
        self.jsf = JsfSession()
        self.captcha = captcha_solver or CaptchaSolver()

    def _get_page_state(self, url: str) -> tuple[str, BeautifulSoup]:
        html, soup = self.jsf.get_page(url)
        return html, soup

    def _solve_captcha_and_submit(
        self,
        page_url: str,
        form_action: str,
        form_data: dict,
        page_html: str,
        captcha_token: str = None,
    ) -> tuple[str, BeautifulSoup]:
        field, token = self.captcha.solve_for_page(page_url, page_html)
        form_data[field] = token

        html, soup = self.jsf.submit_form(form_action, form_data)
        if self.jsf.is_error_page(html) or self.jsf.check_recaptcha_error(html):
            errors = self.jsf.get_error_messages(html)
            raise RuntimeError(f"Erro na consulta: {errors}")
        return html, soup

    def consulta_veiculo(
        self, placa: str, renavam: str, captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["veiculo_detalhada"]
        html, soup = self._get_page_state(url)
        view_state = self.jsf.extract_viewstate(html)
        form_action = self.jsf.extract_form_action(soup, "indexRenavam")
        if not form_action:
            full_url = self.jsf.extract_form_action_from_html(html, "indexRenavam")
            form_action = full_url or url
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action.startswith("/") else form_action

        data = {
            "indexRenavam": "indexRenavam",
            "indexRenavam:placa1": placa.upper(),
            "indexRenavam:renavam": renavam,
            "javax.faces.ViewState": view_state,
            "indexRenavam:confirma": "Consultar Veículo",
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        return parse_veiculo_detalhada(html, soup)

    def consulta_infracoes(
        self, placa: str, renavam: str, captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["infracoes"]
        html, soup = self._get_page_state(url)
        view_state = self.jsf.extract_viewstate(html)
        form_action = self.jsf.extract_form_action(soup, "indexForm")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        data = {
            "indexForm": "indexForm",
            "placa": placa.upper(),
            "renavam": renavam,
            "javax.faces.ViewState": view_state,
            "confirma": "Confirmar",
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        return parse_infracoes(html, soup)

    def boleto_licenciamento_atual(
        self, placa: str, renavam: str, salvar_pdf: str = None, captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["licenciamento_atual"]
        html, soup = self._get_page_state(url)
        view_states = self.jsf.extract_all_viewstates(html)
        view_state = view_states[1] if len(view_states) > 1 else view_states[0]
        form_action = self.jsf.extract_form_action(soup, "indexBoletoAnoAtual")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        # Este form usa nomes de campo SEM o prefixo do form-id (placa1/renavam/
        # confirma), diferente da consulta de veiculo. Com prefixo, a placa e o
        # renavam chegam vazios e a pagina apenas recarrega o formulario.
        data = {
            "indexBoletoAnoAtual": "indexBoletoAnoAtual",
            "placa1": placa.upper(),
            "renavam": renavam,
            "javax.faces.ViewState": view_state,
            "confirma": "Consultar Orçamento",
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        result = parse_licenciamento(html, soup)

        # Etapa 3: a pagina de resultado tem o form "confirmacaoBoletoAnoAtual"
        # com o link "2a Via Boleto" (componente :segundaVia). Esse POST emite o
        # boleto e retorna a Linha Digitavel (o DETRAN-PA nao entrega PDF aqui;
        # o PDF/comprovante e gerado pelo backend a partir destes dados).
        boleto = self._emitir_boleto(html, soup, "confirmacaoBoletoAnoAtual", salvar_pdf)
        if boleto:
            result.setdefault("dados", {}).update(boleto.get("campos", {}))
            if boleto.get("pdf_path"):
                result["pdf_path"] = boleto["pdf_path"]
        return result

    @staticmethod
    def _abs_url(action: str) -> str:
        return (
            f"https://sistemas-renavam.detran.pa.gov.br{action}"
            if action.startswith("/") else action
        )

    def _emitir_boleto(
        self, html: str, soup: BeautifulSoup, form_id: str, salvar_pdf: str = None
    ) -> dict | None:
        """Fluxo do boleto em 2 POSTs:
        - etapa A ('2a Via Boleto' / :segundaVia) -> pagina com a Linha Digitavel;
        - etapa B ('Salvar Boleto' / :gerarBoleto) -> PDF do boleto.
        """
        form = soup.find("form", {"id": form_id})
        if not form:
            return None
        try:
            html3, soup3 = self.jsf.submit_form(
                self._abs_url(form.get("action") or ""),
                {
                    form_id: form_id,
                    f"{form_id}:segundaVia": f"{form_id}:segundaVia",
                    "javax.faces.ViewState": self.jsf.extract_viewstate(html),
                },
            )
        except Exception:
            return None

        campos = {}
        m = re.search(r"\b(\d{40,50})\b", soup3.get_text())
        if m:
            campos["Linha Digitável"] = m.group(1)
        if "gerado com sucesso" in html3.lower():
            campos["Situação"] = "Boleto gerado com sucesso"

        # Etapa B: botao "Salvar Boleto" (:gerarBoleto) retorna o PDF
        pdf_path = None
        form3 = soup3.find("form", {"id": form_id})
        if form3 and salvar_pdf:
            try:
                ok = self.jsf.save_pdf(
                    self._abs_url(form3.get("action") or ""),
                    salvar_pdf,
                    data={
                        form_id: form_id,
                        f"{form_id}:gerarBoleto": "Salvar Boleto",
                        "javax.faces.ViewState": self.jsf.extract_viewstate(html3),
                    },
                )
                if ok:
                    pdf_path = salvar_pdf
            except Exception:
                pdf_path = None

        return {"campos": campos, "pdf_path": pdf_path}

    def boleto_licenciamento_anterior(
        self, placa: str, renavam: str, salvar_pdf: str = None, captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["licenciamento_anterior"]
        html, soup = self._get_page_state(url)
        view_states = self.jsf.extract_all_viewstates(html)
        view_state = view_states[1] if len(view_states) > 1 else view_states[0]
        form_action = self.jsf.extract_form_action(soup, "indexBoletoAnoAnterior")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        data = {
            "indexBoletoAnoAnterior": "indexBoletoAnoAnterior",
            "indexBoletoAnoAnterior:placa1": placa.upper(),
            "indexBoletoAnoAnterior:renavam": renavam,
            "javax.faces.ViewState": view_state,
            "indexBoletoAnoAnterior:confirma": "Confirmar",
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        result = parse_licenciamento(html, soup)

        if salvar_pdf:
            pdf_links = soup.find_all("a", href=True)
            for link in pdf_links:
                href = link.get("href", "")
                if "pdf" in href.lower() or "boleto" in href.lower():
                    pdf_url = href if href.startswith("http") else f"https://sistemas-renavam.detran.pa.gov.br{href}"
                    if self.jsf.save_pdf(pdf_url, salvar_pdf):
                        result["pdf_path"] = salvar_pdf
                        break
        return result

    def boleto_infracao(
        self, placa: str, renavam: str, veiculo_para: bool = True, captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["boleto_infracao"]
        html, soup = self._get_page_state(url)
        view_state = self.jsf.extract_viewstate(html)

        form_action = self.jsf.extract_form_action(soup, "indexBoletoInfracao")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        tipo = "veiculosPara" if veiculo_para else "veiculosOutroEstado"
        data_etapa1 = {
            "indexBoletoInfracao": "indexBoletoInfracao",
            "indexBoletoInfracao:j_idt21": tipo,
            "javax.faces.ViewState": view_state,
            "indexBoletoInfracao:confirma": "Continuar",
        }
        html, soup = self.jsf.submit_form(full_action, data_etapa1)
        if self.jsf.is_error_page(html):
            errors = self.jsf.get_error_messages(html)
            raise RuntimeError(f"Erro na etapa 1: {errors}")

        if veiculo_para:
            form_action_2 = self.jsf.extract_form_action(soup, "indexBoletoInfracao")
        else:
            form_action_2 = self.jsf.extract_form_action(soup, "indexBoletoInfracao")

        if not form_action_2:
            form_action_2 = html
            match = re.search(r'action="([^"]*)"', html)
            if match:
                form_action_2 = match.group(1)

        full_action_2 = f"https://sistemas-renavam.detran.pa.gov.br{form_action_2}" if form_action_2.startswith("/") else form_action_2

        view_state_2 = self.jsf.extract_viewstate(html)

        data_etapa2 = {
            "indexBoletoInfracao": "indexBoletoInfracao",
            "indexBoletoInfracao:placa1": placa.upper(),
            "indexBoletoInfracao:renavam": renavam,
            "javax.faces.ViewState": view_state_2,
            "indexBoletoInfracao:confirma": "Confirmar",
        }
        if not veiculo_para:
            data_etapa2["indexBoletoInfracao:cpfCnpj"] = ""
            data_etapa2["indexBoletoInfracao:nomeCompleto"] = ""

        html, soup = self._solve_captcha_and_submit(
            ENDPOINTS["boleto_infracao"], full_action_2, data_etapa2, html, captcha_token
        )
        return parse_licenciamento(html, soup)

    def gravame(self, chassi: str, captcha_token: str = None) -> dict:
        url = ENDPOINTS["gravame"]
        html, soup = self._get_page_state(url)
        view_state = self.jsf.extract_viewstate(html)
        form_action = self.jsf.extract_form_action(soup, "indexGravame")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        data = {
            "indexGravame": "indexGravame",
            "indexGravame:chassi": chassi.upper(),
            "javax.faces.ViewState": view_state,
            "indexGravame:confirma": "Confirmar",
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        return self._parse_generic_result(html, soup, "Consulta Gravame")

    def crlv_e(self, placa: str, renavam: str, cpf_cnpj: str, captcha_token: str = None) -> dict:
        url = ENDPOINTS["crlv_e"]
        html, soup = self._get_page_state(url)
        view_state = self.jsf.extract_viewstate(html)
        form_action = self.jsf.extract_form_action(soup, "indexCRLVe")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        data = {
            "indexCRLVe": "indexCRLVe",
            "indexCRLVe:placa": placa.upper(),
            "indexCRLVe:renavam": renavam,
            "indexCRLVe:cpfCnpj": cpf_cnpj,
            "javax.faces.ViewState": view_state,
        }
        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        return self._parse_generic_result(html, soup, "CRLV-e")

    def acompanha_documento(
        self, renavam: str = None, chassi: str = None, no_boleto: str = None,
        modo: str = "P", captcha_token: str = None
    ) -> dict:
        url = ENDPOINTS["acompanha_documento"]
        html, soup = self._get_page_state(url)
        view_states = self.jsf.extract_all_viewstates(html)
        view_state = view_states[1] if len(view_states) > 1 else view_states[0]
        form_action = self.jsf.extract_form_action(soup, "indexAcompanhaDocumento")
        full_action = f"https://sistemas-renavam.detran.pa.gov.br{form_action}" if form_action and form_action.startswith("/") else form_action or url

        data = {
            "indexAcompanhaDocumento": "indexAcompanhaDocumento",
            "opcao": modo,
            "javax.faces.ViewState": view_state,
            "confirma": "Confirmar",
        }
        if modo == "P" and renavam:
            data["renavam"] = renavam
        elif modo == "C" and chassi:
            data["chassi"] = chassi.upper()
        if no_boleto:
            data["noBoleto"] = no_boleto

        html, soup = self._solve_captcha_and_submit(url, full_action, data, html, captcha_token)
        return parse_acompanha_documento(html, soup)

    def _parse_generic_result(self, html: str, soup: BeautifulSoup, title: str) -> dict:
        result = {"tipo": title, "dados": {}}
        result["html"] = html
        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        result["dados"][key] = value
        for div in soup.find_all("div", class_=["result-value", "data-value", "info-value"]):
            label = div.find_previous("div", class_=["result-label", "data-label", "info-label"])
            if label:
                result["dados"][label.get_text(strip=True)] = div.get_text(strip=True)
        if not result["dados"]:
            for p in soup.find_all("p"):
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    result["dados"]["mensagem"] = text
                    break
        return result
