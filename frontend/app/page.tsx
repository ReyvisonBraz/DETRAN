"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { listarConsultas, criarJob } from "@/lib/api";
import type { Consulta, CampoEntrada } from "@/lib/types";

const CATEGORIA_CONFIG: Record<string, { label: string; icon: string; desc: string }> = {
  veiculo:     { label: "Veículo",           icon: "🚗", desc: "Débitos, gravames, licenciamento e infrações do veículo" },
  habilitacao: { label: "Habilitação (CNH)", icon: "🪪", desc: "Pontuação, situação e validade da CNH do motorista" },
  boleto:      { label: "Boletos e Docs",    icon: "📋", desc: "Emissão de boletos de infrações e documentos digitais" },
};

const ICONES: Record<string, string> = {
  veiculo_detalhada:      "🚗",
  infracoes:              "⚡",
  gravame:                "🏦",
  crlv_e:                 "📄",
  acompanha_documento:    "📋",
  licenciamento_atual:    "📅",
  licenciamento_anterior: "📆",
  boleto_infracao:        "💸",
  cnh_pontuacao:          "🏆",
};

export default function Home() {
  const router = useRouter();
  const [consultas, setConsultas] = useState<Consulta[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erroCarga, setErroCarga] = useState<string | null>(null);
  const [selecionadas, setSelecionadas] = useState<Set<string>>(new Set());
  const [valores, setValores] = useState<Record<string, string>>({});
  const [enviando, setEnviando] = useState(false);
  const [servidorLento, setServidorLento] = useState(false);
  const [acordando, setAcordando] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setServidorLento(true), 5000);
    listarConsultas()
      .then(setConsultas)
      .catch((e) => setErroCarga(e.message))
      .finally(() => { clearTimeout(timer); setCarregando(false); });
  }, []);

  async function acordar() {
    setAcordando(true);
    try {
      const lista = await listarConsultas();
      setConsultas(lista);
      setCarregando(false);
    } catch {}
    setAcordando(false);
  }

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

  const faltando = camposNecessarios.filter(
    (c) => c.obrigatorio && !(valores[c.nome] || "").trim()
  );
  const podeEnviar = selecionadas.size > 0 && faltando.length === 0 && !enviando;

  async function enviar() {
    setEnviando(true);
    try {
      const res = await criarJob(
        [...selecionadas].map((slug) => ({ slug })),
        valores
      );
      router.push(`/resultado/${res.job_id}`);
    } catch (e: any) {
      alert("Erro ao iniciar consulta: " + e.message);
      setEnviando(false);
    }
  }

  if (carregando && !servidorLento) return (
    <div className="center">
      <div className="spinner"></div>
      <p style={{ marginTop: "1.2rem", color: "var(--muted)" }}>Carregando consultas...</p>
    </div>
  );

  if (carregando) return (
    <div className="center">
      <div className="wakeup-card">
        <div className="wakeup-icon">⏳</div>
        <div className="wakeup-title">Servidor acordando</div>
        <div className="wakeup-desc">
          O servidor hiberna após inatividade (free tier).<br />
          Aguarde até 1 minuto ou clique para tentar novamente.
        </div>
        <button className="btn" onClick={acordar} disabled={acordando}>
          {acordando ? "🔄 Conectando..." : "🔔 Acordar servidor"}
        </button>
      </div>
    </div>
  );

  if (erroCarga) return (
    <div className="center">
      <p>Não foi possível carregar o catálogo.</p>
      <p>{erroCarga}</p>
      <p>Verifique se o backend está rodando.</p>
    </div>
  );

  let cardIndex = 0;

  return (
    <>
      <h1>O que você quer consultar?</h1>
      <p className="subtitle">
        Selecione uma ou mais consultas e execute tudo de uma vez. Preencha os dados necessários abaixo.
      </p>

      {Object.entries(porCategoria).map(([cat, lista]) => {
        const cfg = CATEGORIA_CONFIG[cat] || { label: cat, icon: "📋", desc: "" };
        return (
          <div key={cat} className="cat-section">
            <div className={`cat-header ${cat}`}>
              <div className={`cat-icon-wrap ${cat}`}>{cfg.icon}</div>
              <div className="cat-info">
                <div className="cat-label">{cfg.label}</div>
                {cfg.desc && <div className="cat-desc">{cfg.desc}</div>}
              </div>
              <span className="cat-count">{lista.length} consulta{lista.length > 1 ? "s" : ""}</span>
            </div>
            <div className="grid">
              {lista.map((c) => {
                const sel = selecionadas.has(c.slug);
                const delay = cardIndex++ * 55;
                return (
                  <div
                    key={c.slug}
                    className={`card${sel ? " selected" : ""}`}
                    onClick={() => toggle(c.slug)}
                    style={{ animationDelay: `${delay}ms` }}
                  >
                    <div className="card-head">
                      <div className="card-check">{sel ? "✓" : ""}</div>
                      <div style={{ flex: 1 }}>
                        <span className="card-icon">{ICONES[c.slug] || cfg.icon}</span>
                        <div className="card-title">{c.titulo}</div>
                        <div className="card-desc">{c.descricao}</div>
                      </div>
                    </div>
                    <div className="badges">
                      {c.gera_pdf && <span className="badge pdf">📄 PDF</span>}
                      {c.gera_boleto && <span className="badge">Boleto</span>}
                      <span className="badge credito">
                        {c.creditos} crédito{c.creditos > 1 ? "s" : ""}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {camposNecessarios.length > 0 && (
        <>
          <h2>Dados para a consulta</h2>
          <div className="form-fields">
            {camposNecessarios.map((campo) => (
              <div className="field" key={campo.nome}>
                <label>
                  {campo.rotulo}
                  {campo.obrigatorio ? " *" : ""}
                </label>
                <input
                  value={valores[campo.nome] || ""}
                  placeholder={campo.mascara || ""}
                  onChange={(e) =>
                    setValores((v) => ({ ...v, [campo.nome]: e.target.value }))
                  }
                />
                {campo.ajuda && <div className="help">{campo.ajuda}</div>}
              </div>
            ))}
          </div>
        </>
      )}

      <div className="bar">
        <div className="bar-info">
          <b>{selecionadas.size}</b> consulta(s) · <b>{totalCreditos}</b> crédito(s)
          {faltando.length > 0 && selecionadas.size > 0 && (
            <span> · faltam: {faltando.map((f) => f.rotulo).join(", ")}</span>
          )}
        </div>
        <button className="btn" disabled={!podeEnviar} onClick={enviar}>
          {enviando ? "Iniciando..." : "Consultar agora →"}
        </button>
      </div>
    </>
  );
}
