"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useState, useEffect, useMemo } from "react";
import { listarConsultas, criarJob } from "@/lib/api";
import type { Consulta, CampoEntrada } from "@/lib/types";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";

const CATEGORIA_CONFIG: Record<string, { label: string; icon: JSX.Element; desc: string }> = {
veiculo: {
label: "Veículo",
desc: "Débitos, gravames, licenciamento e infrações",
icon: (
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.2-.7-1.9-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.2C1.8 10.9 1.5 12 1.5 13v3c0 .6.4 1 1 1h1"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
</svg>
),
},
habilitacao: {
label: "Habilitação",
desc: "Pontuação, situação e validade da CNH",
icon: (
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M2 10h2M20 10h2"/>
</svg>
),
},
boleto: {
label: "Boletos e Docs",
desc: "Emissão de boletos e documentos digitais",
icon: (
<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="M12 18v-6"/><path d="M9 15h6"/>
</svg>
),
},
};

const SLUG_ICONE: Record<string, JSX.Element> = {
veiculo_detalhada: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>,
infracoes: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>,
gravame: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>,
crlv_e: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6"/><path d="m9 15 2 2 4-4"/></svg>,
acompanha_documento: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>,
licenciamento_atual: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>,
licenciamento_anterior: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/><path d="m8 15 2 2 4-4"/></svg>,
boleto_infracao: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="8"/><path d="M12 8v8M9 12h6"/></svg>,
cnh_pontuacao: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/><path d="M4 22h16"/><path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22"/><path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2Z"/></svg>,
};

function CheckSvg() {
return <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg>;
}

function ArrowSvg() {
return <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>;
}

export default function ConsultasPage() {
const { user, profile } = useAuth();
const router = useRouter();
const [consultas, setConsultas] = useState<Consulta[]>([]);
const [carregando, setCarregando] = useState(true);
const [erroCarga, setErroCarga] = useState<string | null>(null);
const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set());
const [valores, setValores] = useState<Record<string, string>>({});
const [enviando, setEnviando] = useState(false);

useEffect(() => {
listarConsultas()
.then(setConsultas)
.catch((e) => setErroCarga(e.message))
.finally(() => setCarregando(false));
}, []);

const porCategoria = useMemo(() => {
const m: Record<string, Consulta[]> = {};
for (const c of consultas) (m[c.categoria] ??= []).push(c);
return m;
}, [consultas]);

const camposNecessarios = useMemo(() => {
const vistos = new Map<string, CampoEntrada>();
for (const c of consultas) {
if (!selecionadas.has(c.slug)) continue;
for (const campo of c.entradas) if (!vistos.has(campo.nome)) vistos.set(campo.nome, campo);
}
return [...vistos.values()];
}, [consultas, selecionadas]);

const totalCreditos = useMemo(
() => consultas.filter((c) => selecionadas.has(c.slug)).reduce((s, c) => s + c.creditos, 0),
[consultas, selecionadas]
);

function toggle(slug: string) {
setSelecionadas((prev) => {
const next = new Set(prev);
next.has(slug) ? next.delete(slug) : next.add(slug);
return next;
});
}

const faltando = camposNecessarios.filter((c) => c.obrigatorio && !(valores[c.nome] || "").trim());
const saldoInsuficiente = profile ? profile.saldoCreditos < totalCreditos : false;
const podeEnviar = selecionadas.size > 0 && faltando.length === 0 && !enviando && !saldoInsuficiente;

async function enviar() {
if (!podeEnviar || !user) return;
setEnviando(true);
try {
const res = await criarJob(
[...selecionadas].map((slug) => ({ slug })),
valores
);

// Salvar registro no histórico (users/{uid}/consultas/{jobId})
const slugsSelecionados = [...selecionadas];
const tituloConsulta = consultas
.filter((c) => slugsSelecionados.includes(c.slug))
.map((c) => c.titulo)
.join(", ");
const placaOuCpf =
valores["placa"] || valores["cpf"] || valores["renavam"] || "";

try {
await setDoc(doc(db, "users", user.uid, "consultas", res.job_id), {
jobId: res.job_id,
titulo: tituloConsulta || "Consulta DETRAN-PA",
placaOuCpf,
status: "processando",
creditsUsed: totalCreditos,
consultasSlugs: slugsSelecionados,
createdAt: serverTimestamp(),
});
} catch {
// Falha silenciosa — não impede a navegação
}

router.push(`/resultado/${res.job_id}`);
} catch (e: any) {
alert("Erro ao iniciar consulta: " + e.message);
setEnviando(false);
}
}

