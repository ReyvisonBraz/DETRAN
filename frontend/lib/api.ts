import type { Consulta, Job, CriarJobResponse } from "./types";

const API_PADRAO = "https://detran-api-1651.onrender.com";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || API_PADRAO;

async function getIdToken(): Promise<string | null> {
  try {
    const { auth } = await import("./firebase");
    const user = auth.currentUser;
    if (!user) return null;
    return await user.getIdToken();
  } catch {
    return null;
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await getIdToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (res.status === 401) {
    throw new Error("Sessao expirada. Faca login novamente.");
  }

  if (res.status === 402) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || "Creditos insuficientes.");
  }

  if (!res.ok) {
    let msg = `Erro ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) msg = body.detail;
    } catch {}
    throw new Error(msg);
  }
  return res.json();
}

export function listarConsultas() {
  return req<{ consultas: Consulta[] }>("/api/consultas").then((r) => r.consultas);
}

export function criarJob(
  consultas: { slug: string; parametros?: Record<string, string> }[],
  parametros: Record<string, string>
) {
  return req<CriarJobResponse>("/api/jobs", {
    method: "POST",
    body: JSON.stringify({ consultas, parametros }),
  });
}

export function obterJob(jobId: string) {
  return req<Job>(`/api/jobs/${jobId}`);
}

export function obterSaldo() {
  return req<{ saldo: number; custo_por_consulta: number; historico: Transacao[] }>("/api/creditos/saldo");
}

export function obterHistoricoCreditos() {
  return req<{ transacoes: Transacao[] }>("/api/creditos/historico");
}

export function urlDocumento(url: string) {
  return url.startsWith("http") ? url : `${API_URL}${url}`;
}

export interface Transacao {
  id: string;
  uid: string;
  tipo: "consumo" | "recarga" | "bonus" | "reembolso";
  quantidade: number;
  descricao: string;
  saldoApos: number;
  createdAt: string;
}