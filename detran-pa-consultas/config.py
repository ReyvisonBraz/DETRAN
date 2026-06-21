import os
from dotenv import load_dotenv

load_dotenv()

TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "")

MCAPTCHA_SITE_KEY = "pLmK1r0kfDWi26GT845rxZBaqdFo168p"

SISTRANSITO_BASE = "https://sistemas-renavam.detran.pa.gov.br/sistransito/detran-web"
RENACH_BASE = "https://sistemas-renach.detran.pa.gov.br/renach/renach-web"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)

CAPTCHA_TIMEOUT = int(os.getenv("CAPTCHA_TIMEOUT", "180"))
REQUEST_CONNECT_TIMEOUT = float(os.getenv("REQUEST_CONNECT_TIMEOUT", "10"))
REQUEST_READ_TIMEOUT = float(os.getenv("REQUEST_READ_TIMEOUT", "90"))
REQUEST_RETRIES = int(os.getenv("REQUEST_RETRIES", "2"))

ENDPOINTS = {
    "veiculo_detalhada": f"{SISTRANSITO_BASE}/servicos/veiculos/indexRenavam.jsf",
    "infracoes": f"{SISTRANSITO_BASE}/servicos/infracao/indexConsultaInfracao.jsf",
    "licenciamento_atual": f"{SISTRANSITO_BASE}/servicos/b/indexBLicencAnoAtual.jsf",
    "licenciamento_anterior": f"{SISTRANSITO_BASE}/servicos/b/indexBLicencAnoAnterior.jsf",
    "boleto_infracao": f"{SISTRANSITO_BASE}/servicos/b/indexBInfracao.jsf",
    "gravame": f"{SISTRANSITO_BASE}/servicos/veiculos/indexSNG.jsf",
    "crlv_e": f"{SISTRANSITO_BASE}/servicos/crlv/indexCRLVe.jsf",
    "acompanha_documento": f"{SISTRANSITO_BASE}/servicos/veiculos/indexAcompanhaDocumento.jsf",
    "edital_infracao": f"{SISTRANSITO_BASE}/servicos/veiculos/indexEdital.jsf",
    "cnh_pontuacao": f"{RENACH_BASE}/servicos/consultaPontuacao/indexConsultaPontuacao.jsf",
    "portal_condutor": f"{RENACH_BASE}/servicos/portalCondutor/indexPortalCondutor.jsf",
    "certidao_negativa": f"{RENACH_BASE}/servicos/certidaoNegativa/indexCertidaoNegativa.jsf",
    "renach_imagem_captcha": f"{RENACH_BASE}/imagem",
}

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}
