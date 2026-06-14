"""Gera comprovante PDF profissional a partir de ResultadoConsulta.

Design: layout compacto em pagina unica, identidade visual civic-moderna,
cards com borda colorida, badges de status semanticos, destaque visual
para informacoes criticas (placa, renavam, restricoes, boletos).
"""

import os
import uuid
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app import settings
from app.schemas import ResultadoConsulta

AZUL        = (37,  99,  235)
AZUL_ESCURO = (30,  58,  138)
AZUL_CLARO  = (219, 234, 254)
AZUL_BG     = (239, 246, 255)
CINZA_TEXT  = (100, 116, 139)
CINZA_LABEL = (148, 163, 184)
CINZA_BG    = (248, 250, 252)
CINZA_LINHA = (226, 232, 240)
BRANCO      = (255, 255, 255)
PRETO       = (15,  23,  42)
VERDE       = (22,  163,  74)
VERDE_BG    = (220, 252, 231)
VERDE_BORDER= (34,  197,  94)
VERMELHO    = (220,  38,  38)
VERMELHO_BG = (254, 226, 226)
VERMELHO_BORDER = (248, 113, 113)
LARANJA     = (234,  88,  12)
LARANJA_BG  = (255, 237, 213)
AMARELO_BG  = (254, 243,  199)
AMARELO_BORDER = (251, 191,  36)


def _t(s) -> str:
    return str(s).encode("latin-1", "replace").decode("latin-1")


def _cor_valor(valor: str) -> tuple:
    v = valor.lower()
    if any(w in v for w in (
        "pago", "normal", "ativo", "regular", "nada consta",
        "aprovado", "liberado", "ok", "quitado", "nenhuma", "0 pontos",
        "sem restricao", "sem restri", "nao consta",
    )):
        return VERDE
    if any(w in v for w in (
        "irregular", "vencido", "multa", "bloqueio", "bloqueado",
        "suspenso", "cassado", "cancelado", "apreendido", "impedido",
        "revogado", "expirado", "restricao", "gravame",
    )):
        return VERMELHO
    if any(w in v for w in (
        "aviso", "atencao", "atenc", "pendenc", "pendente",
        "aberto", "em aberto", "notificacao", "notificacao", "a vencer",
    )):
        return LARANJA
    return PRETO


def _cor_bg_valor(valor: str) -> tuple:
    v = valor.lower()
    if any(w in v for w in (
        "pago", "normal", "ativo", "regular", "nada consta",
        "aprovado", "liberado", "ok", "quitado", "nenhuma",
        "sem restricao", "sem restri", "nao consta",
    )):
        return VERDE_BG
    if any(w in v for w in (
        "irregular", "vencido", "multa", "bloqueio", "bloqueado",
        "suspenso", "cassado", "cancelado", "apreendido", "impedido",
        "revogado", "expirado", "restricao", "gravame",
    )):
        return VERMELHO_BG
    if any(w in v for w in (
        "aviso", "atencao", "atenc", "pendenc", "pendente",
        "aberto", "em aberto", "notificacao", "a vencer",
    )):
        return LARANJA_BG
    return BRANCO


def _tem_destaque_negativo(valor: str) -> bool:
    v = valor.lower()
    return any(w in v for w in (
        "irregular", "vencido", "multa", "bloqueio", "bloqueado",
        "suspenso", "cassado", "cancelado", "apreendido", "impedido",
        "revogado", "expirado", "restricao", "gravame",
    ))


