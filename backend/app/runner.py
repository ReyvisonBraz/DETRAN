"""Executa uma consulta do catalogo e normaliza o resultado.

Responsabilidades:
  - chamar o metodo correto do motor com os parametros certos;
  - traduzir o dict cru do motor para ResultadoConsulta;
  - classificar erros (CAPTCHA, validacao, sistema, timeout...);
  - salvar PDFs/boletos e expor link de download.
"""

import os
import time
import uuid
import requests

from app import catalog, settings, pdf_generator
from app.engine_bridge import SistransitoService, RenachService, CaptchaSolver
from app.schemas import (
    ResultadoConsulta, StatusResultado, ErroDetalhe, TipoErro, Documento,
)


def _novo_solver() -> CaptchaSolver:
    return CaptchaSolver(api_key=settings.TWOCAPTCHA_API_KEY or None)


def _classificar_erro(exc: Exception) -> ErroDetalhe:
    msg = str(exc)
    low = msg.lower()
    if isinstance(exc, TimeoutError) or "timed out" in low or "timeout" in low:
        return ErroDetalhe(
            tipo=TipoErro.TIMEOUT,
            mensagem="A consulta demorou demais para responder. Tente novamente.",
            detalhe_tecnico=msg, retentavel=True,
        )
    if "recaptcha" in low or "captcha" in low:
        return ErroDetalhe(
            tipo=TipoErro.CAPTCHA,
            mensagem="Falha na verificacao de seguranca do DETRAN. Tente novamente.",
            detalhe_tecnico=msg, retentavel=True,
        )
    if isinstance(exc, requests.RequestException):
        return ErroDetalhe(
            tipo=TipoErro.SISTEMA,
            mensagem="O sistema do DETRAN esta indisponivel no momento.",
            detalhe_tecnico=msg, retentavel=True,
        )
    # DETRAN retorna "Atencao!!" para dados invalidos ou falha no captcha
    if "atencao" in low or "aten" in low or "erro na consulta" in low:
        return ErroDetalhe(
            tipo=TipoErro.SISTEMA,
            mensagem="O DETRAN retornou um aviso. Verifique se a placa e o Renavam estao corretos.",
            detalhe_tecnico=msg, retentavel=True,
        )
    if any(k in low for k in ("invalid", "obrigat", "placa", "renavam", "cpf")):
        return ErroDetalhe(
            tipo=TipoErro.VALIDACAO,
            mensagem="Verifique os dados informados e tente de novo.",
            detalhe_tecnico=msg, retentavel=False,
        )
    return ErroDetalhe(
        tipo=TipoErro.SISTEMA,
        mensagem="Nao foi possivel concluir a consulta.",
        detalhe_tecnico=msg, retentavel=True,
    )


def _stringify(v) -> str:
    return v if isinstance(v, str) else str(v)


def _normalizar(consulta: catalog.Consulta, bruto: dict, service) -> ResultadoConsulta:
    """Converte o dict cru do motor no envelope padrao."""
    res = ResultadoConsulta(
        slug=consulta.slug,
        titulo=consulta.titulo,
        status=StatusResultado.OK,
    )

    # Erro reportado pelo proprio parser
    if bruto.get("erro"):
        res.status = StatusResultado.ERRO
        res.erro = ErroDetalhe(
            tipo=TipoErro.SISTEMA,
            mensagem=_stringify(bruto["erro"]),
            retentavel=True,
        )
        return res

    # Dados achatados
    for k, v in (bruto.get("dados") or {}).items():
        if isinstance(v, dict):
            res.secoes[_stringify(k)] = {kk: _stringify(vv) for kk, vv in v.items()}
        else:
            res.dados[_stringify(k)] = _stringify(v)

    # Secoes ja agrupadas pelo parser
    for nome, conteudo in (bruto.get("secoes") or {}).items():
        if isinstance(conteudo, dict):
            res.secoes[_stringify(nome)] = {
                kk: _stringify(vv) for kk, vv in conteudo.items()
            }

    # Tabelas (infracoes e tabelas genericas)
    for chave in ("infracoes", "tabelas"):
        bloco = bruto.get(chave)
        if isinstance(bloco, list) and bloco:
            if bloco and isinstance(bloco[0], dict):
                res.tabelas.append([
                    {kk: _stringify(vv) for kk, vv in row.items()} for row in bloco
                ])
            elif bloco and isinstance(bloco[0], list):
                res.tabelas.extend(bloco)

    # "Nada consta" => sucesso, mas sem dados
    if bruto.get("nada_consta") and not res.dados and not res.tabelas:
        res.status = StatusResultado.SEM_DADOS

    # Documentos / PDF
    _anexar_documentos(consulta, bruto, service, res)

    if not res.dados and not res.tabelas and not res.documentos and not res.secoes:
        res.status = StatusResultado.SEM_DADOS

    return res


