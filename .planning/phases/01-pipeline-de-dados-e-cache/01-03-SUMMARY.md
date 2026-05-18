---
plan: 01-03
phase: 01-pipeline-de-dados-e-cache
status: complete
---

# Summary: Plan 01-03 — Cache Manager

## What Was Built

`cache_manager.py` — único ponto de entrada para `app.py`. Orquestra `data_loader` + `geo_engine` + SQLite com lógica de cache: na primeira execução processa tudo, nas seguintes lê o banco.

## Files Created

- `cache_manager.py`

## Functions Exported

- `get_or_process_data()` — verifica existência de `dados_processados.db`; se existe, lê diretamente; se não, processa todos os VPs com `st.progress()` VP a VP, aplica geofencing, salva no SQLite e retorna DataFrame consolidado
- `delete_cache()` — apaga `dados_processados.db` sem erro se inexistente; usado pelo botão "Recarregar Banco de Dados" (D-03)

## Schema SQLite (10 colunas)

| Coluna | Tipo | Origem |
|--------|------|--------|
| VP | str | escala |
| CMT | str | escala |
| Motorista | str | escala |
| Data | str | escala |
| Horário | str | escala |
| Data_Hora | str | telemetria |
| Endereco | str | telemetria |
| Latitude | float | telemetria |
| Longitude | float | telemetria |
| Status | str ('INSIDE'/'OUTSIDE') | geofencing |

## Decisions Made

- `sqlite3` nativo (sem SQLAlchemy) — mais simples, sem dependência extra, ideal para pendrive
- Função pública única `get_or_process_data()` — `app.py` nunca importa `data_loader` ou `geo_engine` diretamente (D-02)
- Enriquecimento de telemetria com dados de escala (VP, CMT, Motorista, Data, Horário) — permite filtragem direta do banco sem JOIN
- `FileNotFoundError` capturado por VP → `st.warning()` com nome da VP e arquivo esperado (D-01) → continua processamento para demais VPs
- DataFrame vazio com schema correto retornado se nenhum arquivo encontrado — evita crash em `app.py`

## Interface que app.py deve usar (Phase 2)

```python
from cache_manager import get_or_process_data, delete_cache

df = get_or_process_data()  # DataFrame com 10 colunas pronto para filtros

if st.button("Recarregar Banco de Dados"):
    delete_cache()
    st.rerun()
```

## Self-Check: PASSED

- `from cache_manager import get_or_process_data, delete_cache` — importa sem erro
- `import sqlite3` presente (sem sqlalchemy)
- `from data_loader import load_schedule, load_telemetry` presente
- `from geo_engine import load_perimeter, apply_geofencing` presente
- `if DB_PATH.exists():` — branch de cache hit presente
- `st.progress(` e `st.warning(` presentes
- `except FileNotFoundError:` presente
- Schema com 10 colunas completo
- `DB_PATH.unlink()` em `delete_cache()` com guard `if DB_PATH.exists()`