class _PDF(FPDF):
    _consulta_titulo: str = ""
    _emitido_em: str = ""
    _protocolo: str = ""

    def header(self):
        self.set_fill_color(*AZUL_ESCURO)
        self.rect(0, 0, self.w, 20, "F")

        self.set_fill_color(*AZUL)
        self.rect(0, 17, self.w, 2, "F")

        self.set_xy(self.l_margin, 3)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*BRANCO)
        self.cell(0, 5, _t(self._consulta_titulo), align="L")

        self.set_xy(self.l_margin, 10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*AZUL_CLARO)
        self.cell(0, 4, _t(self._emitido_em), align="L")

        self.set_xy(0, 3)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*BRANCO)
        self.cell(self.w, 5, _t("DETRAN-PA"), align="C")

        self.set_xy(0, 9)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*AZUL_CLARO)
        self.cell(self.w, 4, _t("Comprovante de Consulta"), align="C")

        self.set_xy(self.l_margin, 14)
        self.set_font("Helvetica", "", 6)
        self.set_text_color(*AZUL_CLARO)
        self.cell(0, 3, _t(f"Protocolo: {self._protocolo}"), align="L")

        self.set_y(22)

    def footer(self):
        self.set_y(-12)
        self.set_draw_color(*CINZA_LINHA)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(1.5)
        self.set_font("Helvetica", "I", 5.5)
        self.set_text_color(*CINZA_TEXT)
        aviso = (
            "Documento gerado automaticamente. Dados obtidos diretamente do DETRAN-PA "
            "na data/hora da consulta. Nao tem valor fiscal."
        )
        self.cell(0, 3, _t(aviso), align="L")
        self.set_xy(-self.r_margin - 15, self.get_y() - 3)
        self.cell(15, 3, _t(f"Pag. {self.page_no()}"), align="R")


def _desenhar_badge(pdf: _PDF, texto: str, cor_texto: tuple, cor_bg: tuple, x: float, y: float, largura: float = 35):
    pdf.set_fill_color(*cor_bg)
    pdf.set_draw_color(*cor_texto)
    pdf.rect(x, y, largura, 5, "DF")
    pdf.set_xy(x + 1, y + 0.5)
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_text_color(*cor_texto)
    pdf.cell(largura - 2, 4, _t(texto), align="C")


def _circulo_status(pdf: _PDF, x: float, y: float, cor: tuple, raio: float = 1.5):
    pdf.set_fill_color(*cor)
    pdf.set_draw_color(*cor)
    pdf.ellipse(x - raio, y - raio, raio * 2, raio * 2, "DF")


