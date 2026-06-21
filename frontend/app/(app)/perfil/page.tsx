"use client";

import { useState } from "react";
import { doc, updateDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useAuth } from "@/lib/auth";

export default function PerfilPage() {
  const { user, profile, refreshProfile } = useAuth();
  const [nome, setNome] = useState(profile?.nome || "");
  const [sobrenome, setSobrenome] = useState(profile?.sobrenome || "");
  const [telefone, setTelefone] = useState(profile?.telefone || "");
  const [salvando, setSalvando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  if (!profile || !user) return <div className="center"><div className="spinner" /></div>;

  const initials = `${profile.nome?.[0] || ""}${profile.sobrenome?.[0] || ""}`.toUpperCase();

  async function salvar(e: React.FormEvent) {
    e.preventDefault();
    if (!nome.trim() || !sobrenome.trim()) return;
    setSalvando(true);
    setSucesso(false);
    setErro(null);
    try {
      await updateDoc(doc(db, "users", user!.uid), {
        nome: nome.trim(),
        sobrenome: sobrenome.trim(),
        telefone: telefone.trim(),
      });
      await refreshProfile();
      setSucesso(true);
      setTimeout(() => setSucesso(false), 3000);
    } catch (e: any) {
      setErro("Erro ao salvar. Tente novamente.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div style={{ maxWidth: 480, margin: "0 auto" }}>
      <h1>Meu perfil</h1>
      <p className="subtitle" style={{ textAlign: "left", maxWidth: "none", marginLeft: 0, marginRight: 0 }}>
        Atualize seus dados pessoais.
      </p>

      {/* Avatar */}
      <div style={{
        display: "flex", alignItems: "center", gap: 16,
        background: "var(--glass)", border: "1px solid var(--border)",
        borderRadius: "var(--radius)", padding: "20px 24px", marginBottom: 24,
      }}>
        <div style={{
          width: 56, height: 56, borderRadius: "50%",
          background: "linear-gradient(135deg, var(--primary), var(--primary-2))",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "1.3rem", fontWeight: 700, color: "#fff", flexShrink: 0,
        }}>
          {initials || "?"}
        </div>
        <div>
          <div style={{ fontWeight: 600, fontSize: "1rem", color: "var(--text)" }}>
            {profile.nome} {profile.sobrenome}
          </div>
          <div style={{ fontSize: ".82rem", color: "var(--muted)", marginTop: 2 }}>
            {profile.email}
          </div>
          <div style={{ fontSize: ".78rem", color: "var(--muted)", marginTop: 4 }}>
            Código: <span style={{ color: "var(--primary-2)", fontWeight: 600, letterSpacing: 1 }}>
              {profile.codigoIndicacao || "—"}
            </span>
          </div>
        </div>
      </div>

      {/* Formulário */}
      <form onSubmit={salvar} style={{
        background: "var(--glass)", border: "1px solid var(--border)",
        borderRadius: "var(--radius)", padding: "24px",
      }}>
        <div className="form-fields" style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr" }}>
          <div className="field">
            <label>Nome <span className="required-mark">*</span></label>
            <input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Seu nome"
              required
            />
          </div>
          <div className="field">
            <label>Sobrenome <span className="required-mark">*</span></label>
            <input
              value={sobrenome}
              onChange={(e) => setSobrenome(e.target.value)}
              placeholder="Seu sobrenome"
              required
            />
          </div>
        </div>

        <div className="field" style={{ marginTop: 16 }}>
          <label>Telefone / WhatsApp</label>
          <input
            value={telefone}
            onChange={(e) => setTelefone(e.target.value)}
            placeholder="(00) 90000-0000"
          />
        </div>

        <div className="field" style={{ marginTop: 16 }}>
          <label>E-mail</label>
          <input value={profile.email} disabled style={{ opacity: .5, cursor: "not-allowed" }} />
          <div className="help">E-mail vinculado à conta Google — não pode ser alterado.</div>
        </div>

        {sucesso && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginTop: 16,
            background: "rgba(16,185,129,.08)", border: "1px solid rgba(16,185,129,.25)",
            borderRadius: 8, padding: "10px 14px", color: "#6ee7b7", fontSize: ".85rem", fontWeight: 500,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
            Dados salvos com sucesso!
          </div>
        )}

        {erro && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8, marginTop: 16,
            background: "rgba(244,63,94,.08)", border: "1px solid rgba(244,63,94,.25)",
            borderRadius: 8, padding: "10px 14px", color: "#fda4af", fontSize: ".85rem",
          }}>
            {erro}
          </div>
        )}

        <button
          type="submit"
          className="btn"
          style={{ width: "100%", justifyContent: "center", marginTop: 20 }}
          disabled={salvando || !nome.trim() || !sobrenome.trim()}
        >
          {salvando ? <><span className="btn-spinner" /> Salvando...</> : "Salvar alterações"}
        </button>
      </form>

      {/* Stats */}
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginTop: 20,
      }}>
        {[
          { label: "Créditos", value: profile.saldoCreditos },
          { label: "Consultas", value: profile.totalConsultas ?? 0 },
          { label: "Membro desde", value: profile.createdAt
            ? new Date((profile.createdAt as any).toDate?.() ?? profile.createdAt).toLocaleDateString("pt-BR", { month: "short", year: "numeric" })
            : "—" },
        ].map((s) => (
          <div key={s.label} style={{
            background: "var(--glass)", border: "1px solid var(--border)",
            borderRadius: "var(--radius-sm)", padding: "16px 12px", textAlign: "center",
          }}>
            <div style={{ fontSize: "1.3rem", fontWeight: 700, color: "var(--text)" }}>{s.value}</div>
            <div style={{ fontSize: ".72rem", color: "var(--muted)", marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
