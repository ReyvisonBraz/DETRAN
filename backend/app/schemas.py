"""Schemas (contratos) da API.

O ponto central e o ResultadoConsulta: TODA consulta, com sucesso ou erro,
retorna nesse mesmo formato. Assim o frontend tem um unico jeito de renderizar
resultado completo, parcial, com PDF ou com erro.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Resultado de uma consulta individual
# --------------------------------------------------------------------------- #

class StatusResultado(str, Enum):
    OK = "ok"                 # consulta retornou dados
    PARCIAL = "parcial"       # retornou alguns dados mas houve aviso/limite
    SEM_DADOS = "sem_dados"   # consulta ok, porem nada consta
    ERRO = "erro"             # falhou


class TipoErro(str, Enum):
    CAPTCHA = "captcha"         # CAPTCHA invalido/expirado -> retentavel
    VALIDACAO = "validacao"     # dado de entrada invalido (placa/renavam) -> NAO retentavel
    SISTEMA = "sistema"         # DETRAN fora do ar ou erro interno -> retentavel
    TIMEOUT = "timeout"         # demorou demais -> retentavel
    BLOQUEADO = "bloqueado"     # IP/sessao bloqueada -> exige acao
    SEM_RESULTADO = "sem_resultado"  # nada encontrado para os dados informados


class ErroDetalhe(BaseModel):
    tipo: TipoErro
    mensagem: str                       # mensagem amigavel ao cliente
    detalhe_tecnico: str | None = None  # para log/diagnostico (nao exibir ao cliente)
    retentavel: bool = False            # frontend pode oferecer "tentar novamente"


class Documento(BaseModel):
    tipo: str = "pdf"          # pdf | imagem
    nome: str                  # nome amigavel (ex: "Boleto Licenciamento 2026")
    url: str                   # endpoint de download na nossa API
    tamanho_bytes: int | None = None


class ResultadoConsulta(BaseModel):
    slug: str
    titulo: str
    status: StatusResultado
    # Pares chave/valor "achatados" (renderizacao simples)
    dados: dict[str, str] = Field(default_factory=dict)
    # Dados agrupados por secao (ex: "Restricoes", "Caracteristicas")
    secoes: dict[str, dict[str, str]] = Field(default_factory=dict)
    # Tabelas (ex: lista de infracoes)
    tabelas: list[list[dict[str, str]]] = Field(default_factory=list)
    documentos: list[Documento] = Field(default_factory=list)
    erro: ErroDetalhe | None = None
    executado_em: datetime = Field(default_factory=datetime.utcnow)
    duracao_seg: float | None = None


# --------------------------------------------------------------------------- #
# Jobs (uma ou varias consultas disparadas juntas - "lote")
# --------------------------------------------------------------------------- #

class StatusJob(str, Enum):
    FILA = "fila"
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"           # tudo ok
    CONCLUIDO_PARCIAL = "parcial"     # parte ok, parte com erro
    ERRO = "erro"                     # tudo falhou


class StatusItem(str, Enum):
    FILA = "fila"
    PROCESSANDO = "processando"
    OK = "ok"
    ERRO = "erro"


class ItemJob(BaseModel):
    slug: str
    titulo: str
    status: StatusItem = StatusItem.FILA
    resultado: ResultadoConsulta | None = None


class Job(BaseModel):
    job_id: str
    uid: str = ""
    status: StatusJob = StatusJob.FILA
    criado_em: datetime = Field(default_factory=datetime.utcnow)
    atualizado_em: datetime = Field(default_factory=datetime.utcnow)
    itens: list[ItemJob] = Field(default_factory=list)
    parametros: dict[str, str] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Entrada da API
# --------------------------------------------------------------------------- #

class ConsultaSelecionada(BaseModel):
    slug: str
    # Parametros especificos desta consulta; se vazio, usa os globais do job
    parametros: dict[str, str] = Field(default_factory=dict)


class CriarJobRequest(BaseModel):
    """Cliente marca varias consultas e dispara de uma vez.

    `parametros` traz os dados comuns (placa, renavam, cpf...). Cada item pode
    sobrescrever com parametros proprios.
    """

    consultas: list[ConsultaSelecionada]
    parametros: dict[str, str] = Field(default_factory=dict)


class CriarJobResponse(BaseModel):
    job_id: str
    status: StatusJob
    total: int
