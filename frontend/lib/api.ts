import type { Consulta, Job, CriarJobResponse } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
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

// PDF: a API devolve url relativa (ex: /api/documentos/xxx.pdf)
export function urlDocumento(url: string) {
  return url.startsWith("http") ? url : `${API_URL}${url}`;
}
