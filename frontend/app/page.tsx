"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { listarConsultas, criarJob } from "@/lib/api";
import type { Consulta, CampoEntrada } from "@/lib/types";

const CATEGORIA_LABEL: Record<string, string> = {
  veiculo: "Veiculo",
  habilitacao: "Habilitacao (CNH)",
  boleto: "Boletos e documentos",
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

  useEffect(() => {
    const timer = setTimeout(() => setServidorLento(true), 5000);
    listarConsultas()
      .then(setConsultas)
      .catch((e) => setErroCarga(e.message))
      .finally(() => { clearTimeout(timer); setCarregando(false); });
  }, []);

  const porCategoria = useMemo(() => {
    const m: Record<string, Consulta[]> = {};
    for (const c of consultas) (m[c.categoria] ??= []).push(c);
    return m;
  }, [consultas]);

  // Campos exigidos pela uniao das consultas selecionadas
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

  if (carregando) return <p className="center">{servidorLento ? "Aguardando servidor... (free tier - ate 1 min)" : "Carregando consultas..."}</p>;
  if (erroCarga)
    return (
      <div className="center">
        <p>Nao foi possivel carregar o catalogo.</p>
        <p className="alert erro">{erroCarga}</p>
        <p>Verifique se o backend esta rodando (NEXT_PUBLIC_API_URL).</p>
      </div>
    );

  return (
    <>
      <h1>O que voce quer consultar?</h1>
      <p className="subtitle">
        Marque uma ou varias consultas e faca tudo de uma vez. Preencha os dados abaixo.
      </p>

      {Object.entries(porCategoria).map(([cat, lista]) => (
        <div key={cat}>
          <h2>{CATEGORIA_LABEL[cat] || cat}</h2>
          <div className="grid">
            {lista.map((c) => {
              const sel = selecionadas.has(c.slug);
              return (
                <div
                  key={c.slug}
                  className={`card${sel ? " selected" : ""}`}
                  onClick={() => toggle(c.slug)}
                >
                  <div className="card-head">
                    <div className="card-check">{sel ? "✓" : ""}</div>
                    <div>
                      <div className="card-title">{c.titulo}</div>
                      <div className="card-desc">{c.descricao}</div>
                    </div>
                  </div>
                  <div className="badges">
                    {c.gera_pdf && <span className="badge pdf">📄 Gera PDF</span>}
                    {c.gera_boleto && <span className="badge">Boleto</span>}
                    <span className="badge credito">
                      {c.creditos} credito{c.creditos > 1 ? "s" : ""}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

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
          <b>{selecionadas.size}</b> consulta(s) selecionada(s) · <b>{totalCreditos}</b> credito(s)
          {faltando.length > 0 && selecionadas.size > 0 && (
            <span> · faltam: {faltando.map((f) => f.rotulo).join(", ")}</span>
          )}
        </div>
        <button className="btn" disabled={!podeEnviar} onClick={enviar}>
          {enviando ? "Iniciando..." : "Consultar agora"}
        </button>
      </div>
    </>
  );
}
