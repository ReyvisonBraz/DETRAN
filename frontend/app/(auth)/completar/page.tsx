"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { updateDoc, doc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useRouter } from "next/navigation";

export default function CompletarPerfilPage() {
  const { user, profile, refreshProfile } = useAuth();
  const router = useRouter();
  const [nome, setNome] = useState(profile?.nome || user?.displayName?.split(" ")[0] || "");
  const [sobrenome, setSobrenome] = useState(profile?.sobrenome || user?.displayName?.split(" ").slice(1).join(" ") || "");
  const [telefone, setTelefone] = useState(profile?.telefone || "");
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState("");

  async function salvar() {
    if (!nome.trim()) { setErro("Informe seu nome."); return; }
    if (!sobrenome.trim()) { setErro("Informe seu sobrenome."); return; }
    if (!user) return;

    setSalvando(true);
    setErro("");
    try {
      await updateDoc(doc(db, "users", user.uid), {
        nome: nome.trim(),
        sobrenome: sobrenome.trim(),
        telefone: telefone.trim() || null,
        perfilCompleto: true,
        updatedAt: new Date(),
      });
      await refreshProfile();
      router.push("/dashboard");
    } catch {
      setErro("Erro ao salvar. Tente novamente.");
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
          </svg>
        </div>
        <h1 className="auth-title">Complete seu cadastro</h1>
        <p className="auth-subtitle">Precisamos de algumas informações para continuar.</p>

        {user?.photoURL && (
          <div className="auth-photo">
            <img src={user.photoURL} alt="Foto" referrerPolicy="no-referrer" />
          </div>
        )}

        <div className="auth-fields">
          <div className="field">
            <label>Nome *</label>
            <input
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              placeholder="Primeiro nome"
            />
          </div>
          <div className="field">
            <label>Sobrenome *</label>
            <input
              value={sobrenome}
              onChange={(e) => setSobrenome(e.target.value)}
              placeholder="Sobrenome"
            />
          </div>
          <div className="field">
            <label>WhatsApp (opcional)</label>
            <input
              value={telefone}
              onChange={(e) => setTelefone(e.target.value)}
              placeholder="(91) 99999-9999"
            />
          </div>
        </div>

        {erro && <p className="auth-error">{erro}</p>}

        <button className="btn btn-primary" onClick={salvar} disabled={salvando}>
          {salvando ? "Salvando..." : "Continuar"}
        </button>
      </div>
    </div>
  );
}