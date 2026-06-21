# DECISÃO DEFINITIVA — Liderança e Divisão de Trabalho

> Síntese das 3 avaliações (GLM-5.1, Claude Opus 4.8, Codex GPT-5) · 21/06/2026

---

## Convergência das 3 IAs

| Critério | Consenso? | Detalhe |
|----------|:---------:|---------|
| Claude tem o maior conhecimento prático do motor | ✅ Unânime | Testou, debugou, corrigiu bugs reais |
| GLM tem a melhor visão de produto/arquitetura SaaS | ✅ Unânime | Modelos de dados, fluxos de crédito, roadmap |
| Codex é o mais cauteloso e verificável | ✅ Unânime | Separa "observado" de "planejado" |
| A pasta `DETRAN/` é lixo/cópia | ✅ Unânime | Confirmar e remover |
| Jobs em memória é fragilidade | ✅ Unânime | Precisa de persistência antes de produção |
| Auth/créditos/pagamentos não estão implementados no backend | ✅ Unânime | Apenas planejados |

## Divergência

| Quem deve liderar? | Votação |
|---------------------|---------|
| **Claude Opus 4.8** | GLM-5.1 + Claude Opus 4.8 (2 votos) |
| **Codex GPT-5** | Codex GPT-5 (1 voto) |

---

## DECISÃO FINAL

### Lider técnico: **Claude Opus 4.8**

2 de 3 IAs recomendam, incluindo a GLM-5.1 — que reconheceu as próprias limitações.
A justificativa central é: para **deixar o sistema funcionando**, conhecimento empírico
do runtime (scraping JSF, CAPTCHA, encoding, fluxos de 4 POSTs, bugs já corrigidos)
é o que mais desbloqueia. Codex é mais seguro em premissas, mas não destrava.

### Papéis definitivos

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLAUDE OPUS 4.8 — LÍDER TÉCNICO              │
│                                                                 │
│  • Define prioridades e ordem de execução                       │
│  • Toma decisões finais de arquitetura backend + scraping       │
│  • Debugging do motor JSF, CAPTCHA, encoding, PDF              │
│  • Valida se algo "está funcionando" em execução real           │
│  • Aprova ou rejeita mudanças no motor e no backend             │
│                                                                 │
│  Regra: nada é declarado "funcionando" sem validar no runtime    │
├─────────────────────────────────────────────────────────────────┤
│                    GLM-5.1 — ARQUITETO DE PRODUTO                │
│                                                                 │
│  • Dono do modelo de dados Firestore                            │
│  • Desenha fluxos de negócio (créditos, PIX, Mercado Pago)     │
│  • Especifica telas: dashboard, créditos, admin, perfil        │
│  • Maintém roadmap e checklist de features                     │
│  • Implementa frontend (Next.js + Firebase)                    │
│                                                                 │
│  Regra: toda especificação passa pelo Codex antes de virar código│
├─────────────────────────────────────────────────────────────────┤
                    CODEx GPT-5 — GUARDIÃO DA VERDADE               │
│                                                                 │
│  • Verifica cada afirmação contra o código real                 │
│  • Sinaliza riscos: deps em memória, pasta duplicada, configs  │
│  • Revisa PRs antes de merge                                    │
│  • Garante que "planejado" ≠ "implementado"                     │
│  • Valida segurança e consistência                              │
│                                                                 │
│  Regra: nada entra como premissa sem o Codex confirmar no repo   │
└─────────────────────────────────────────────────────────────────┘
```

### Regra de ouro do trio

```
Nada entra como PREMISSA    sem o Codex confirmar que EXISTE no código.
Nada é declarado FUNCIONANDO sem o Claude validar em EXECUÇÃO REAL.
Nada de PRODUTO avança       sem o GLM ter ESPECIFICADO primeiro.
```

---

## Primeiras 5 decisões a tomar (consenso das 3 IAs)

| # | Decisão | Dono | Critério de aprovação |
|---|---------|------|-----------------------|
| 1 | **Persistência de jobs** — migrar de memória para Redis/Firestore | Claude (lidera) + Codex (valida) | Job sobrevive a restart do processo |
| 2 | **Fix `cnh_pontuacao`** — implementar etapa de follow-up no RENACH | Claude (lidera) | Teste real retorna pontuação |
| 3 | **Remover pasta `DETRAN/` duplicada** | Codex (confirma) + Claude (aprova) | Git limpo, sem referências quebradas |
| 4 | **Commit de `captcha_solver.py`** — revisar mudança local | Codex (revisa) + Claude (aprova) | Commit com mensagem clara |
| 5 | **Auditoria do estado real** — o que funciona vs. o que é só plano | Codex (lidera) | Lista verificada contra o código |

---

## Ordem de trabalho para "deixar funcionando"

```
FASE 1 — Estabilizar o que existe (Claude lidera, Codex valida)
  ├── 1.1  Auditoria: o que REALMENTE funciona vs. planejado
  ├── 1.2  Remover pasta DETRAN/ duplicada
  ├── 1.3  Commit de mudanças pendentes (captcha_solver.py)
  ├── 1.4  Fix cnh_pontuacao (RENACH follow-up)
  └── 1.5  Persistir jobs (Redis ou Firestore)

FASE 2 — Auth e proteção (GLM especifica, Claude implementa, Codex revisa)
  ├── 2.1  Firebase Auth no backend (auth.py, deps.py)
  ├── 2.2  Middleware de autenticação nas rotas
  ├── 2.3  Tela de login + completar perfil (refinar existente)
  └── 2.4  Proteger POST /api/jobs com Bearer token

FASE 3 — Sistema de créditos (GLM lidera design, Claude implementa, Codex revisa)
  ├── 3.1  Crud de transações no Firestore
  ├── 3.2  Desconto de créditos ao criar job
  ├── 3.3  Tela de saldo + extrato
  ├── 3.4  Tela de pacotes de créditos
  └── 3.5  Bônus de cadastro (2 créditos)

FASE 4 — Pagamentos Mercado Pago (GLM lidera, Codex revisa)
  ├── 4.1  Integração Mercado Pago (PIX)
  ├── 4.2  Tela de pagamento com QR Code
  ├── 4.3  Webhook de confirmação
  └── 4.4  Polling de status de pagamento

FASE 5 — Painel Admin (GLM lidera)
  ├── 5.1  Dashboard métricas
  ├── 5.2  CRUD usuários
  ├── 5.3  Transações e configurações
  └── 5.4  Firestore security rules

FASE 6 — Polish + Deploy (Claude lidera)
  ├── 6.1  Rate limiting
  ├── 6.2  Testes E2E
  └── 6.3  Deploy produção
```

---

*Decisão consolidada a partir das avaliações de GLM-5.1, Claude Opus 4.8 e Codex GPT-5.*