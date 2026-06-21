"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { obterJob, urlDocumento } from "@/lib/api";
import type { Job, ItemJob, ResultadoConsulta, TipoErro } from "@/lib/types";
import { doc, setDoc, updateDoc, increment, serverTimestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useAuth } from "@/lib/auth";

const FeedbackWidget = dynamic(() => import("@/components/FeedbackWidget"), { ssr: false });
const Toast = dynamic(() => import("@/components/Toast"), { ssr: false });

const STATUS_FINAL = new Set(["concluido", "parcial", "erro"]);

// Erros causados por falha do sistema (não do usuário) → elegíveis para estorno
const ERROS_SISTEMA = new Set(["captcha", "sistema", "timeout", "bloqueado", "_desconhecido"]);

const ERRO_CONFIG: Record<string, { titulo: string; descricao: string; icone: JSX.Element; cor: string; retentar: boolean }> = {
captcha: {
titulo: "Falha na verificacao de seguranca",
descricao: "O sistema do DETRAN-PA exige um CAPTCHA que nao pudemos resolver automaticamente. Isso acontece quando o site esta com muito acesso ou quando o CAPTCHA expira rapidamente.",
cor: "amber",
retentar: true,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
</svg>
),
},
validacao: {
titulo: "Dados invalidos",
descricao: "Os dados informados nao sao validados pelo DETRAN-PA. Verifique se a placa, RENAVAM ou CPF estao corretos e tente novamente.",
cor: "rose",
retentar: false,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>
),
},
sistema: {
titulo: "Sistema do DETRAN indisponivel",
descricao: "O site do DETRAN-PA esta fora do ar, lento ou retornando erros. Isso e comum em horarios de pico ou quando o sistema esta em manutencao. Tente novamente em alguns minutos.",
cor: "amber",
retentar: true,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
),
},
timeout: {
titulo: "Tempo esgotado",
descricao: "A consulta demorou demais e ultrapassou o limite de tempo. O DETRAN-PA pode estar congestionado. Tente novamente — geralmente funciona na segunda tentativa.",
cor: "amber",
retentar: true,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
),
},
bloqueado: {
titulo: "Acesso bloqueado pelo DETRAN",
descricao: "O DETRAN-PA bloqueou temporariamente o acesso por excesso de consultas. Aguarde alguns minutos (geralmente 5-10 min) antes de tentar novamente.",
cor: "rose",
retentar: true,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
),
},
sem_resultado: {
titulo: "Nenhum resultado encontrado",
descricao: "O DETRAN-PA nao retornou dados para os dados informados. Verifique se a placa ou RENAVAM estao corretos e se o veiculo esta registrado no Estado do Para.",
cor: "muted",
retentar: false,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
<line x1="8" y1="11" x2="14" y2="11"/>
</svg>
),
},
_desconhecido: {
titulo: "Erro inesperado",
descricao: "Ocorreu um erro nao identificado. Tente novamente em alguns instantes.",
cor: "rose",
retentar: true,
icone: (
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
</svg>
),
},
};

function RotuloStatus({ status }: { status: string }) {
const labels: Record<string, string> = {
fila: "Na fila",
processando: "Processando",
ok: "Concluido",
erro: "Erro",
};
return <>{labels[status] || status}</>;
}

function ErroTela({ erro, titulo }: { erro: { tipo: string; mensagem: string; retentavel: boolean }; titulo: string }) {
const config = ERRO_CONFIG[erro.tipo] || ERRO_CONFIG._desconhecido;
const corClass = config.cor === "amber" ? "error-amber" : config.cor === "muted" ? "error-muted" : "error-rose";

return (
<div className={`error-screen ${corClass}`}>
<div className="error-icon-wrap">{config.icone}</div>
<div className="error-content">
<div className="error-titulo">{config.titulo}</div>
<div className="error-desc">{config.descricao}</div>
<div className="error-detail">
<span className="error-label">Consulta:</span> {titulo}
{erro.mensagem && erro.mensagem !== config.titulo && (
<><span className="error-sep">·</span><span className="error-label">Detalhe:</span> {erro.mensagem}</>
)}
</div>
{config.retentar && erro.retentavel && (
<div className="error-hint">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
Voce pode tentar novamente
</div>
)}
{!erro.retentavel && erro.tipo === "validacao" && (
<div className="error-hint hint-warn">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>
Verifique os dados informados e faca uma nova consulta
</div>
)}
</div>
</div>
);
}

function NadaConsta({ titulo }: { titulo: string }) {
return (
<div className="error-screen error-nada">
<div className="error-icon-wrap">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
</svg>
</div>
<div className="error-content">
<div className="error-titulo">Nada consta</div>
<div className="error-desc">A consulta foi realizada com sucesso, mas nao ha restricoes ou pendencias registradas para os dados informados.</div>
<div className="error-detail">
<span className="error-label">Consulta:</span> {titulo}
</div>
</div>
</div>
);
}

