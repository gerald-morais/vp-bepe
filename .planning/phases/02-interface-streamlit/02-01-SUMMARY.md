---
phase: 02-interface-streamlit
plan: 01
subsystem: ui
tags: [folium, shapely, pandas, map_renderer, geofencing, polyline, circlemarker]

requires:
  - phase: 01-pipeline-de-dados-e-cache
    provides: geo_engine.load_perimeter() retorna Polygon; cache_manager retorna DataFrame com 10 colunas incluindo Status/Latitude/Longitude

provides:
  - map_renderer.render_map(df, polygon) → folium.Map com perímetro KML, PolyLine de rota e CircleMarkers coloridos por Status
  - _add_perimeter: polígono laranja semi-transparente com swap (lon,lat)→(lat,lon)
  - _add_route: PolyLine azul cronológica com sort por pd.to_datetime(dayfirst=True)
  - _add_markers: CircleMarker verde (INSIDE r=4) e vermelho (OUTSIDE r=6) com popup Data_Hora+Endereço
  - _compute_bounds: bounds [[min_lat,min_lon],[max_lat,max_lon]] para fit_bounds()

affects: [app.py, 02-02-PLAN.md]

tech-stack:
  added: [folium==0.20.0, branca==0.8.2, xyzservices==2026.3.0]
  patterns:
    - Módulo puro sem import de streamlit — recebe dados, retorna objeto
    - Coordinate swap obrigatório (lon,lat)→(lat,lon) ao converter Shapely→Folium
    - folium.Map(tiles=...) sem location/zoom_start quando fit_bounds() é usado
    - Defensive copy (.copy()) antes de .sort_values() para não mutar DataFrame do caller

key-files:
  created:
    - map_renderer.py
  modified: []

key-decisions:
  - "folium.Map sem location= e zoom_start= para evitar conflito visual com fit_bounds()"
  - "Sort por pd.to_datetime(dayfirst=True) para suportar formato brasileiro DD/MM/YYYY HH:MM:SS"
  - "Cores: #e67e22 perímetro, #2980b9 rota, #27ae60/#2ecc71 INSIDE, #c0392b/#e74c3c OUTSIDE"
  - "Guard len(coords) < 2 em _add_route para evitar PolyLine inválida"
  - "folium instalado como devDependency (pip install folium) — não estava presente no ambiente"

patterns-established:
  - "Pure-function renderer: recebe (df, polygon), retorna objeto configurado, zero side-effects"
  - "Coordinate swap: [(lat, lon) for lon, lat in polygon.exterior.coords]"
  - "fit_bounds sobre polígono (df vazio) ou polígono+rota (df com dados)"

requirements-completed: [UI-02, UI-03, UI-04]

duration: 8min
completed: 2026-05-18
---

# Phase 2 Plan 01: map_renderer.py Summary

**Módulo puro de renderização Folium com polígono KML, PolyLine cronológica e CircleMarkers verdes/vermelhos por Status de geofencing**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-18T00:00:00Z
- **Completed:** 2026-05-18T00:08:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- `render_map(df, polygon)` exportada como única API pública — zero imports de streamlit/geo_engine/cache_manager
- Coordinate swap `(lon,lat)→(lat,lon)` implementado em `_add_perimeter` e `_compute_bounds`, respeitando a diferença entre Shapely (x=lon, y=lat) e Folium (lat, lon)
- `fit_bounds()` gerencia centro e zoom automaticamente — `folium.Map()` criado sem `location=` nem `zoom_start=` para evitar salto visual
- Sort cronológico robusto com `pd.to_datetime(dayfirst=True)` suporta formatos brasileiros (`DD/MM/YYYY HH:MM:SS` e `YYYY-MM-DD HH:MM:SS`)

## Função pública — assinatura exata

```python
def render_map(df: pd.DataFrame, polygon: Polygon) -> folium.Map:
    """Constrói mapa Folium com perímetro, rota e marcadores coloridos."""
```

## Helpers privados

| Helper | Comportamento |
|--------|---------------|
| `_add_perimeter(m, polygon)` | Adiciona `folium.Polygon` laranja (#e67e22, fill_opacity=0.08) com swap obrigatório de coordenadas |
| `_add_route(m, df)` | Adiciona `folium.PolyLine` azul (#2980b9) em ordem cronológica; guard `len(coords) < 2` |
| `_add_markers(m, df)` | Adiciona `folium.CircleMarker` verde r=4 (INSIDE) ou vermelho r=6 (OUTSIDE) com popup |
| `_compute_bounds(polygon, df=None)` | Retorna `[[min_lat, min_lon], [max_lat, max_lon]]` expandido com pontos da rota se df presente |

## Decisões de cores

| Elemento | Cor borda | Cor fill | Opacidade fill |
|----------|-----------|----------|----------------|
| Polígono perímetro | `#e67e22` | `#e67e22` | 0.08 |
| Rota PolyLine | `#2980b9` | — | 0.7 |
| Marcador INSIDE | `#27ae60` | `#2ecc71` | 0.6 |
| Marcador OUTSIDE | `#c0392b` | `#e74c3c` | 0.9 |

## Confirmação do coordinate swap pattern

```python
# _add_perimeter — linha 52:
coords = [(lat, lon) for lon, lat in polygon.exterior.coords]

# _compute_bounds — lê separadamente:
poly_lons = [c[0] for c in polygon.exterior.coords]  # c[0] = lon no Shapely
poly_lats = [c[1] for c in polygon.exterior.coords]  # c[1] = lat no Shapely
```

## Task Commits

1. **Task 1: Criar map_renderer.py com render_map() e helpers privados** - `712da3e` (feat)

**Plan metadata:** (a seguir neste commit)

## Files Created/Modified

- `map_renderer.py` — módulo puro de renderização Folium (155 linhas)

## Decisions Made

- `folium.Map(tiles="OpenStreetMap")` sem `location=` e `zoom_start=` para evitar conflito visual com `fit_bounds()`
- Sort por `pd.to_datetime(df_sorted["Data_Hora"], dayfirst=True)` em vez de sort direto por string para suportar ambos os formatos de data do cache
- Cores escolhidas com contraste suficiente para visualização diurna e com daltonismo parcial: laranja para perímetro, azul para rota, verde/vermelho para status

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Instalação do pacote folium ausente no ambiente**
- **Found during:** Task 1 (verificação de import)
- **Issue:** `import folium` falhava com `ModuleNotFoundError` — folium não instalado
- **Fix:** `pip install folium` (instalou folium==0.20.0, branca==0.8.2, xyzservices==2026.3.0)
- **Files modified:** ambiente Python (não rastreado em git)
- **Verification:** `python -c "import map_renderer; print('OK')"` retorna OK
- **Committed in:** 712da3e (incluído no task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — dependência ausente)
**Impact on plan:** Instalação necessária para execução. Nenhum desvio de escopo.

## Issues Encountered

None além da dependência folium ausente (resolvida via Rule 3).

## User Setup Required

None — nenhuma configuração externa necessária.

## Next Phase Readiness

- `map_renderer.render_map()` pronto para ser importado por `app.py` (Plano 02-02)
- Interface: `render_map(filtered_df, polygon)` para estado com dados; `render_map(pd.DataFrame(), polygon)` para estado inicial
- Dependências folium instaladas e funcionais

---
*Phase: 02-interface-streamlit*
*Completed: 2026-05-18*
