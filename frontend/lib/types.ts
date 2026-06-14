// Espelha os schemas do backend (app/schemas.py e catalog.py)

export interface CampoEntrada {
  nome: string;
  rotulo: string;
  tipo: string;
  obrigatorio: boolean;
  mascara: string | null;
  ajuda: string | null;
}

export interface Consulta {
  slug: string;
  titulo: string;
  descricao: string;
  categoria: "veiculo" | "habilitacao" | "boleto";
  sistema: string;
  handler: string;
  entradas: CampoEntrada[];
  gera_pdf: boolean;
  gera_boleto: boolean;
  requer_captcha: boolean;
  multi_etapa: boolean;
  creditos: number;
  tempo_estimado_seg: number;
  ativo: boolean;
}

export type StatusResultado = "ok" | "parcial" | "sem_dados" | "erro";
export type TipoErro =
  | "captcha" | "validacao" | "sistema" | "timeout" | "bloqueado" | "sem_resultado";

export interface ErroDetalhe {
  tipo: TipoErro;
  mensagem: string;
  detalhe_tecnico: string | null;
  retentavel: boolean;
}

export interface Documento {
  tipo: string;
  nome: string;
  url: string;
  tamanho_bytes: number | null;
}

export interface ResultadoConsulta {
  slug: string;
  titulo: string;
  status: StatusResultado;
  dados: Record<string, string>;
  secoes: Record<string, Record<string, string>>;
  tabelas: Record<string, string>[][];
  documentos: Documento[];
  erro: ErroDetalhe | null;
  executado_em: string;
  duracao_seg: number | null;
}

export type StatusItem = "fila" | "processando" | "ok" | "erro";
export type StatusJob = "fila" | "processando" | "concluido" | "parcial" | "erro";

export interface ItemJob {
  slug: string;
  titulo: string;
  status: StatusItem;
  resultado: ResultadoConsulta | null;
}

export interface Job {
  job_id: string;
  status: StatusJob;
  criado_em: string;
  atualizado_em: string;
  itens: ItemJob[];
  parametros: Record<string, string>;
}

export interface CriarJobResponse {
  job_id: string;
  status: StatusJob;
  total: number;
}

// ── Auth & Users ──

export type UserRole = "cliente" | "admin";

export interface UserProfile {
  uid: string;
  email: string;
  nome: string;
  sobrenome: string;
  telefone: string | null;
  fotoURL: string | null;
  role: UserRole;
  saldoCreditos: number;
  totalConsultas: number;
  createdAt: string;
  updatedAt: string;
  perfilCompleto: boolean;
}

// ── Créditos & Transações ──

export type TipoTransacao = "recarga" | "consumo" | "reembolso" | "bonus";
export type StatusTransacao = "pendente" | "confirmado" | "cancelado" | "estornado";
export type MetodoPagamento = "pix" | "cartao_credito" | "cartao_debito" | "mercado_pago" | "bonus" | "admin";

export interface Transacao {
  id: string;
  uid: string;
  tipo: TipoTransacao;
  creditos: number;
  valorReais: number | null;
  descricao: string;
  metodoPagamento: MetodoPagamento | null;
  status: StatusTransacao;
  pagamentoId: string | null;
  jobId: string | null;
  createdAt: string;
  confirmedAt: string | null;
}

export interface PacoteCreditos {
  id: string;
  creditos: number;
  preco: number;
  titulo: string;
}

// ── Pagamentos ──

export type StatusPagamento = "aguardando" | "pago" | "cancelado" | "estornado";

export interface Pagamento {
  id: string;
  uid: string;
  gateway: "mercado_pago";
  gatewayId: string;
  tipo: "pix" | "cartao_credito" | "cartao_debito";
  valor: number;
  creditos: number;
  status: StatusPagamento;
  pixQrCode: string | null;
  pixCopiaCola: string | null;
  pixExpiracao: string | null;
  createdAt: string;
  pagoEm: string | null;
}
