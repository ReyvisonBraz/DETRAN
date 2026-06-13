"""Gera comprovante PDF profissional a partir de ResultadoConsulta.

Design: header com faixa de cor, secoes com titulo em bloco colorido,
linhas alternadas (zebra), valores coloridos por status semantico,
rodape com numero de pagina e aviso legal.
"""

import os
import uuid
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app import settings
from app.schemas import ResultadoConsulta

# ── Paleta ─────────────────────────────────────────────────────────────────
AZUL        = (37,  99,  235)   # primario
AZUL_ESCURO = (30,  58,  138)   # header / rodape
AZUL_CLARO  = (219, 234, 254)   # fundo secao
CINZA_TEXT  = (100, 116, 139)   # rotulos / muted
CINZA_BG    = (248, 250, 252)   # zebra par
BRANCO      = (255, 255, 255)
PRETO       = (15,  23,  42)    # texto principal
VERDE       = (22,  163,  74)   # ok / pago / regular
VERMELHO    = (220,  38,  38)   # irregular / bloqueado
LARANJA     = (234,  88,  12)   # pendente / aviso
AMARELO_BG  = (254, 243, 199)   # fundo alerta boleto


def _t(s) -> str:
    """Converte para latin-1 (fpdf core fonts)."""
    return str(s).encode("latin-1", "replace").decode("latin-1")


def _cor_valor(valor: str) -> tuple:
    v = valor.lower()
    if any(w in v for w in (
        "pago", "normal", "ativo", "regular", "nada consta",
        "aprovado", "liberado", "ok", "quitado", "nenhuma", "0 pontos",
    )):
        return VERDE
    if any(w in v for w in (
        "irregular", "vencido", "multa", "bloqueio", "bloqueado",
        "suspenso", "cassado", "cancelado", "apreendido", "impedido",
        "revogado", "expirado",
    )):
        return VERMELHO
    if any(w in v for w in (
        "aviso", "atencao", "atencão", "pendenc", "pendente",
        "aberto", "em aberto", "notificacao", "notificação", "a vencer",
    )):
        return LARANJA
    return PRETO


class _PDF(FPDF):
    _consulta_titulo: str = ""
    _emitido_em: str = ""

    # ── Header ──────────────────────────────────────────────────────────────
    def header(self):
        # Faixa superior escura
        self.set_fill_color(*AZUL_ESCURO)
        self.rect(0, 0, self.w, 26, "F")

        # Faixa inferior clara (detalhe)
        self.set_fill_color(*AZUL)
        self.rect(0, 22, self.w, 3, "F")

        # Icone / label "DETRAN-PA"
        self.set_xy(self.l_margin, 4)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*AZUL_CLARO)
        self.cell(40, 6, _t("DETRAN-PA"), align="L")

        # Titulo da consulta (centro)
        self.set_xy(0, 4)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*BRANCO)
        self.cell(self.w, 6, _t("Comprovante de Consulta"), align="C")

        # Data (direita)
        self.set_xy(self.w - self.r_margin - 55, 12)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*AZUL_CLARO)
        self.cell(55, 5, _t(self._emitido_em), align="R")

        self.ln(30)

    # ── Footer ──────────────────────────────────────────────────────────────
    def footer(self):
        self.set_y(-18)
        # Linha divisoria
        self.set_draw_color(*AZUL)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*CINZA_TEXT)
        aviso = (
            "Documento gerado automaticamente. Dados obtidos diretamente do DETRAN-PA "
            "na data/hora da consulta. Nao tem valor fiscal."
        )
        self.multi_cell(self.w - self.l_margin - self.r_margin - 20, 3.5, _t(aviso), align="L")
        self.set_xy(-self.r_margin - 20, self.get_y() - 3.5)
        self.cell(18, 3.5, _t(f"Pag. {self.page_no()}"), align="R")


# ── Helpers de layout ────────────────────────────────────────────────────────

