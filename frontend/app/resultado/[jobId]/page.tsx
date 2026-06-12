"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { obterJob, urlDocumento } from "@/lib/api";
import type { Job, ItemJob, ResultadoConsulta } from "@/lib/types";

const STATUS_FINAL = new Set(["concluido", "parcial", "erro"]);

export default function ResultadoPage({ params }: { params: { jobId: string } }) {
  const [job, setJob] = useState<Job | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let ativo = true;
    async function tick() {
      try {
        const j = await obterJob(params.jobId);
        if (!ativo) return;
        setJob(j);
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
  }, [params.jobId]);

  if (erro) return <div className="center"><p className="alert erro">{erro}</p></div>;
  if (!job) return <p className="center">Carregando...</p>;

  const processando = !STATUS_FINAL.has(job.status);
  const concluidos = job.itens.filter((i) => i.status === "ok" || i.status === "erro").length;

  return (
    <>
      <p style={{ marginTop: 24 }}>
        <Link href="/" className="back-link">← Nova consulta</Link>
      </p>
      <h1>Resultado da consulta</h1>
      <p className="subtitle">
        {processando
          ? `Processando... ${concluidos}/${job.itens.length} concluida(s). Pode levar ate ~1 min por consulta.`
          : `Concluido: ${concluidos}/${job.itens.length} consulta(s).`}
      </p>

      {job.itens.map((item) => (
        <ItemView key={item.slug} item={item} />
      ))}
    </>
  );
}

function ItemView({ item }: { item: ItemJob }) {
  const r = item.resultado;
  return (
    <div className="section-block">
      <div className="result-head">
        <span className={`dot ${item.status}`} />
        <span className="result-title">{item.titulo}</span>
        <span className={`pill ${item.status}`} style={{ marginLeft: "auto" }}>
          {rotuloStatus(item.status)}
        </span>
      </div>
      {item.status === "fila" && <p className="alert info">Aguardando na fila...</p>}
      {item.status === "processando" && (
        <p className="alert info">Consultando o DETRAN e resolvendo verificacao de seguranca...</p>
      )}
      {r && <ResultadoView r={r} />}
    </div>
  );
}

function ResultadoView({ r }: { r: ResultadoConsulta }) {
  if (r.status === "erro" && r.erro) {
    return (
      <div className="alert erro">
        <strong>{r.erro.mensagem}</strong>
        {r.erro.retentavel && <div style={{ marginTop: 6 }}>Voce pode tentar esta consulta novamente.</div>}
        {r.erro.tipo === "validacao" && (
          <div style={{ marginTop: 6 }}>Confira os dados informados.</div>
        )}
      </div>
    );
  }

  const semConteudo =
    Object.keys(r.dados).length === 0 &&
    Object.keys(r.secoes).length === 0 &&
    r.tabelas.length === 0 &&
    r.documentos.length === 0;

  if (r.status === "sem_dados" || semConteudo) {
    return <p className="alert info">Nada consta / nenhum resultado encontrado.</p>;
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
          📄 Baixar {doc.nome}
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

function rotuloStatus(s: string) {
  return {
    fila: "Na fila",
    processando: "Processando",
    ok: "Concluido",
    erro: "Erro",
  }[s] || s;
}
