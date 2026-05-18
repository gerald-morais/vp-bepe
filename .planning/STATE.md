# Project State: VP-GPS

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-18)

**Core value:** Identificar e visualizar no mapa todos os pontos de telemetria onde uma VP saiu do perímetro autorizado em determinado turno de escala.
**Current focus:** Phase 2 — Interface Streamlit (Plan 01/3 complete)

## Current Phase

**Phase 2: Interface Streamlit**
Status: In progress (Plan 01 of 3 complete)
Goal: Interface interativa completa com filtros em cascata, mapa geoespacial e tabela de infrações.

### Completed Plans

- **Plan 01: map_renderer.py** — Complete 2026-05-18
  - Módulo puro Folium: render_map(df, polygon) → folium.Map
  - Helpers: _add_perimeter, _add_route, _add_markers, _compute_bounds
  - Commit: 712da3e

### Key Decisions (Phase 2)

- `folium.Map()` sem `location=`/`zoom_start=` quando `fit_bounds()` é usado — evita conflito visual
- Coordinate swap obrigatório `(lon,lat)→(lat,lon)` ao converter Shapely→Folium
- Sort cronológico por `pd.to_datetime(dayfirst=True)` para suportar formatos BR e ISO
- Cores: #e67e22 perímetro, #2980b9 rota, #27ae60/#2ecc71 INSIDE, #c0392b/#e74c3c OUTSIDE

## Completed Phases

- **Phase 1: Pipeline de Dados e Cache** — Complete 2026-05-18
  - data_loader.py, geo_engine.py, cache_manager.py
  - Verificação: 11/11 must-haves — human_needed (runtime behaviors requerem Streamlit + dados reais)

## Blockers

(None)

---
*State initialized: 2026-05-18*
