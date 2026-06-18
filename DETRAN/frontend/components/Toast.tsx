"use client";

import { useEffect, useState } from "react";

export type ToastType = "success" | "error" | "info";

interface ToastProps {
  mensagem: string;
  tipo?: ToastType;
  duracao?: number; // ms
  onClose: () => void;
}

export default function Toast({ mensagem, tipo = "info", duracao = 4000, onClose }: ToastProps) {
  const [saindo, setSaindo] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => {
      setSaindo(true);
      setTimeout(onClose, 300);
    }, duracao);
    return () => clearTimeout(t);
  }, [duracao, onClose]);

  const icone =
    tipo === "success" ? (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ) : tipo === "error" ? (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
    ) : (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    );

  return (
    <div
      className={`toast toast-${tipo}${saindo ? " toast-saindo" : ""}`}
      role="alert"
      onClick={() => { setSaindo(true); setTimeout(onClose, 300); }}
    >
      <span className="toast-icon">{icone}</span>
      <span className="toast-msg">{mensagem}</span>
    </div>
  );
}
