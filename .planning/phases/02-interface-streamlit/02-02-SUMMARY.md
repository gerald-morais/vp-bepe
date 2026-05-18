---
phase: 02-interface-streamlit
plan: "02"
subsystem: ui
tags: [streamlit, pandas, folium, streamlit-folium, cascade-filters]

requires:
  - phase: 01-pipeline-de-dados-e-cache
    provides: "cache_manager.get_or_process_data(), delete_cache(); DataFrame com 10 colunas VP/CMT/Motorista/Data/Horário/Data_Hora/Endereco/Latitude/Longitude/Status"
  - phase: 02-interface-streamlit-plan-01
    provides: "map_renderer.render_map(df, polygon) -> folium.Map"

provides:
  - "app.py: entry point Streamlit com page config, carregamento de dados e sidebar com 4 filtros em cascata"
  - "Filtro cascata Data → VP → CMT (opcional) → Motorista (opcional) com mascaramento progressivo por DataFrame slice"
  - "Guard de DataFrame vazio com st.stop() antes de qualquer acesso a colunas"
  - "Botão Recarregar Banco de Dados: delete_cache() + st.rerun()"
  - "Placeholder Plan 03 na área principal com instrução de estado inicial"

affects:
  - "02-interface-streamlit-plan-03: substituirá o bloco placeholder com render_map() + st_folium() + tabela OUTSIDE"

tech-stack:
  added: []
  patterns:
    - "Cascade selectbox sem st.session_state: cada nível deriva options do slice anterior (df_by_date → df_by_vp → df_by_cmt → filtered_df)"
    - "Guard df.empty + st.stop() antes de qualquer df[coluna].unique() para evitar crash com banco vazio"
    - "load_perimeter() propaga FileNotFoundError/ValueError nativamente sem swallowing (T-02-04)"

key-files:
  created:
    - app.py
  modified: []

key-decisions:
  - "NÃO usar st.session_state para valores de filtros — re-run model do Streamlit gerencia cascade reset automaticamente"
  - "Placeholder explícito na área principal (Plan 03) em vez de código incompleto de mapa"
  - "load_perimeter() chamado no topo sem try/except — erro nativo do geo_engine aparece ao usuário via Streamlit (T-02-04)"

patterns-established:
  - "Cascade 4 níveis: sorted(df_col.unique().tolist()) em cada slice progressivo, sem state explícito"
  - "Guard de DataFrame vazio antes do bloco sidebar para evitar crash em .unique()"

requirements-completed:
  - UI-01

duration: 1min
completed: 2026-05-18
---

# Phase 02 Plan 02: app.py — Entry Point Streamlit Summary

**app.py com page config, 4 filtros em cascata (Data→VP→CMT→Motorista), guard de df vazio, botão de reload e placeholder documentado para Plan 03**

## Performance

- **Duration:** 1 min
- **Started:** 2026-05-18T13:38:53Z
- **Completed:** 2026-05-18T13:39:55Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- app.py criado com syntax Python válida, zero funções definidas (script puro)
- 4 selectboxes em cascata operacionais sem st.session_state, cada nível mascarando o anterior via slice de DataFrame
- Guard de DataFrame vazio com st.stop() antes de qualquer acesso a colunas (Pitfall 3 de RESEARCH.md)
- Botão "Recarregar Banco de Dados" chama delete_cache() + st.rerun() corretamente
- Importa exatamente cache_manager, geo_engine, map_renderer, streamlit_folium — sem data_loader (regra D-02 Phase 1)

## Task Commits

Cada task commitada atomicamente:

1. **Task 1: Criar app.py com page config, carregamento de dados e filtros em cascata** - `2036614` (feat)

**Plan metadata:** a ser commitado após SUMMARY

## Files Created/Modified

- `app.py` — Entry point Streamlit: page config, carregamento de polígono e dados, sidebar com 4 filtros em cascata, placeholder Plan 03

## Imports Exatos Presentes em app.py

```python
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cache_manager import delete_cache, get_or_process_data
from geo_engine import load_perimeter
from map_renderer import render_map
```

## Estrutura de Cascata

| Nível | Variável | Fonte das options | Variável de corte |
|-------|----------|-------------------|-------------------|
| 1 | `selected_date` | `sorted(df["Data"].unique())` | `df_by_date` |
| 2 | `selected_vp` | `sorted(df_by_date["VP"].unique().tolist())` | `df_by_vp` |
| 3 | `selected_cmt` | `["Todos"] + sorted(df_by_vp["CMT"].unique().tolist())` | `df_by_cmt` |
| 4 | `selected_motorista` | `["Todos"] + sorted(df_by_cmt["Motorista"].unique().tolist())` | `filtered_df` |

**Confirmação:** `st.session_state` NÃO é usado para nenhum filtro — 0 ocorrências em app.py.

## Estado do Placeholder TODO para Plan 03

```python
# --- Main area: placeholder (Plan 03 will replace this block) ---
if selected_date and selected_vp:
    # TODO Plan 03: render map + OUTSIDE table
    st.info(f"VP **{selected_vp}** selecionada — mapa será exibido aqui (Plan 03).")
else:
    st.info("Selecione uma Data e VP na sidebar para visualizar a rota.")
```

Plan 03 substituirá este bloco por: `render_map(filtered_df, polygon)` + `st_folium()` + tabela OUTSIDE com `st.dataframe()`.

## Known Stubs

| Stub | Arquivo | Linha | Razão |
|------|---------|-------|-------|
| Placeholder de mapa/tabela | app.py | 71-74 | Intencional — Plan 03 integra render_map() + st_folium() + tabela OUTSIDE neste bloco |

## Decisions Made

- NÃO usar `st.session_state` para valores de filtros — re-run model do Streamlit gerencia cascade reset automaticamente (Pitfall 2 de RESEARCH.md)
- `load_perimeter()` chamado sem try/except: erro nativo de geo_engine aparece ao usuário via Streamlit (mitigação T-02-04)
- Placeholder explícito com comentário `# TODO Plan 03` em vez de código de mapa incompleto

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- app.py funcional e commitado — Plan 03 pode substituir o bloco placeholder diretamente
- filtered_df disponível para render_map() no contexto do bloco `if selected_date and selected_vp:`
- polygon disponível como variável no escopo top-level do script

---
*Phase: 02-interface-streamlit*
*Completed: 2026-05-18*
