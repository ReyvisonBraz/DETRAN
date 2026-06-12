"""Gera um comprovante PDF a partir de um ResultadoConsulta.

Como varias consultas do DETRAN-PA nao entregam um PDF (ex: licenciamento so
da a Linha Digitavel; veiculo/multas vem em HTML), o backend gera um comprovante
proprio, baixavel pelo cliente no navegador ou celular.
"""

import os
import uuid
from datetime import datetime

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from app import settings
from app.schemas import ResultadoConsulta

AZUL       = (37, 99, 235)
AZUL_CLARO = (219, 234, 254)
CINZA      = (100, 116, 139)
CINZA_BG   = (248, 250, 252)
PRETO      = (15, 23, 42)
VERDE      = (22, 163, 74)
VERMELHO   = (220, 38, 38)
LARANJA    = (234, 88, 12)


def _t(s) -> str:
    # Fontes core do fpdf usam latin-1 (cp1252), que cobre os acentos PT-BR.
    return str(s).encode("latin-1", "replace").decode("latin-1")


def _cor_valor(valor: str):
    """Retorna cor RGB baseada em palavras-chave de status."""
    v = valor.lower()
    if any(w in v for w in ("pago", "normal", "ativo", "regular", "nada consta",
                             "aprovado", "liberado", "ok", "quitado")):
        return VERDE
    if any(w in v for w in ("irregular", "vencido", "multa", "bloqueio", "bloqueado",
                             "suspenso", "cassado", "cancelado", "apreendido", "impedido")):
        return VERMELHO
    if any(w in v for w in ("aviso", "atencao", "atencao", "pendenc", "pendente",
                             "aberto", "em aberto", "notificacao", "notificacao")):
        return LARANJA
    return PRETO


class _PDF(FPDF):
    titulo_consulta = ""

    def header(self):
        self.set_fill_color(*AZUL)
        self.rect(0, 0, self.w, 22, "F")
        self.set_y(6)
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, _t("Comprovante de Consulta - DETRAN-PA"), align="L")
        self.ln(16)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*CINZA)
        msg = (
            "Documento gerado automaticamente. Os dados foram obtidos diretamente "
            "do sistema do DETRAN-PA na data/hora da consulta."
        )
        self.multi_cell(0, 4, _t(msg), align="C")
        self.cell(0, 4, _t(f"Pagina {self.page_no()}"), align="C")


def _titulo_secao(pdf: _PDF, texto: str):
    pdf.ln(3)
    pdf.set_fill_color(*AZUL_CLARO)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*AZUL)
    pdf.cell(pdf.epw, 8, "  " + _t(texto.upper()), fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_draw_color(*AZUL)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + pdf.epw, pdf.get_y())
    pdf.ln(1)


def _linha_kv(pdf: _PDF, chave: str, valor: str, zebra: bool = False):
    if zebra:
        pdf.set_fill_color(*CINZA_BG)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*CINZA)
    pdf.cell(58, 6, _t(chave), border=0, new_x=XPos.RIGHT, new_y=YPos.TOP, fill=zebra)
    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(*_cor_valor(valor))
    largura = max(20, pdf.w - pdf.r_margin - pdf.get_x())
    pdf.multi_cell(largura, 6, _t(valor), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=zebra)
    pdf.set_draw_color(226, 232, 240)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())


def _box_destaque(pdf: _PDF, titulo: str, valor: str):
    pdf.ln(2)
    pdf.set_x(pdf.l_margin)
    pdf.set_fill_color(239, 246, 255)
    pdf.set_draw_color(*AZUL)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*AZUL)
    pdf.multi_cell(pdf.epw, 6, _t(titulo), border=1, fill=True, align="L",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*PRETO)
    pdf.multi_cell(pdf.epw, 8, _t(valor), border="LRB", align="L",
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)


def gerar_comprovante(resultado: ResultadoConsulta) -> tuple[str, str] | None:
    """Renderiza o resultado em PDF. Retorna (nome_arquivo, caminho) ou None."""
    pdf = _PDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Cabecalho do documento
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(*PRETO)
    pdf.cell(0, 8, _t(resultado.titulo))
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(*CINZA)
    pdf.cell(0, 5, _t(f"Emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}"))
    pdf.ln(8)

    # Destaque para boleto (linha digitavel / total)
    boleto = getattr(resultado, "dados", {})
    linha = boleto.get("Linha Digitavel") or boleto.get("Linha Digitavel")
    if linha:
        _box_destaque(pdf, "LINHA DIGITAVEL (use para pagar)", linha)
    total = boleto.get("Total")
    if total:
        _box_destaque(pdf, "VALOR TOTAL", total)

    # Dados principais (exceto os ja destacados)
    pulares = {"Linha Digitavel", "Linha Digitavel", "Total"}
    dados = {k: v for k, v in resultado.dados.items() if k not in pulares}
    if dados:
        _titulo_secao(pdf, "Dados")
        for i, (k, v) in enumerate(dados.items()):
            _linha_kv(pdf, k, v, zebra=(i % 2 == 1))

    # Secoes
    for nome, conteudo in resultado.secoes.items():
        _titulo_secao(pdf, nome)
        for i, (k, v) in enumerate(conteudo.items()):
            _linha_kv(pdf, k, v, zebra=(i % 2 == 1))

    # Tabelas
    for tabela in resultado.tabelas:
        if not tabela:
            continue
        _titulo_secao(pdf, "Itens")
        for i, linha_t in enumerate(tabela):
            if i:
                pdf.ln(1)
            for j, (k, v) in enumerate(linha_t.items()):
                _linha_kv(pdf, k, v, zebra=(j % 2 == 1))

    nome_arquivo = f"comprovante_{resultado.slug}_{uuid.uuid4().hex[:10]}.pdf"
    caminho = os.path.join(settings.STORAGE_DIR, nome_arquivo)
    pdf.output(caminho)
    return nome_arquivo, caminho