if (carregando) return (
<div className="center"><div className="spinner"></div></div>
);

if (erroCarga) return (
<div className="center">
<p>Não foi possível carregar o catálogo.</p>
<p>{erroCarga}</p>
</div>
);

let cardIndex = 0;

return (
<>
<div className="hero">
<div className="hero-badge">DETRAN-PA</div>
<h1>Nova Consulta</h1>
<p className="subtitle">Selecione as consultas desejadas e preencha os dados do veículo.</p>
</div>

{saldoInsuficiente && (
<div className="error-screen error-rose" style={{ marginBottom: 16 }}>
<div className="error-icon-wrap">
<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
</div>
<div className="error-content">
<div className="error-titulo">Créditos insuficientes</div>
<div className="error-desc">Você tem <strong>{profile?.saldoCreditos}</strong> créditos, mas precisa de <strong>{totalCreditos}</strong> para esta consulta.</div>
<a href="/creditos" className="btn btn-primary" style={{ marginTop: 8, display: "inline-flex" }}>Recarregar créditos</a>
</div>
</div>
)}

{Object.entries(porCategoria).map(([cat, lista]) => {
const cfg = CATEGORIA_CONFIG[cat] || { label: cat, icon: <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"><rect x="3" y="3" width="18" height="18" rx="2"/></svg>, desc: "" };
return (
<section key={cat} className="cat-section">
<div className={`cat-header ${cat}`}>
<div className={`cat-icon-wrap ${cat}`}>{cfg.icon}</div>
<div className="cat-info">
<div className="cat-label">{cfg.label}</div>
{cfg.desc && <div className="cat-desc">{cfg.desc}</div>}
</div>
<span className="cat-count">{lista.length}</span>
</div>
<div className="grid">
{lista.map((c) => {
const sel = selecionadas.has(c.slug);
const delay = cardIndex++ * 55;
return (
<button key={c.slug} className={`card${sel ? " selected" : ""}`} onClick={() => toggle(c.slug)} style={{ animationDelay: `${delay}ms` }}>
<div className="card-indicator">{sel ? <CheckSvg /> : <span className="card-indicator-empty" />}</div>
<div className="card-body">
<div className="card-top">
<span className="card-icon-wrap">{SLUG_ICONE[c.slug] || cfg.icon}</span>
<span className="card-title">{c.titulo}</span>
</div>
<div className="card-desc">{c.descricao}</div>
<div className="badges">
{c.gera_pdf && <span className="badge pdf-label">PDF</span>}
{c.gera_boleto && <span className="badge boleto-label">Boleto</span>}
<span className="badge credito-label">{c.creditos} cr</span>
</div>
</div>
</button>
);
})}
</div>
</section>
);
})}

{camposNecessarios.length > 0 && (
<section className="form-section">
<h2>Dados para a consulta</h2>
<div className="form-fields">
{camposNecessarios.map((campo) => (
<div className="field" key={campo.nome}>
<label>{campo.rotulo}{campo.obrigatorio && <span className="required-mark">*</span>}</label>
<input value={valores[campo.nome] || ""} placeholder={campo.mascara || ""} onChange={(e) => setValores((v) => ({ ...v, [campo.nome]: e.target.value }))} />
{campo.ajuda && <div className="help">{campo.ajuda}</div>}
</div>
))}
</div>
</section>
)}

<div className="bar">
<div className="bar-left">
<div className="bar-stats">
<span className="bar-stat"><span className="bar-stat-num">{selecionadas.size}</span><span className="bar-stat-label">consulta{selecionadas.size !== 1 ? "s" : ""}</span></span>
<span className="bar-divider" />
<span className="bar-stat"><span className="bar-stat-num">{totalCreditos}</span><span className="bar-stat-label">crédito{totalCreditos !== 1 ? "s" : ""}</span></span>
<span className="bar-divider" />
<span className="bar-stat" style={{ color: saldoInsuficiente ? "var(--rose)" : "var(--muted)" }}><span className="bar-stat-label">saldo:</span><span className="bar-stat-num" style={{ color: saldoInsuficiente ? "var(--rose)" : "var(--emerald)" }}>{profile?.saldoCreditos}</span></span>
</div>
{faltando.length > 0 && selecionadas.size > 0 && (
<div className="bar-warning">Preencha: {faltando.map((f) => f.rotulo).join(", ")}</div>
)}
</div>
<button className="btn btn-primary" disabled={!podeEnviar} onClick={enviar}>
{enviando ? <><span className="btn-spinner"></span> Iniciando...</> : <>Consultar agora <ArrowSvg /></>}
</button>
</div>
</>
);
}
