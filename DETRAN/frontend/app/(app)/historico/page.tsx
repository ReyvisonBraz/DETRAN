"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/lib/auth";
import { collection, query, where, orderBy, getDocs, Timestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useRouter } from "next/navigation";

interface ConsultaHistorico {
  id: string;
  jobId: string;
  titulo: string;
  placaOuCpf: string;
  status: "concluido" | "erro" | "estornado";
  creditsUsed: number;
  createdAt: Timestamp;
  consultasSlugs: string[];
}

function formatarData(ts: Timestamp) {
  const d = ts.toDate();
  return d.toLocaleDateString("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  });
}

function diasRestantes(ts: Timestamp) {
  const diff = 30 - Math.floor((Date.now() - ts.toDate().getTime()) / 86400000);
  return Math.max(0, diff);
}

export default function HistoricoPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [consultas, setConsultas] = useState<ConsultaHistorico[]>([]);
  const [carregando, setCarregando] = useState(true);

  useEffect(() => {
    if (!user) return;
    const limite30Dias = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    const q = query(
      collection(db, "users", user.uid, "consultas"),
      where("createdAt", ">=", Timestamp.fromDate(limite30Dias)),
      orderBy("createdAt", "desc")
    );
    getDocs(q)
      .then((snap) => {
        setConsultas(
          snap.docs.map((d) => ({ id: d.id, ...d.data() } as ConsultaHistorico))
        );
      })
      .finally(() => setCarregando(false));
  }, [user]);

  if (carregando) return <div className="center"><div className="spinner" /></div>;

  return (
    <div className="historico-page">
      <div>
        <h1>Histórico de consultas</h1>
        <p className="subtitle" style={{ textAlign: "left", maxWidth: "none", marginLeft: 0, marginRight: 0, marginBottom: 4 }}>
          Consultas dos últimos 30 dias. Clique para ver os resultados novamente.
        </p>
      </div>

      {consultas.length === 0 ? (
        <div className="historico-empty">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--muted)", marginBottom: 12 }}>
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          <p>Nenhuma consulta encontrada nos últimos 30 dias.</p>
          <button className="btn" style={{ marginTop: 16 }} onClick={() => router.push("/consultas")}>
            Fazer primeira consulta →
          </button>
        </div>
      ) : (
        <>
          {consultas.map((c) => {
            const statusColor =
              c.status === "concluido" ? "var(--emerald)" :
              c.status === "estornado" ? "var(--amber)" :
              "var(--rose)";

            const statusLabel =
              c.status === "concluido" ? "Concluído" :
              c.status === "estornado" ? "Estornado" :
              "Erro";

            return (
              <div
                key={c.id}
                className="historico-item"
                onClick={() => router.push(`/resultado/${c.jobId}`)}
              >
                <div
                  className="historico-status-dot"
                  style={{ background: statusColor, boxShadow: `0 0 6px ${statusColor}` }}
                />
                <div className="historico-info">
                  <div className="historico-titulo">{c.titulo || "Consulta"}</div>
                  <div className="historico-meta">
                    <span>{formatarData(c.createdAt)}</span>
                    {c.placaOuCpf && <span>· {c.placaOuCpf}</span>}
                    <span>· {c.creditsUsed} cr</span>
                    <span style={{ color: statusColor }}>· {statusLabel}</span>
                  </div>
                </div>
                <svg className="historico-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>
            );
          })}

          <p className="historico-expira">
            O histórico é mantido por 30 dias. Consultas mais antigas são removidas automaticamente.
          </p>
        </>
      )}
    </div>
  );
}