function ProcessandoCard() {
return (
<div className="error-screen error-processing">
<div className="error-icon-wrap">
<div className="spinner" style={{ width: 24, height: 24, borderWidth: 2.5 }}></div>
</div>
<div className="error-content">
<div className="error-titulo">Consultando o DETRAN-PA...</div>
<div className="error-desc">Isso pode levar ate 1 minuto. Estamos resolvendo a verificacao de seguranca e buscando os dados.</div>
</div>
</div>
);
}

function FilaCard() {
return (
<div className="error-screen error-fila">
<div className="error-icon-wrap">
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
</div>
<div className="error-content">
<div className="error-titulo">Aguardando na fila</div>
<div className="error-desc">Sua consulta esta na fila e sera processada em breve.</div>
</div>
</div>
);
}

function StatusDot({ status }: { status: string }) {
return <span className={`dot ${status}`} />;
}

function StatusPill({ status }: { status: string }) {
return (
<span className={`pill ${status}`} style={{ marginLeft: "auto" }}>
<RotuloStatus status={status} />
</span>
);
}

function ResultadoView({ r }: { r: ResultadoConsulta }) {
if (r.status === "erro" && r.erro) {
return <ErroTela erro={r.erro} titulo={r.titulo} />;
}

const semConteudo =
Object.keys(r.dados).length === 0 &&
Object.keys(r.secoes).length === 0 &&
r.tabelas.length === 0 &&
r.documentos.length === 0;

if (r.status === "sem_dados" || semConteudo) {
return <NadaConsta titulo={r.titulo} />;
}

return (
<>
{Object.keys(r.dados).length > 0 && (
<dl className="kv">
{Object.entries(r.dados).map(([k, v]) => (
<div key={k} style={{ display: "contents" }}>
<dt>{k}</dt>
<dd>{v}</dd>
</div>
))}
</dl>
)}

{Object.entries(r.secoes).map(([nome, conteudo]) => (
<div key={nome}>
<div className="secao-title">{nome}</div>
<dl className="kv">
{Object.entries(conteudo).map(([k, v]) => (
<div key={k} style={{ display: "contents" }}>
<dt>{k}</dt>
<dd>{v}</dd>
</div>
))}
</dl>
</div>
))}

{r.tabelas.map((tabela, i) => (
<Tabela key={i} linhas={tabela} />
))}

{r.documentos.map((doc, i) => (
<a key={i} className="doc-link" href={urlDocumento(doc.url)} target="_blank" rel="noopener noreferrer">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
Baixar {doc.nome}
</a>
))}
</>
);
}

function Tabela({ linhas }: { linhas: Record<string, string>[] }) {
if (!linhas.length) return null;
const colunas = Object.keys(linhas[0]);
return (
<table>
<thead>
<tr>{colunas.map((c) => <th key={c}>{c}</th>)}</tr>
</thead>
<tbody>
{linhas.map((linha, i) => (
<tr key={i}>{colunas.map((c) => <td key={c}>{linha[c]}</td>)}</tr>
))}
</tbody>
</table>
);
}

function ItemView({ item }: { item: ItemJob }) {
const r = item.resultado;
return (
<div className="section-block">
<div className="result-head">
<StatusDot status={item.status} />
<span className="result-title">{item.titulo}</span>
<StatusPill status={item.status} />
</div>
{item.status === "fila" && <FilaCard />}
{item.status === "processando" && <ProcessandoCard />}
{item.status === "ok" && r && <ResultadoView r={r} />}
{item.status === "erro" && r && <ResultadoView r={r} />}
</div>
);
}

