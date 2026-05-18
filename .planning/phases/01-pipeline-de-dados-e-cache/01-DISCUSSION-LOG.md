# Phase 1: Pipeline de Dados e Cache - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-18
**Phase:** 1 - Pipeline de Dados e Cache
**Areas discussed:** Arquivo .xls ausente, Orquestração dos módulos

---

## Arquivo .xls ausente

| Option | Description | Selected |
|--------|-------------|----------|
| Aviso na UI + continua | st.warning() exibindo nome da VP e arquivo esperado | ✓ |
| Pula silenciosamente | Log interno sem output visual | |

**User's choice:** Aviso na UI + continua

| Option | Description | Selected |
|--------|-------------|----------|
| Durante o processamento | st.warning() em tempo real junto com a barra de progresso | ✓ |
| Resumo no final | Bloco único de avisos ao final do processamento | |

**User's choice:** Durante o processamento (em tempo real junto com a barra de progresso)

---

## Orquestração dos módulos

| Option | Description | Selected |
|--------|-------------|----------|
| cache_manager encapsula tudo | app.py chama get_or_process_data(), cache_manager coordena internamente | ✓ |
| app.py coordena | app.py chama data_loader, geo_engine, cache_manager diretamente | |

**User's choice:** cache_manager.py encapsula tudo

| Option | Description | Selected |
|--------|-------------|----------|
| Apaga .db e reprocessa | Deleta dados_processados.db, mantém st.session_state | ✓ |
| Apaga .db + reseta sessão | Deleta banco E limpa st.session_state | |

**User's choice:** Apaga .db e reprocessa (mantém filtros da sessão)

---

## Claude's Discretion

- **Schema do SQLite:** Incluir colunas de escala (VP, CMT, Motorista, Data, Horário) junto à telemetria para evitar JOINs no app
- **sqlite3 vs SQLAlchemy:** Usar sqlite3 nativo (mais simples, sem dependência extra para pendrive)

## Deferred Ideas

Nenhuma.
