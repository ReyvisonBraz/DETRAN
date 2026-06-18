"use client";

import { useState } from "react";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { useAuth } from "@/lib/auth";

interface Props {
  jobId: string;
}

export default function FeedbackWidget({ jobId }: Props) {
  const { user } = useAuth();
  const [avaliacao, setAvaliacao] = useState<"positivo" | "negativo" | null>(null);
  const [comentario, setComentario] = useState("");
  const [enviado, setEnviado] = useState(false);
  const [enviando, setEnviando] = useState(false);

  async function enviar(tipo: "positivo" | "negativo") {
    if (!user) return;
    setAvaliacao(tipo);
  }

  async function confirmar() {
    if (!user || !avaliacao) return;
    setEnviando(true);
    try {
      await setDoc(doc(db, "feedbacks", `${user.uid}_${jobId}`), {
        uid: user.uid,
        jobId,
        avaliacao,
        comentario: comentario.trim() || null,
        createdAt: serverTimestamp(),
      });
      setEnviado(true);
    } catch {
      // silencioso — feedback não é crítico
      setEnviado(true);
    } finally {
      setEnviando(false);
    }
  }

  if (enviado) {
    return (
      <div className="feedback-widget">
        <div className="feedback-sent">
          {avaliacao === "positivo" ? "😊" : "🙏"} Obrigado pelo seu feedback! Isso nos ajuda a melhorar.
        </div>
      </div>
    );
  }

  return (
    <div className="feedback-widget">
      <div className="feedback-title">
        Como foi essa consulta?
      </div>
      <div className="feedback-buttons">
        <button
          className={`feedback-btn positivo${avaliacao === "positivo" ? " active" : ""}`}
          onClick={() => enviar("positivo")}
        >
          👍 Satisfeito
        </button>
        <button
          className={`feedback-btn negativo${avaliacao === "negativo" ? " active" : ""}`}
          onClick={() => enviar("negativo")}
        >
          👎 Insatisfeito
        </button>
      </div>

      {avaliacao && (
        <>
          <textarea
            className="feedback-textarea"
            placeholder={
              avaliacao === "positivo"
                ? "Tem algum elogio ou sugestão? (opcional)"
                : "O que aconteceu? Nos conte para melhorar... (opcional)"
            }
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            maxLength={400}
          />
          <button
            className="btn"
            style={{ width: "100%", justifyContent: "center" }}
            onClick={confirmar}
            disabled={enviando}
          >
            {enviando ? <><span className="btn-spinner" /> Enviando...</> : "Enviar feedback"}
          </button>
        </>
      )}
    </div>
  );
}
