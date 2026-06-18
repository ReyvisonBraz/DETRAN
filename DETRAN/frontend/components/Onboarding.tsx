"use client";

import { useState } from "react";
import { doc, updateDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useAuth } from "@/lib/auth";

const STEPS = [
  {
    icon: (
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.2-.7-1.9-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.2C1.8 10.9 1.5 12 1.5 13v3c0 .6.4 1 1 1h1"/>
        <circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>
      </svg>
    ),
    iconBg: "rgba(99,102,241,.15)",
    iconColor: "var(--primary-2)",
    titulo: "Bem-vindo ao DETRAN-PA",
    desc: "Aqui você consulta dados de veículos, infrações, licenciamento, CNH e emite documentos — tudo direto do DETRAN-PA, de forma rápida e segura.",
    destaque: null,
  },
  {
    icon: (
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="8"/><line x1="12" y1="8" x2="12" y2="16"/><line x1="8" y1="12" x2="16" y2="12"/>
      </svg>
    ),
    iconBg: "rgba(16,185,129,.15)",
    iconColor: "var(--emerald)",
    titulo: "Como funcionam os créditos",
    desc: "Cada consulta consome créditos. Você começou com 2 créditos grátis! Se o sistema falhar por problema técnico, seus créditos são devolvidos automaticamente.",
    destaque: "Você tem 2 créditos grátis esperando por você",
  },
  {
    icon: (
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
    iconBg: "rgba(34,211,238,.15)",
    iconColor: "var(--cyan)",
    titulo: "Fazendo uma consulta",
    desc: "Selecione os tipos de consulta que deseja (pode selecionar vários de uma vez!), preencha os dados do veículo ou CPF e clique em Consultar agora.",
    destaque: null,
  },
  {
    icon: (
      <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    iconBg: "rgba(245,158,11,.15)",
    iconColor: "var(--amber)",
    titulo: "Indique e ganhe mais",
    desc: "Compartilhe seu código de indicação com amigos. Cada amigo que se cadastrar usando seu código dá +2 créditos pra você e +2 créditos pra ele.",
    destaque: "Veja seu código na página de Créditos",
  },
];

export default function Onboarding({ onClose }: { onClose: () => void }) {
  const { user, refreshProfile } = useAuth();
  const [step, setStep] = useState(0);
  const [fechando, setFechando] = useState(false);

  async function concluir() {
    setFechando(true);
    if (user) {
      await updateDoc(doc(db, "users", user.uid), { onboardingCompleto: true });
      await refreshProfile();
    }
    onClose();
  }

  async function pular() {
    await concluir();
  }

  const atual = STEPS[step];
  const ultimo = step === STEPS.length - 1;

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-card">
        {/* Indicadores de passo */}
        <div className="ob-step-indicator">
          {STEPS.map((_, i) => (
            <div key={i} className={`ob-dot${i === step ? " active" : ""}`} />
          ))}
        </div>

        {/* Ícone */}
        <div
          className="ob-icon"
          style={{ background: atual.iconBg, color: atual.iconColor }}
        >
          {atual.icon}
        </div>

        {/* Conteúdo */}
        <div className="ob-title">{atual.titulo}</div>
        <p className="ob-desc">{atual.desc}</p>

        {atual.destaque && (
          <div className="ob-highlight">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            {atual.destaque}
          </div>
        )}

        {/* Ações */}
        <div className="ob-actions">
          {!ultimo ? (
            <>
              <button className="ob-skip" onClick={pular}>
                Pular
              </button>
              <button
                className="btn ob-next"
                onClick={() => setStep((s) => s + 1)}
              >
                Próximo →
              </button>
            </>
          ) : (
            <button
              className="btn ob-next"
              onClick={concluir}
              disabled={fechando}
              style={{ flex: 1 }}
            >
              {fechando ? "Carregando..." : "Começar a consultar 🚀"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