def _titulo_secao(pdf: _PDF, texto: str):
    pdf.ln(3)
    # Bloco colorido (fundo azul claro, texto azul)
    pdf.set_fill_color(*AZUL_CLARO)
    pdf.set_draw_color(*AZUL)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.cell(
        pdf.epw, 7, "  " + _t(texto.upper()),
        fill=True, border="B",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(1)


def _linha_kv(pdf: _PDF, chave: str, valor: str, zebra: bool = False):
    # Fundo zebra
    if zebra:
        pdf.set_fill_color(*CINZA_BG)
    else:
        pdf.set_fill_color(*BRANCO)

    # Altura calculada (suporte a valores longos)
    pdf.set_font("Helvetica", "", 8.5)
    linhas_valor = max(1, len(str(valor)) // 52 + 1)
    h = max(6, 5 * linhas_valor)

    pdf.set_x(pdf.l_margin)
    # Coluna chave
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*CINZA_TEXT)
    pdf.cell(58, h, _t(chave), fill=True, border=0, new_x=XPos.RIGHT, new_y=YPos.TOP)

    # Separador
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*CINZA_TEXT)
    pdf.cell(4, h, ":", fill=zebra, new_x=XPos.RIGHT, new_y=YPos.TOP)

    # Coluna valor (colorida por semantica)
    cor = _cor_valor(str(valor))
    pdf.set_text_color(*cor)
    pdf.set_font("Helvetica", "B" if cor != PRETO else "", 8.5)
    largura = max(20, pdf.w - pdf.r_margin - pdf.get_x())
    pdf.multi_cell(
        largura, h,
        _t(str(valor)),
        fill=zebra,
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )


def _box_destaque(pdf: _PDF, label: str, valor: str, bg: tuple = AMARELO_BG):
    """Caixa grande para valores criticos (linha digitavel, total)."""
    pdf.ln(3)
    pdf.set_x(pdf.l_margin)

    # Label pequeno
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.cell(
        pdf.epw, 6, "  " + _t(label.upper()),
        fill=True, border="LTR",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )

    # Valor destaque
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(*bg)
    pdf.set_text_color(*AZUL_ESCURO)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(
        pdf.epw, 9, "  " + _t(str(valor)),
        fill=True, border="LBR",
        new_x=XPos.LMARGIN, new_y=YPos.NEXT,
    )
    pdf.ln(3)


def _separador(pdf: _PDF):
    pdf.set_draw_color(*AZUL_CLARO)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
    pdf.ln(2)


# ── Funcao principal ─────────────────────────────────────────────────────────

def gerar_comprovante(resultado: ResultadoConsulta) -> tuple[str, str] | None:
    """Renderiza o resultado em PDF. Retorna (nome_arquivo, caminho) ou None."""
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    pdf = _PDF()
    pdf._consulta_titulo = resultado.titulo
    pdf._emitido_em = f"Emitido em {agora}"
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    # ── Identificacao do documento ───────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*PRETO)
    pdf.cell(0, 8, _t(resultado.titulo), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CINZA_TEXT)
    pdf.cell(0, 5, _t(f"Emitido em {agora}  |  Protocolo: {uuid.uuid4().hex[:12].upper()}"),
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)
    _separador(pdf)

    # ── Destaques criticos ────────────────────────────────────────────────────
    dados = resultado.dados or {}
    linha_dig = dados.get("Linha Digitavel") or dados.get("Linha Digitável")
    total     = dados.get("Total")

    if linha_dig:
        _box_destaque(pdf, "Linha Digitavel — use para pagamento no banco ou app", linha_dig)
    if total:
        _box_destaque(pdf, "Valor Total", total, bg=(220, 252, 231))  # verde claro

    # ── Dados principais ─────────────────────────────────────────────────────
    pulares = {"Linha Digitavel", "Linha Digitável", "Total"}
    dados_filtrados = {k: v for k, v in dados.items() if k not in pulares}
    if dados_filtrados:
        _titulo_secao(pdf, "Dados da Consulta")
        for i, (k, v) in enumerate(dados_filtrados.items()):
            _linha_kv(pdf, k, v, zebra=(i % 2 == 1))

    # ── Secoes ───────────────────────────────────────────────────────────────
    for nome, conteudo in resultado.secoes.items():
        if not conteudo:
            continue
        _titulo_secao(pdf, nome)
        for i, (k, v) in enumerate(conteudo.items()):
            _linha_kv(pdf, k, v, zebra=(i % 2 == 1))

    # ── Tabelas ──────────────────────────────────────────────────────────────
    for tabela in resultado.tabelas:
        if not tabela:
            continue
        _titulo_secao(pdf, "Itens Detalhados")
        for i, linha_t in enumerate(tabela):
            if i:
                pdf.ln(2)
                _separador(pdf)
            for j, (k, v) in enumerate(linha_t.items()):
                _linha_kv(pdf, k, v, zebra=(j % 2 == 1))

    # ── Output ────────────────────────────────────────────────────────────────
    nome_arquivo = f"comprovante_{resultado.slug}_{uuid.uuid4().hex[:10]}.pdf"
    caminho = os.path.join(settings.STORAGE_DIR, nome_arquivo)
    pdf.output(caminho)
    return nome_arquivo, caminho