def _anexar_documentos(consulta, bruto, service, res: ResultadoConsulta):
    if not (consulta.gera_pdf or bruto.get("pdf_path") or bruto.get("pdf_link")):
        return

    destino_nome = f"{consulta.slug}_{uuid.uuid4().hex[:12]}.pdf"
    destino = os.path.join(settings.STORAGE_DIR, destino_nome)

    salvo = False
    # Caso o service ja tenha salvo
    if bruto.get("pdf_path") and os.path.exists(bruto["pdf_path"]):
        destino = bruto["pdf_path"]
        destino_nome = os.path.basename(destino)
        salvo = True
    # Senao, baixar pelo link usando a sessao autenticada do motor
    elif bruto.get("pdf_link"):
        try:
            salvo = service.jsf.save_pdf(bruto["pdf_link"], destino)
        except Exception:
            salvo = False

    if salvo and os.path.exists(destino):
        tamanho = os.path.getsize(destino)
        res.documentos.append(Documento(
            tipo="pdf",
            nome=f"{consulta.titulo}",
            url=f"/api/documentos/{destino_nome}",
            tamanho_bytes=tamanho,
        ))


# --------------------------------------------------------------------------- #
# Dispatch: slug -> chamada do motor com os parametros corretos
# --------------------------------------------------------------------------- #

def _exec_handler(consulta: catalog.Consulta, p: dict, salvar_pdf: str | None):
    solver = _novo_solver()
    h = consulta.handler

    if consulta.sistema == catalog.Sistema.RENACH:
        svc = RenachService(solver)
    else:
        svc = SistransitoService(solver)

    if h == "consulta_veiculo":
        bruto = svc.consulta_veiculo(p["placa"], p["renavam"])
    elif h == "consulta_infracoes":
        bruto = svc.consulta_infracoes(p["placa"], p["renavam"])
    elif h == "boleto_licenciamento_atual":
        bruto = svc.boleto_licenciamento_atual(p["placa"], p["renavam"], salvar_pdf=salvar_pdf)
    elif h == "boleto_licenciamento_anterior":
        bruto = svc.boleto_licenciamento_anterior(p["placa"], p["renavam"], salvar_pdf=salvar_pdf)
    elif h == "boleto_infracao":
        bruto = svc.boleto_infracao(p["placa"], p["renavam"], veiculo_para=True)
    elif h == "gravame":
        bruto = svc.gravame(p["chassi"])
    elif h == "crlv_e":
        bruto = svc.crlv_e(p["placa"], p["renavam"], p.get("cpf_cnpj", ""))
    elif h == "acompanha_documento":
        bruto = svc.acompanha_documento(
            renavam=p.get("renavam"),
            chassi=p.get("chassi"),
            no_boleto=p.get("no_boleto") or None,
            modo="C" if p.get("chassi") else "P",
        )
    elif h == "consulta_pontuacao_cnh":
        bruto = svc.consulta_pontuacao_cnh(p["cpf"])
    else:
        raise ValueError(f"Handler desconhecido: {h}")

    return bruto, svc


def executar(slug: str, parametros: dict) -> ResultadoConsulta:
    """Executa uma consulta e devolve sempre um ResultadoConsulta (nunca lanca)."""
    consulta = catalog.obter(slug)
    if not consulta:
        return ResultadoConsulta(
            slug=slug, titulo=slug, status=StatusResultado.ERRO,
            erro=ErroDetalhe(tipo=TipoErro.VALIDACAO,
                             mensagem="Consulta nao encontrada.", retentavel=False),
        )

    # Valida campos obrigatorios antes de gastar CAPTCHA
    faltando = [
        c.rotulo for c in consulta.entradas
        if c.obrigatorio and not (parametros.get(c.nome) or "").strip()
    ]
    if faltando:
        return ResultadoConsulta(
            slug=slug, titulo=consulta.titulo, status=StatusResultado.ERRO,
            erro=ErroDetalhe(
                tipo=TipoErro.VALIDACAO,
                mensagem=f"Preencha: {', '.join(faltando)}.",
                retentavel=False,
            ),
        )

    salvar_pdf = None
    if consulta.gera_pdf:
        salvar_pdf = os.path.join(
            settings.STORAGE_DIR, f"{slug}_{uuid.uuid4().hex[:12]}.pdf"
        )

    inicio = time.time()
    try:
        bruto, svc = _exec_handler(consulta, parametros, salvar_pdf)
        resultado = _normalizar(consulta, bruto, svc)
    except Exception as exc:  # noqa: BLE001 - queremos sempre devolver envelope
        resultado = ResultadoConsulta(
            slug=slug, titulo=consulta.titulo, status=StatusResultado.ERRO,
            erro=_classificar_erro(exc),
        )

    # Consultas sem PDF nativo (veiculo, multas, CNH) ganham um comprovante PDF
    # gerado pelo backend, para o cliente baixar.
    if resultado.status != StatusResultado.ERRO and not resultado.documentos:
        try:
            nome, caminho = pdf_generator.gerar_comprovante(resultado)
            resultado.documentos.append(Documento(
                tipo="pdf",
                nome=f"Comprovante - {resultado.titulo}",
                url=f"/api/documentos/{nome}",
                tamanho_bytes=os.path.getsize(caminho),
            ))
        except Exception:
            pass

    resultado.duracao_seg = round(time.time() - inicio, 1)
    return resultado
