"""Catalogo de consultas do DETRAN-PA.

Esta e a fonte unica de verdade do produto. Cada consulta descreve, em
linguagem do cliente, o que faz, quais dados precisa, o que entrega
(PDF/boleto), se pode falhar por CAPTCHA e quanto custa em creditos.

O frontend monta a tela de selecao e os formularios a partir daqui, e o
runner usa o campo `handler` para saber qual metodo do motor executar.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum


class Categoria(str, Enum):
    VEICULO = "veiculo"
    HABILITACAO = "habilitacao"
    BOLETO = "boleto"


class Sistema(str, Enum):
    SISTRANSITO = "sistransito"
    RENACH = "renach"


@dataclass
class CampoEntrada:
    """Um campo de formulario que o cliente precisa preencher."""

    nome: str                      # chave enviada na requisicao (ex: "placa")
    rotulo: str                    # texto exibido (ex: "Placa do veiculo")
    tipo: str = "texto"            # texto | cpf | cnpj | placa | renavam | chassi
    obrigatorio: bool = True
    mascara: str | None = None     # dica de formato (ex: "AAA0A00")
    ajuda: str | None = None       # texto auxiliar curto


@dataclass
class Consulta:
    slug: str                      # identificador estavel (ex: "veiculo_detalhada")
    titulo: str                    # nome curto exibido
    descricao: str                 # "o que faz", em linguagem do cliente
    categoria: Categoria
    sistema: Sistema
    handler: str                   # nome do metodo no runner
    entradas: list[CampoEntrada] = field(default_factory=list)
    gera_pdf: bool = False         # entrega documento PDF ao cliente
    gera_boleto: bool = False      # gera boleto de pagamento
    requer_captcha: bool = True    # passa por CAPTCHA (pode falhar/retentar)
    multi_etapa: bool = False      # fluxo com mais de um passo no DETRAN
    creditos: int = 1              # custo placeholder (precificacao futura)
    tempo_estimado_seg: int = 45   # estimativa p/ a UX (barra de progresso)
    ativo: bool = True             # permite desligar uma consulta sem remover

    def to_dict(self) -> dict:
        d = asdict(self)
        d["categoria"] = self.categoria.value
        d["sistema"] = self.sistema.value
        return d


# Campos reutilizados
_PLACA = CampoEntrada("placa", "Placa do veiculo", tipo="placa", mascara="AAA0A00")
_RENAVAM = CampoEntrada("renavam", "Renavam", tipo="renavam", mascara="00000000000",
                        ajuda="11 digitos, com zeros a esquerda")
_CPF = CampoEntrada("cpf", "CPF", tipo="cpf", mascara="000.000.000-00")
_CHASSI = CampoEntrada("chassi", "Chassi", tipo="chassi")


CATALOGO: list[Consulta] = [
    Consulta(
        slug="veiculo_detalhada",
        titulo="Consulta Veiculo Detalhada",
        descricao=(
            "Situacao completa do veiculo: dados cadastrais, restricoes "
            "administrativas e judiciais, e caracteristicas. Use para saber "
            "se ha bloqueios, roubo/furto ou pendencias no veiculo."
        ),
        categoria=Categoria.VEICULO,
        sistema=Sistema.SISTRANSITO,
        handler="consulta_veiculo",
        entradas=[_PLACA, _RENAVAM],
        creditos=2,
    ),
    Consulta(
        slug="infracoes",
        titulo="Consulta de Infracoes / Multas",
        descricao=(
            "Lista as multas e infracoes vinculadas ao veiculo, com datas, "
            "valores e situacao de cada uma."
        ),
        categoria=Categoria.VEICULO,
        sistema=Sistema.SISTRANSITO,
        handler="consulta_infracoes",
        entradas=[_PLACA, _RENAVAM],
        creditos=2,
    ),
    Consulta(
        slug="licenciamento_atual",
        titulo="Boleto Licenciamento (Ano Atual)",
        descricao=(
            "Gera o boleto do licenciamento do ano vigente. Entrega o PDF "
            "pronto para pagamento."
        ),
        categoria=Categoria.BOLETO,
        sistema=Sistema.SISTRANSITO,
        handler="boleto_licenciamento_atual",
        entradas=[_PLACA, _RENAVAM],
        gera_pdf=True,
        gera_boleto=True,
        creditos=1,
    ),
    Consulta(
        slug="licenciamento_anterior",
        titulo="Boleto Licenciamento (Ano Anterior)",
        descricao="Gera o boleto de licenciamento de anos anteriores em aberto.",
        categoria=Categoria.BOLETO,
        sistema=Sistema.SISTRANSITO,
        handler="boleto_licenciamento_anterior",
        entradas=[_PLACA, _RENAVAM],
        gera_pdf=True,
        gera_boleto=True,
        creditos=1,
    ),
    Consulta(
        slug="boleto_infracao",
        titulo="Boleto de Infracao",
        descricao=(
            "Emite o boleto para pagamento de multas do veiculo (veiculos "
            "emplacados no Para)."
        ),
        categoria=Categoria.BOLETO,
        sistema=Sistema.SISTRANSITO,
        handler="boleto_infracao",
        entradas=[_PLACA, _RENAVAM],
        gera_pdf=True,
        gera_boleto=True,
        multi_etapa=True,
        creditos=1,
    ),
    Consulta(
        slug="gravame",
        titulo="Consulta Gravame",
        descricao=(
            "Mostra se ha gravame (financiamento/alienacao fiduciaria) "
            "registrado no veiculo, pelo numero do chassi."
        ),
        categoria=Categoria.VEICULO,
        sistema=Sistema.SISTRANSITO,
        handler="gravame",
        entradas=[_CHASSI],
        creditos=2,
    ),
    Consulta(
        slug="crlv_e",
        titulo="Emissao CRLV-e",
        descricao=(
            "Emite o documento eletronico do veiculo (CRLV-e) em PDF, "
            "quando o licenciamento esta em dia."
        ),
        categoria=Categoria.VEICULO,
        sistema=Sistema.SISTRANSITO,
        handler="crlv_e",
        entradas=[
            _PLACA,
            _RENAVAM,
            CampoEntrada("cpf_cnpj", "CPF ou CNPJ do proprietario", tipo="cpf"),
        ],
        gera_pdf=True,
        creditos=2,
    ),
    Consulta(
        slug="acompanha_documento",
        titulo="Acompanhe seu Documento",
        descricao=(
            "Acompanha o andamento de documentos/processos do veiculo "
            "(por Renavam ou Chassi)."
        ),
        categoria=Categoria.VEICULO,
        sistema=Sistema.SISTRANSITO,
        handler="acompanha_documento",
        entradas=[
            _RENAVAM,
            CampoEntrada("no_boleto", "Numero do boleto", obrigatorio=False,
                         ajuda="Opcional; vazio busca o ultimo"),
        ],
        creditos=1,
    ),
    Consulta(
        slug="cnh_pontuacao",
        titulo="Consulta Pontuacao CNH",
        descricao=(
            "Mostra a pontuacao atual da carteira de habilitacao e as "
            "infracoes que geraram pontos, pelo CPF do condutor."
        ),
        categoria=Categoria.HABILITACAO,
        sistema=Sistema.RENACH,
        handler="consulta_pontuacao_cnh",
        entradas=[_CPF],
        creditos=2,
    ),
]


_POR_SLUG: dict[str, Consulta] = {c.slug: c for c in CATALOGO}


def listar(incluir_inativos: bool = False) -> list[Consulta]:
    return [c for c in CATALOGO if incluir_inativos or c.ativo]


def obter(slug: str) -> Consulta | None:
    return _POR_SLUG.get(slug)
