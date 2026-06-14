"use client";

import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const { profile } = useAuth();
  const router = useRouter();

  if (!profile) return <div className="center"><div className="spinner" /></div>;

  return (
    <div className="dashboard">
      <div className="dash-header">
        <h1>Olá, {profile.nome}!</h1>
        <p className="subtitle" style={{ textAlign: "left", maxWidth: "none", marginLeft: 0, marginRight: 0 }}>
          Bem-vindo ao painel de consultas do DETRAN-PA.
        </p>
      </div>

      <div className="dash-grid">
        <div className="dash-card dash-card-credits" onClick={() => router.push("/creditos")}>
          <div className="dash-card-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="8"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
            </svg>
          </div>
          <div className="dash-card-info">
            <div className="dash-card-value">{profile.saldoCreditos}</div>
            <div className="dash-card-label">créditos disponíveis</div>
          </div>
          <div className="dash-card-action">Recarregar →</div>
        </div>

        <div className="dash-card" onClick={() => router.push("/consultas")}>
          <div className="dash-card-icon dash-card-icon-blue">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </div>
          <div className="dash-card-info">
            <div className="dash-card-value">{profile.totalConsultas}</div>
            <div className="dash-card-label">consultas realizadas</div>
          </div>
          <div className="dash-card-action">Nova consulta →</div>
        </div>

        <div className="dash-card" onClick={() => router.push("/historico")}>
          <div className="dash-card-icon dash-card-icon-cyan">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
            </svg>
          </div>
          <div className="dash-card-info">
            <div className="dash-card-label">Histórico</div>
          </div>
          <div className="dash-card-action">Ver todas →</div>
        </div>

        <div className="dash-card" onClick={() => router.push("/suporte")}>
          <div className="dash-card-icon dash-card-icon-green">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
            </svg>
          </div>
          <div className="dash-card-info">
            <div className="dash-card-label">Suporte</div>
          </div>
          <div className="dash-card-action">Falar no WhatsApp →</div>
        </div>
      </div>
    </div>
  );
}