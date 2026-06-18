"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { useRouter } from "next/navigation";

const PACOTES = [
  { creditos: 10, preco: 10, label: "Básico", porCr: "R$1,00/cr" },
  { creditos: 30, preco: 25, label: "Popular", popular: true, porCr: "R$0,83/cr" },
  { creditos: 70, preco: 50, label: "Pro", porCr: "R$0,71/cr" },
];

export default function CreditosPage() {
  const { profile } = useAuth();
  const router = useRouter();
  const [copiado, setCopiado] = useState(false);
  const [pacoteSelecionado, setPacoteSelecionado] = useState<number | null>(null);

  if (!profile) return <div className="center"><div className="spinner" /></div>;

  function copiarCodigo() {
    navigator.clipboard.writeText(profile!.codigoIndicacao || "");
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2000);
  }

  function compartilhar() {
    const texto = `Use meu código *${profile!.codigoIndicacao}* no DETRAN-PA e ganhe 2 créditos grátis! 🚗\nhttps://detran-reyvisonbrazs-projects.vercel.app`;
    if (navigator.share) {
      navigator.share({ text: texto });
    } else {
      navigator.clipboard.writeText(texto);
      alert("Link copiado para a área de transferência!");
    }
  }

  async function comprar(pacote: typeof PACOTES[0]) {
    setPacoteSelecionado(pacote.creditos);
    // TODO: integrar Mercado Pago
    // Por enquanto abre modal de contato
    alert(`Em breve! Para recarregar ${pacote.creditos} créditos por R$${pacote.preco}, entre em contato pelo WhatsApp ou aguarde a integração de pagamento.`);
    setPacoteSelecionado(null);
  }

  return (
    <div className="creditos-page">
      {/* Saldo atual */}
      <div className="creditos-saldo-card">
        <div>
          <div className="creditos-saldo-num">{profile.saldoCreditos}</div>
          <div className="creditos-saldo-label">créditos disponíveis</div>
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ color: "var(--text-2)", fontSize: ".85rem", lineHeight: 1.6 }}>
            Cada consulta consome 1–2 créditos dependendo do tipo.<br />
            Em caso de falha técnica do sistema, os créditos são <strong style={{ color: "var(--emerald)" }}>devolvidos automaticamente</strong>.
          </p>
        </div>
      </div>

      {/* Pacotes */}
      <div>
        <h2>Recarregar créditos</h2>
        <div className="pacotes-grid">
          {PACOTES.map((p) => (
            <div key={p.creditos} className={`pacote-card${p.popular ? " popular" : ""}`}>
              <div className="pacote-creditos">
                {p.creditos} <span>CR</span>
              </div>
              <div className="pacote-preco">R$ {p.preco}</div>
              <div className="pacote-por-cr">{p.porCr}</div>
              <button
                className="btn"
                style={{ width: "100%", justifyContent: "center", padding: "10px" }}
                onClick={() => comprar(p)}
                disabled={pacoteSelecionado === p.creditos}
              >
                {pacoteSelecionado === p.creditos ? (
                  <><span className="btn-spinner" /> Aguarde...</>
                ) : (
                  <>Comprar via Pix</>
                )}
              </button>
            </div>
          ))}
        </div>
        <p style={{ fontSize: ".75rem", color: "var(--muted)", marginTop: 10, textAlign: "center" }}>
          Pagamento via Pix ou cartão • Créditos adicionados instantaneamente após confirmação
        </p>
      </div>

      {/* Código de indicação */}
      <div className="indicacao-card">
        <h2 style={{ margin: 0 }}>Indique e ganhe</h2>
        <p style={{ fontSize: ".85rem", color: "var(--muted)", margin: "8px 0 0", lineHeight: 1.6 }}>
          Compartilhe seu código. Quando um amigo se cadastrar usando ele, vocês dois ganham <strong style={{ color: "var(--emerald)" }}>+2 créditos</strong> cada.
        </p>
        <div className="indicacao-code-wrap">
          <div className="indicacao-code">{profile.codigoIndicacao || "—"}</div>
          <button className="btn btn-secondary" onClick={copiarCodigo} style={{ flexShrink: 0 }}>
            {copiado ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                Copiado
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                Copiar
              </>
            )}
          </button>
          <button className="btn" onClick={compartilhar} style={{ flexShrink: 0 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>
            Compartilhar
          </button>
        </div>
        <p className="indicacao-info">
          💡 Seu código é único e permanente. Cada indicação válida adiciona créditos automaticamente para ambos.
        </p>
      </div>

      {/* Histórico de recargas — placeholder */}
      <div>
        <h2>Histórico de recargas</h2>
        <div style={{
          background: "var(--glass)", border: "1px solid var(--border)",
          borderRadius: "var(--radius)", padding: "24px", textAlign: "center",
          color: "var(--muted)", fontSize: ".88rem"
        }}>
          Nenhuma recarga realizada ainda.
        </div>
      </div>
    </div>
  );
}