def _card_identidade(pdf: _PDF, dados: dict, titulo: str):
    placa = dados.get("Placa") or dados.get("placa", "")
    renavam = dados.get("Renavam") or dados.get("renavam", "")
    marca = dados.get("Marca/Modelo") or dados.get("marca/Modelo", "")
    cor = dados.get("Cor") or dados.get("cor", "")
    ano_fab = dados.get("Ano Fabrica") or dados.get("Ano Fabricacao", "")
    ano_mod = dados.get("Ano Modelo") or dados.get("Ano Modelo", "")
    especie = dados.get("Especie") or dados.get("Especie", "")
    categoria = dados.get("Categoria") or dados.get("Categoria", "")

    y_start = pdf.get_y()
    pdf.set_fill_color(*AZUL_BG)
    pdf.set_draw_color(*AZUL)
    pdf.rect(pdf.l_margin, y_start, pdf.epw, 28, "DF")

    x0 = pdf.l_margin + 3
    pdf.set_xy(x0, y_start + 2)
    pdf.set_font("Helvetica", "", 6)
    pdf.set_text_color(*AZUL)
    pdf.cell(0, 3, _t(titulo.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if placa:
        pdf.set_xy(x0, y_start + 6)
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(*AZUL_ESCURO)
        pdf.cell(40, 8, _t(placa))
        if renavam:
            pdf.set_xy(x0 + 42, y_start + 7)
            pdf.set_font("Helvetica", "", 6)
            pdf.set_text_color(*CINZA_LABEL)
            pdf.cell(12, 3, _t("RENAVAM"))
            pdf.set_xy(x0 + 42, y_start + 10)
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(*PRETO)
            pdf.cell(50, 4, _t(renavam))

    y_info = y_start + 18
    pdf.set_xy(x0, y_info)
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(*CINZA_TEXT)

    info_parts = []
    if marca:
        info_parts.append(marca)
    if cor:
        info_parts.append(cor)
    if ano_fab or ano_mod:
        ano_txt = f"{ano_fab}/{ano_mod}" if ano_fab and ano_mod else (ano_fab or ano_mod)
        info_parts.append(ano_txt)
    if especie:
        info_parts.append(especie)
    if categoria:
        info_parts.append(categoria)

    if info_parts:
        pdf.cell(0, 3, _t("  |  ".join(info_parts)))

    pdf.set_y(y_start + 30)


def _secao_card(pdf: _PDF, titulo: str, conteudo: dict, cor_borda: tuple = AZUL, compacto: bool = False):
    if not conteudo:
        return

    y_start = pdf.get_y()
    needed = _calcular_altura_secao(pdf, conteudo, compacto)
    if y_start + needed > pdf.h - pdf.b_margin - 12:
        pdf.add_page()
        y_start = pdf.get_y()

    pdf.set_fill_color(*cor_borda)
    pdf.rect(pdf.l_margin, y_start, 2.5, 6, "F")

    x_titulo = pdf.l_margin + 4
    pdf.set_xy(x_titulo, y_start + 1)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.cell(0, 4, _t(titulo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    y_dados = y_start + 7
    _renderizar_kv(pdf, conteudo, y_dados, compacto)

    pdf.set_y(y_start + 7 + len(conteudo) * (4.5 if compacto else 5.5) + 2)


def _renderizar_kv(pdf: _PDF, conteudo: dict, y_start: float, compacto: bool = False):
    h_linha = 4.5 if compacto else 5.5
    font_kv = 7 if compacto else 7.5
    font_v = 7 if compacto else 7.5
    x_key = pdf.l_margin + 4
    larg_key = 38
    x_val = x_key + larg_key + 1
    larg_val = pdf.epw - larg_key - 5

    for i, (k, v) in enumerate(conteudo.items()):
        y = y_start + i * h_linha
        zebra = i % 2 == 1

        if zebra:
            pdf.set_fill_color(*CINZA_BG)
            pdf.rect(x_key - 1, y, larg_val + larg_key + 2, h_linha, "F")

        pdf.set_xy(x_key, y + (h_linha - 3.5) / 2)
        pdf.set_font("Helvetica", "B", font_kv)
        pdf.set_text_color(*CINZA_TEXT)
        pdf.cell(larg_key, 3.5, _t(k), align="L")

        cor = _cor_valor(str(v))
        cor_bg = _cor_bg_valor(str(v))

        if _tem_destaque_negativo(str(v)) or cor in (VERDE, VERMELHO, LARANJA):
            badge_larg = max(20, pdf.get_string_width(_t(str(v))) + 6)
            pdf.set_fill_color(*cor_bg)
            pdf.set_draw_color(*cor)
            x_badge = x_val
            badge_y = y + (h_linha - 4) / 2
            pdf.rect(x_badge, badge_y, badge_larg, 4, "DF")
            pdf.set_xy(x_badge + 1, badge_y + 0.3)
            pdf.set_font("Helvetica", "B", font_v - 0.5)
            pdf.set_text_color(*cor)
            pdf.cell(badge_larg - 2, 3.5, _t(str(v)), align="C")
        else:
            pdf.set_xy(x_val, y + (h_linha - 3.5) / 2)
            pdf.set_font("Helvetica", "", font_v)
            pdf.set_text_color(*PRETO)
            pdf.cell(larg_val, 3.5, _t(str(v)), align="L")


def _calcular_altura_secao(pdf: _PDF, conteudo: dict, compacto: bool = False) -> float:
    h_linha = 4.5 if compacto else 5.5
    return 7 + len(conteudo) * h_linha + 4


def _box_destaque(pdf: _PDF, label: str, valor: str, bg: tuple, cor_borda: tuple, icone: str = ""):
    pdf.ln(1)
    y_start = pdf.get_y()

    if y_start + 16 > pdf.h - pdf.b_margin - 12:
        pdf.add_page()
        y_start = pdf.get_y()

    pdf.set_fill_color(*bg)
    pdf.set_draw_color(*cor_borda)
    pdf.rect(pdf.l_margin, y_start, pdf.epw, 15, "DF")

    pdf.set_xy(pdf.l_margin + 3, y_start + 1)
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(*AZUL_ESCURO)
    label_text = icone + " " + label.upper() if icone else label.upper()
    pdf.cell(0, 3.5, _t(label_text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_xy(pdf.l_margin + 3, y_start + 5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.multi_cell(pdf.epw - 6, 5, _t(str(valor)))
    pdf.set_y(y_start + 17)


def _resumo_rapido(pdf: _PDF, dados: dict):
    campos_interesse = {
        "Situacao": ("Situacao", "Situacao"),
        "Situacao do Veiculo": ("Situacao", "Situacao do Veiculo"),
        "Restricao 1": ("Restricao", "Restricao 1"),
        "Restricao 2": ("Restricao", "Restricao 2"),
        "Restricao 3": ("Restricao", "Restricao 3"),
        "Restricao 4": ("Restricao", "Restricao 4"),
    }

    badges_y = pdf.get_y()
    x_pos = pdf.l_margin

    for campo, (tipo, chave) in campos_interesse.items():
        valor = dados.get(chave) or dados.get(campo)
        if valor is None:
            continue

        cor = _cor_valor(str(valor))
        if tipo == "Situacao":
            badge_text = f"{campo}: {valor}"
        else:
            badge_text = f"{valor}"

        larg = pdf.get_string_width(_t(badge_text)) + 8
        if x_pos + larg > pdf.w - pdf.r_margin:
            x_pos = pdf.l_margin
            badges_y += 6
            if badges_y > pdf.h - pdf.b_margin - 12:
                pdf.add_page()
                badges_y = pdf.get_y()

        _desenhar_badge(pdf, badge_text, cor, _cor_bg_valor(str(valor)), x_pos, badges_y, larg)
        x_pos += larg + 3

    if x_pos > pdf.l_margin:
        pdf.set_y(badges_y + 7)


def gerar_comprovante(resultado: ResultadoConsulta) -> tuple[str, str] | None:
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    protocolo = uuid.uuid4().hex[:12].upper()

    pdf = _PDF()
    pdf._consulta_titulo = resultado.titulo
    pdf._emitido_em = f"Emitido em {agora}"
    pdf._protocolo = protocolo
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(10, 10, 10)
    pdf.add_page()

    dados = resultado.dados or {}
    pulares = {"Linha Digitavel", "Linha Digitável", "Total"}
    total = dados.get("Total")

    dados_filtrados = {k: v for k, v in dados.items() if k not in pulares}

    campos_identidade = {
        "Placa", "placa", "Renavam", "renavam",
        "Marca/Modelo", "marca/Modelo",
        "Cor", "cor", "Ano Fabrica", "Ano Fabricacao", "Ano Modelo",
        "Especie", "Categoria",
    }
    dados_identidade = {}
    dados_resto = {}
    for k, v in dados_filtrados.items():
        if k in campos_identidade:
            dados_identidade[k] = v
        else:
            dados_resto[k] = v

    if dados_identidade:
        _card_identidade(pdf, dados_identidade, "Identificacao do Veiculo")

    if total:
        _box_destaque(pdf, "Valor Total", total, VERDE_BG, VERDE_BORDER, icone="[$]")

    _resumo_rapido(pdf, dados_filtrados)

    secoes_processadas = set()
    for nome, conteudo in resultado.secoes.items():
        if not conteudo:
            continue

        is_restricao = any(w in nome.lower() for w in ("restric", "penal", "multa", "bloque", "grav"))
        cor_borda = VERMELHO if is_restricao else AZUL
        compacto = len(conteudo) > 4

        _secao_card(pdf, nome, conteudo, cor_borda=cor_borda, compacto=compacto)
        secoes_processadas.add(nome)

        for k_sec in conteudo:
            dados_resto.pop(k_sec, None)

    if dados_resto:
        tem_negativo = any(_tem_destaque_negativo(str(v)) for v in dados_resto.values())
        cor_borda = VERMELHO if tem_negativo else AZUL
        compacto = len(dados_resto) > 6
        _secao_card(pdf, "Dados da Consulta", dados_resto, cor_borda=cor_borda, compacto=compacto)

    for tabela in resultado.tabelas:
        if not tabela:
            continue
        for i, linha_t in enumerate(tabela):
            cor_borda = VERMELHO if any(_tem_destaque_negativo(str(v)) for v in linha_t.values()) else AZUL
            _secao_card(pdf, f"Item {i+1}", linha_t, cor_borda=cor_borda, compacto=True)
            if i < len(tabela) - 1:
                pdf.ln(1)

    nome_arquivo = f"comprovante_{resultado.slug}_{uuid.uuid4().hex[:10]}.pdf"
    caminho = os.path.join(settings.STORAGE_DIR, nome_arquivo)
    pdf.output(caminho)
    return nome_arquivo, caminho