export default function ResultadoPage({ params }: { params: { jobId: string } }) {
const { user, refreshProfile } = useAuth();
const [job, setJob] = useState<Job | null>(null);
const [erro, setErro] = useState<string | null>(null);
const [estornado, setEstornado] = useState(false);
const [creditosEstornados, setCreditosEstornados] = useState(0);
const [toast, setToast] = useState<{ mensagem: string; tipo: "success" | "error" | "info" } | null>(null);
const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
const estornoFeito = useRef(false);

// Verifica se todos os itens com erro são falhas de sistema (não do usuário)
function todosErrosSistema(itens: ItemJob[]): boolean {
const comErro = itens.filter((i) => i.status === "erro");
if (comErro.length === 0) return false;
const algumOk = itens.some((i) => i.status === "ok");
if (algumOk) return false; // pelo menos uma consulta funcionou — não estornar
return comErro.every((i) => {
const tipo = i.resultado?.erro?.tipo ?? "_desconhecido";
return ERROS_SISTEMA.has(tipo);
});
}

// Atualiza status do registro de histórico no Firestore
async function atualizarHistorico(status: "concluido" | "erro" | "estornado") {
if (!user) return;
try {
await setDoc(
doc(db, "users", user.uid, "consultas", params.jobId),
{ status },
{ merge: true }
);
} catch {
// Silencioso — histórico não é crítico
}
}

// Estorna créditos automaticamente em erros de sistema
async function processarEstorno(j: Job) {
if (!user || estornoFeito.current) return;
estornoFeito.current = true;

const creditos = j.itens.length; // 1 crédito por consulta
const refundId = `${user.uid}_${params.jobId}`;

try {
// Idempotente: setDoc com merge evita estorno duplo
await setDoc(
doc(db, "refunds", refundId),
{ uid: user.uid, jobId: params.jobId, creditos, createdAt: serverTimestamp() },
{ merge: true }
);
// Devolve os créditos ao saldo do usuário
await updateDoc(doc(db, "users", user.uid), {
saldoCreditos: increment(creditos),
});
await atualizarHistorico("estornado");
await refreshProfile();
setCreditosEstornados(creditos);
setEstornado(true);
setToast({ mensagem: `${creditos} crédito${creditos !== 1 ? "s" : ""} devolvido${creditos !== 1 ? "s" : ""}! Falha técnica do sistema.`, tipo: "info" });
} catch {
// Estorno silencioso — log server-side para revisão manual se necessário
}
}

useEffect(() => {
let ativo = true;
async function tick() {
try {
const j = await obterJob(params.jobId);
if (!ativo) return;
setJob(j);

// Quando o job finaliza, verificar se precisa de estorno ou atualizar histórico
if (STATUS_FINAL.has(j.status)) {
if (todosErrosSistema(j.itens)) {
await processarEstorno(j);
} else {
const temSucesso = j.itens.some((i) => i.status === "ok");
const statusFinal = temSucesso ? "concluido" : "erro";
await atualizarHistorico(statusFinal);
if (document.hidden) {
  // usuário está em outra aba — tenta notificação do browser
  if (Notification.permission === "granted") {
    new Notification("DETRAN-PA — Consulta concluída!", {
      body: temSucesso ? "Seus resultados estão prontos." : "A consulta foi concluída com erros.",
      icon: "/favicon.ico",
    });
  }
}
setToast({
  mensagem: temSucesso ? "Consulta concluída! Veja os resultados abaixo." : "Consulta finalizada com erros.",
  tipo: temSucesso ? "success" : "error",
});
// Incrementa totalConsultas apenas quando há pelo menos uma consulta com sucesso
if (temSucesso && user) {
try {
await updateDoc(doc(db, "users", user.uid), {
totalConsultas: increment(1),
});
} catch {
// silencioso
}
}
}
}

if (!STATUS_FINAL.has(j.status)) timer.current = setTimeout(tick, 2500);
} catch (e: any) {
if (ativo) setErro(e.message);
}
}
tick();
return () => {
ativo = false;
if (timer.current) clearTimeout(timer.current);
};
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [params.jobId, user]);

if (erro) return (
<div className="center">
<div className="error-screen error-rose">
<div className="error-icon-wrap">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
</svg>
</div>
<div className="error-content">
<div className="error-titulo">Falha na comunicacao</div>
<div className="error-desc">{erro}</div>
</div>
</div>
<Link href="/" className="btn btn-ghost" style={{ marginTop: 16 }}>Voltar ao inicio</Link>
</div>
);

if (!job) return (
<div className="center">
<div className="spinner" style={{ width: 36, height: 36 }}></div>
<p style={{ marginTop: 8, color: "var(--muted)" }}>Carregando resultado...</p>
</div>
);

const processando = !STATUS_FINAL.has(job.status);
const concluidos = job.itens.filter((i) => i.status === "ok" || i.status === "erro").length;
const finalizado = STATUS_FINAL.has(job.status);

return (
<>
<div style={{ marginTop: 24, marginBottom: 8 }}>
<Link href="/" className="back-link">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 6, verticalAlign: -2 }}><line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/></svg>
Nova consulta
</Link>
</div>
<h1>Resultado da consulta</h1>
<p className="subtitle" style={{ textAlign: "left", maxWidth: "none", marginLeft: 0, marginRight: 0 }}>
{processando
? `Processando... ${concluidos}/${job.itens.length} concluida(s). Pode levar ate ~1 min por consulta.`
: `Concluido: ${concluidos}/${job.itens.length} consulta(s).`}
</p>

{/* Aviso de estorno automático */}
{estornado && (
<div className="credit-refund-notice">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
<polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
</svg>
<span>
<strong>{creditosEstornados} crédito{creditosEstornados !== 1 ? "s" : ""} devolvido{creditosEstornados !== 1 ? "s" : ""}!</strong>{" "}
O sistema do DETRAN-PA apresentou uma falha técnica — seus créditos foram estornados automaticamente.
</span>
</div>
)}

{job.itens.map((item) => (
<ItemView key={item.slug} item={item} />
))}

{/* Widget de feedback — aparece quando job está finalizado */}
{finalizado && <FeedbackWidget jobId={params.jobId} />}

{/* Toast de notificação */}
{toast && (
  <Toast
    mensagem={toast.mensagem}
    tipo={toast.tipo}
    onClose={() => setToast(null)}
  />
)}
</>
);
}
