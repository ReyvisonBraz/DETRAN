import uuid
import logging
from datetime import datetime, timezone

from firebase_admin import firestore

logger = logging.getLogger(__name__)

CUSTO_POR_CONSULTA = 1


def _db():
    from app.firebase_admin import init_firebase
    init_firebase()
    return firestore.client()


def obter_saldo(uid: str) -> int:
    db = _db()
    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict().get("saldoCreditos", 0)
    return 0


def deduzir_creditos(uid: str, quantidade: int, descricao: str = "Consulta") -> dict:
    db = _db()
    user_ref = db.collection("users").document(uid)
    transacao_id = uuid.uuid4().hex

    @firestore.transactional
    def _tx(transaction, _user_ref):
        doc = transaction.get(_user_ref)
        if not doc.exists:
            raise RuntimeError(f"Usuario {uid} nao encontrado")

        saldo = doc.to_dict().get("saldoCreditos", 0)
        if saldo < quantidade:
            raise RuntimeError(
                f"Saldo insuficiente: {saldo} creditos, necessario {quantidade}"
            )

        novo_saldo = saldo - quantidade
        transaction.update(_user_ref, {
            "saldoCreditos": novo_saldo,
            "updatedAt": datetime.now(timezone.utc),
        })

        tx_ref = db.collection("transacoes").document(transacao_id)
        transaction.set(tx_ref, {
            "uid": uid,
            "tipo": "consumo",
            "quantidade": -quantidade,
            "descricao": descricao,
            "saldoApos": novo_saldo,
            "createdAt": datetime.now(timezone.utc),
        })

        return {"sucesso": True, "saldoApos": novo_saldo, "transacaoId": transacao_id}

    return _tx(db.transaction(), user_ref)


def adicionar_creditos(uid: str, quantidade: int, descricao: str = "Recarga") -> dict:
    db = _db()
    user_ref = db.collection("users").document(uid)
    transacao_id = uuid.uuid4().hex

    @firestore.transactional
    def _tx(transaction, _user_ref):
        doc = transaction.get(_user_ref)
        if not doc.exists:
            raise RuntimeError(f"Usuario {uid} nao encontrado")

        saldo = doc.to_dict().get("saldoCreditos", 0)
        novo_saldo = saldo + quantidade
        transaction.update(_user_ref, {
            "saldoCreditos": novo_saldo,
            "updatedAt": datetime.now(timezone.utc),
        })

        tx_ref = db.collection("transacoes").document(transacao_id)
        transaction.set(tx_ref, {
            "uid": uid,
            "tipo": "recarga" if "Recarga" in descricao else "bonus",
            "quantidade": quantidade,
            "descricao": descricao,
            "saldoApos": novo_saldo,
            "createdAt": datetime.now(timezone.utc),
        })

        return {"sucesso": True, "saldoApos": novo_saldo, "transacaoId": transacao_id}

    return _tx(db.transaction(), user_ref)


def obter_historico(uid: str, limite: int = 50) -> list[dict]:
    db = _db()
    docs = (
        db.collection("transacoes")
        .where("uid", "==", uid)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(limite)
        .stream()
    )
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]


def tem_creditos_suficientes(uid: str, quantidade: int = CUSTO_POR_CONSULTA) -> bool:
    return obter_saldo(uid) >= quantidade