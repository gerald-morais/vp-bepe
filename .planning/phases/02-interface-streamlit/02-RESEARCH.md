# Phase 2: Interface Streamlit - Research

**Researched:** 2026-05-18
**Domain:** Streamlit UI + Folium maps + cascade filters
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Estado inicial: mapa vazio centrado no perímetro KML, instrução na tela ("Selecione uma Data e VP..."). Nenhum dado antes de Data + VP selecionadas.
- **D-02:** Cascata real: Data filtra VPs; VP filtra CMT; CMT filtra Motorista.
- **D-03:** CMT e Motorista são opcionais — mapa e tabela aparecem com apenas Data + VP.
- **D-04:** Popup nos marcadores: Data_Hora e Endereço em ambos os tipos (INSIDE e OUTSIDE).
- **D-05:** PolyLine conecta todos os pontos da VP em ordem cronológica de Data_Hora (INSIDE + OUTSIDE).
- **D-06:** fit_bounds() sobre o polígono KML ao inicializar; re-aplicar sobre polígono + pontos da rota ao selecionar VP.
- **D-07:** Tabela: colunas Data_Hora, Endereço, Latitude, Longitude — apenas Status == 'OUTSIDE'.
- **D-08:** Título dinâmico: "VP-XYZ: N registros fora do perímetro".
- **D-09:** VP sem OUTSIDE → st.success("VP XYZ permaneceu dentro do perímetro em todo o turno.").
- **D-10:** Banco ausente → processar automaticamente via get_or_process_data() com barra de progresso do cache_manager. Sem tela de boas-vindas extra.

### Claude's Discretion

- Cores exatas dos marcadores: azul ou verde para INSIDE, vermelho para OUTSIDE.
- Estilo da PolyLine: espessura, cor, opacidade.
- Tile base do mapa: OpenStreetMap padrão.
- Layout exato da sidebar: ordem, separadores, help text.
- Estrutura interna de map_renderer.py: assinatura da função pública.

### Deferred Ideas (OUT OF SCOPE)

- Exportação CSV/PDF (EXPRT-01 — v2)
- Filtro por horário de turno (TURNO-01 — v2)
- Paginação ou limite de linhas na tabela
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Filtros em cascata na sidebar: Data → VP → CMT → Motorista | Cascade filter pattern with DataFrame masking |
| UI-02 | Mapa interativo (streamlit-folium) com polígono KML desenhado em overlay | folium.Polygon from shapely.exterior.coords + st_folium() |
| UI-03 | Rota da VP como PolyLine no mapa | folium.PolyLine(locations=list_of_lat_lon) |
| UI-04 | INSIDE = azul/verde markers; OUTSIDE = vermelho em destaque | folium.Icon(color=...) or folium.CircleMarker |
| UI-05 | Tabela abaixo do mapa — apenas OUTSIDE com 4 colunas | st.dataframe on filtered DataFrame |
</phase_requirements>

---

## Summary

Phase 2 builds the complete Streamlit UI consuming the DataFrame already produced by `cache_manager.get_or_process_data()`. No data processing logic belongs here — the phase is purely UI: sidebar filters, a Folium map inside `st_folium()`, and a filtered results table.

The three key technical domains are: (1) Streamlit's reactive re-run model and how to implement cascade selectboxes without infinite loops, (2) the `st_folium()` API — specifically how `returned_objects=[]` prevents unwanted reruns and how `feature_group_to_add` can be used for efficient updates, and (3) the Folium object model — Polygon, PolyLine, Marker, CircleMarker, fit_bounds.

The central integration pattern is: `app.py` holds all state and filter logic; `map_renderer.py` is a pure function that receives a filtered DataFrame and a shapely Polygon and returns a configured `folium.Map` object ready for `st_folium()`.

**Primary recommendation:** Use `returned_objects=[]` on `st_folium()` so map interactions (pan, zoom) do not trigger Streamlit reruns. Rebuild the entire folium.Map on each filter change — this is simpler and correct for this use case given the full rerun already happens when sidebar widgets change.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Filter state management | Streamlit (app.py) | — | Streamlit re-run model — filters live in the script flow |
| DataFrame subsetting | Streamlit (app.py) | — | Pure pandas operations after each filter selection |
| Map construction | map_renderer.py (function) | — | Encapsulates all folium API calls; returns Map object |
| Map rendering | st_folium() in app.py | — | Component bridges folium Map into Streamlit DOM |
| OUTSIDE table | Streamlit (app.py) | — | st.dataframe on already-filtered slice |
| Reload button | Streamlit (app.py) | cache_manager | Calls delete_cache() + st.rerun() |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| streamlit | 1.57.0 (installed) | App framework, sidebar, widgets, rerun | Locked by project |
| folium | 0.20.0 [VERIFIED: pypi.org 2026-05-18] | Interactive Leaflet maps | Locked by project |
| streamlit-folium | 0.27.2 [VERIFIED: github.com/randyzwitch 2026-05-18] | Bridge folium → Streamlit | Locked by project |
| pandas | (Phase 1 version) | DataFrame filtering | Already in use |
| shapely | (Phase 1 version) | Polygon exterior coords extraction | Already in use |

### Installation

```bash
pip install folium streamlit-folium
```

**Note:** `streamlit` is already installed (1.57.0). Confirm `folium` and `streamlit-folium` are added to `requirements.txt` in Phase 3.

---

## Architecture Patterns

### System Architecture Diagram

```
Streamlit re-run cycle
─────────────────────────────────────────────────────────────────────
  app.py starts
       │
       ▼
  get_or_process_data()          ← cache_manager (Phase 1)
       │  returns full DataFrame (10 cols)
       ▼
  SIDEBAR FILTERS
  ┌─────────────────────────────────────────────────┐
  │  st.selectbox("Data")                           │
  │    │  masks df → dates available                │
  │  st.selectbox("VP")    ← options from date mask │
  │    │  masks df → vps on that date               │
  │  st.selectbox("CMT")   ← options from vp mask   │
  │  st.selectbox("Motorista") ← options from cmt   │
  │  st.button("Recarregar Banco de Dados")         │
  └─────────────────────────────────────────────────┘
       │  filtered_df (rows matching selections)
       ▼
  if Data + VP selected:
       │
       ├──► map_renderer.render_map(filtered_df, polygon)
       │         │ builds folium.Map
       │         │   folium.Polygon  ← perimeter overlay
       │         │   folium.PolyLine ← route (all points, chronological)
       │         │   folium.Marker   ← per point (color by Status)
       │         │   m.fit_bounds()  ← auto-zoom to perimeter + route
       │         └─ returns folium.Map object
       │
       ├──► st_folium(m, returned_objects=[], use_container_width=True)
       │         renders map in Streamlit (no interaction reruns)
       │
       └──► outside_df = filtered_df[filtered_df.Status == 'OUTSIDE']
            st.subheader(f"VP-{vp}: {len(outside_df)} registros fora do perímetro")
            if len(outside_df) == 0:
                st.success("VP permaneceu dentro do perímetro...")
            else:
                st.dataframe(outside_df[['Data_Hora','Endereco','Latitude','Longitude']])
  else:
       └──► show empty map centered on perimeter + instruction text
```

### Recommended Project Structure

```
./
├── app.py               # Entry point: Streamlit layout, sidebar, filter logic
├── map_renderer.py      # Pure function: render_map(df, polygon) -> folium.Map
├── data_loader.py       # Phase 1
├── geo_engine.py        # Phase 1
├── cache_manager.py     # Phase 1
└── ...
```

### Pattern 1: Streamlit Cascade Filters (no session_state needed)

**What:** Each selectbox's `options` list is derived from a progressively narrower slice of the DataFrame. Streamlit re-runs top-to-bottom on every widget interaction, so each selectbox automatically sees the narrowed options from the one above.

**When to use:** Simple cascade where each level is always a subset of the previous. This project's 4-level cascade (Data → VP → CMT → Motorista) is exactly this pattern.

**How it works:** No `st.session_state` keys are needed for basic cascading. The re-run model handles it: when "Data" changes, Streamlit reruns the whole script; by the time it reaches the VP selectbox, the df_by_date mask already restricts VP options.

```python
# Source: pattern from streamlit community + Context7 /streamlit/streamlit
import streamlit as st
import pandas as pd

# df is the full 10-column DataFrame from cache_manager
df = get_or_process_data()

with st.sidebar:
    # Level 1: Data
    available_dates = sorted(df["Data"].unique())
    selected_date = st.selectbox("Data", options=available_dates)

    # Level 2: VP — restricted to VPs that ran on selected_date
    df_by_date = df[df["Data"] == selected_date]
    available_vps = sorted(df_by_date["VP"].unique())
    selected_vp = st.selectbox("VP", options=available_vps)

    # Level 3: CMT — optional; restricted to VPs on that date
    df_by_vp = df_by_date[df_by_date["VP"] == selected_vp]
    available_cmts = sorted(df_by_vp["CMT"].unique())
    selected_cmt = st.selectbox("CMT (opcional)", options=["Todos"] + list(available_cmts))

    # Level 4: Motorista — optional; restricted by CMT selection
    df_by_cmt = df_by_vp if selected_cmt == "Todos" else df_by_vp[df_by_vp["CMT"] == selected_cmt]
    available_motoristas = sorted(df_by_cmt["Motorista"].unique())
    selected_motorista = st.selectbox("Motorista (opcional)", options=["Todos"] + list(available_motoristas))

# Final filtered DataFrame
filtered_df = df_by_cmt if selected_motorista == "Todos" else df_by_cmt[df_by_cmt["Motorista"] == selected_motorista]
```

**Key insight:** `df_by_date` / `df_by_vp` / `df_by_cmt` are computed sequentially as local variables during each re-run. No explicit session_state needed for the options themselves.

### Pattern 2: st_folium() — Correct Usage

**What:** Renders a `folium.Map` object inside Streamlit and optionally returns interaction data.

**Signature (verified from source):**
```python
st_folium(
    fig,                        # folium.Map or MacroElement
    key=None,                   # str — component key; stable key prevents remount
    height=700,                 # int
    width=None,                 # int or None
    use_container_width=True,   # bool — recommended for responsive layout
    returned_objects=[],        # list — [] = no interaction data returned, NO reruns
    zoom=None,                  # override zoom
    center=None,                # override center as (lat, lon)
    feature_group_to_add=None,  # FeatureGroup or list — update without full remap
)
```

**For this project:** Use `returned_objects=[]` because we do NOT need click data from the map. This prevents the map from triggering Streamlit reruns when the user pans or zooms — critical for smooth UX.

```python
# Source: VERIFIED via randyzwitch/streamlit-folium source (2026-05-18)
from streamlit_folium import st_folium

m = render_map(filtered_df, polygon)
st_folium(m, use_container_width=True, height=500, returned_objects=[])
```

**Stable key:** Use `key="main_map"` so Streamlit does not remount the component unnecessarily between reruns. Without a stable key, the component remounts on every rerun, causing a full white-flash redraw.

### Pattern 3: Folium Map Construction (map_renderer.py)

**Function signature (Claude's discretion per CONTEXT.md):**

```python
# Source: VERIFIED against folium 0.20.0 API (Context7 /python-visualization/folium)
import folium
from shapely.geometry import Polygon

def render_map(df: pd.DataFrame, polygon: Polygon, empty: bool = False) -> folium.Map:
    """Build a Folium map for the given filtered DataFrame and perimeter polygon.

    Args:
        df: Filtered DataFrame (10 cols). May be empty if no VP selected.
        polygon: Shapely Polygon from geo_engine.load_perimeter().
        empty: If True, render only the perimeter polygon (no route, no markers).

    Returns:
        Configured folium.Map ready for st_folium().
    """
```

### Pattern 4: Drawing the Perimeter Polygon from Shapely

**Key insight:** Shapely stores coordinates as (lon, lat) — Folium/Leaflet expects (lat, lon). The conversion must swap the order.

```python
# Source: VERIFIED — Shapely docs + Folium Polygon API (Context7 /python-visualization/folium)
import folium
from shapely.geometry import Polygon

def _add_perimeter(m: folium.Map, polygon: Polygon) -> None:
    # shapely exterior.coords gives (lon, lat) pairs — swap to (lat, lon) for Folium
    coords = [(lat, lon) for lon, lat in polygon.exterior.coords]

    folium.Polygon(
        locations=coords,
        color="#e67e22",        # orange border — visually distinct from route/markers
        weight=3,
        fill=True,
        fill_color="#e67e22",
        fill_opacity=0.08,      # very transparent fill, just a hint
        tooltip="Perímetro autorizado",
    ).add_to(m)
```

### Pattern 5: Drawing the Route as PolyLine

```python
# Source: VERIFIED — Context7 /python-visualization/folium PolyLine docs
import folium
import pandas as pd

def _add_route(m: folium.Map, df: pd.DataFrame) -> None:
    # Sort chronologically (D-05: all points, INSIDE + OUTSIDE)
    df_sorted = df.sort_values("Data_Hora")
    coords = list(zip(df_sorted["Latitude"], df_sorted["Longitude"]))

    if len(coords) < 2:
        return  # cannot draw a line with fewer than 2 points

    folium.PolyLine(
        locations=coords,
        color="#2980b9",    # blue route line
        weight=3,
        opacity=0.7,
        tooltip="Rota da VP",
    ).add_to(m)
```

### Pattern 6: Colored Markers per Status

Two options exist. **Use folium.CircleMarker** (not folium.Marker) for better visual density with many telemetry points. CircleMarker uses pixel-radius so they remain readable at all zoom levels.

```python
# Source: VERIFIED — Context7 /python-visualization/folium CircleMarker docs
import folium

def _add_markers(m: folium.Map, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        is_outside = row["Status"] == "OUTSIDE"

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6 if is_outside else 4,
            color="#c0392b" if is_outside else "#27ae60",   # red / green
            fill=True,
            fill_color="#e74c3c" if is_outside else "#2ecc71",
            fill_opacity=0.9 if is_outside else 0.6,
            popup=folium.Popup(
                f"<b>{row['Data_Hora']}</b><br>{row['Endereco']}",
                max_width=250,
            ),
            tooltip=row["Status"],
        ).add_to(m)
```

**Why CircleMarker over Marker:** `folium.Marker` uses a pin icon that stacks poorly with hundreds of telemetry points. CircleMarker is visually cleaner and performs better in the browser for large datasets.

**Available colors for folium.Icon** (if standard pin markers are preferred): `red`, `blue`, `green`, `purple`, `orange`, `darkred`, `lightred`, `beige`, `darkblue`, `darkgreen`, `cadetblue`, `darkpurple`, `white`, `pink`, `lightblue`, `lightgreen`, `gray`, `black`, `lightgray`. [VERIFIED: Context7 /python-visualization/folium]

### Pattern 7: fit_bounds — Auto-zoom

```python
# Source: VERIFIED — Context7 /python-visualization/folium fit_bounds docs
import folium
from shapely.geometry import Polygon

def _compute_bounds(polygon: Polygon, df: pd.DataFrame | None = None):
    """Compute bounding box for fit_bounds.
    Returns [[min_lat, min_lon], [max_lat, max_lon]].
    """
    # Polygon coords are (lon, lat) in shapely
    poly_lons = [c[0] for c in polygon.exterior.coords]
    poly_lats = [c[1] for c in polygon.exterior.coords]

    min_lat, max_lat = min(poly_lats), max(poly_lats)
    min_lon, max_lon = min(poly_lons), max(poly_lons)

    if df is not None and not df.empty:
        min_lat = min(min_lat, df["Latitude"].min())
        max_lat = max(max_lat, df["Latitude"].max())
        min_lon = min(min_lon, df["Longitude"].min())
        max_lon = max(max_lon, df["Longitude"].max())

    return [[min_lat, min_lon], [max_lat, max_lon]]

# Usage in render_map():
bounds = _compute_bounds(polygon, df if not empty else None)
m = folium.Map(tiles="OpenStreetMap")
m.fit_bounds(bounds)
```

**Important:** When constructing `folium.Map()`, do NOT pass `location=` and `zoom_start=` if you will call `fit_bounds()`. Let `fit_bounds()` set both center and zoom. Passing conflicting location+zoom causes a visual jump.

### Anti-Patterns to Avoid

- **Calling `geo_engine.load_perimeter()` inside map_renderer.py:** The polygon should be passed as an argument, not loaded inside the renderer. `app.py` loads it once at startup and passes it down.
- **Rebuilding the map in a cached function:** `folium.Map` objects are not serializable for `@st.cache_data`. Build the map inside the render function without caching.
- **Using `returned_objects=None` (default):** Default behavior returns all interaction data and triggers a Streamlit rerun on every map pan/zoom. This causes the whole page to re-render while the user is navigating the map. Always pass `returned_objects=[]` unless click data is needed.
- **Missing `key=` on st_folium:** Without a stable key, the component is treated as a new instance on each rerun and remounts (white flash). Always pass `key="main_map"`.
- **Sorting by string Data_Hora:** The `Data_Hora` column comes from SQLite as a string (e.g., "2024-01-15 07:32:00"). For chronological sort of PolyLine, call `pd.to_datetime(df['Data_Hora'])` before sorting, or use `df.sort_values('Data_Hora')` only if the format is ISO-sortable (YYYY-MM-DD HH:MM:SS is lexicographically safe).
- **Coordinate order confusion:** Shapely uses (x, y) = (lon, lat). Folium/Leaflet uses (lat, lon). Every coordinate conversion must swap the order explicitly.
- **Large marker count performance:** For datasets with thousands of telemetry points, adding individual markers in a Python loop can be slow and the resulting map heavy in the browser. Consider adding a `folium.plugins.MarkerCluster` for INSIDE points and individual CircleMarkers only for OUTSIDE points if performance is a concern.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Map tile rendering | Custom tile fetcher | OpenStreetMap via folium default | Folium handles tile URLs, attribution, caching |
| Coordinate projection | Manual lat/lon math | folium.Map + fit_bounds | Leaflet handles all projection internally |
| Polygon rendering from KML | KML → HTML canvas | folium.Polygon from shapely coords | Two lines of code; handles winding order |
| Map interactivity (pan, zoom) | Custom JS | Folium + Leaflet (via streamlit-folium) | Battle-tested in-browser interaction |
| HTML popup formatting | Custom HTML template | folium.Popup(html_string) | Supports arbitrary HTML in two lines |

**Key insight:** The entire interactive map stack (tiles, projection, pan/zoom, popups) is handled by Leaflet.js under the hood via folium. The Python layer only assembles layer objects — no geo math, no JS.

---

## Common Pitfalls

### Pitfall 1: Map Rerenders on Every Sidebar Interaction

**What goes wrong:** Every time the user touches a sidebar filter, Streamlit reruns the script. If `st_folium()` is called without `returned_objects=[]`, the map also reacts to its own rendered state, potentially doubling reruns. The user experiences a sluggish UI where the map flickers on every filter change.

**Why it happens:** `st_folium()` default behavior returns all interaction data (clicks, zoom, bounds), which registers as a component value change and triggers additional reruns.

**How to avoid:** Always pass `returned_objects=[]` (display-only) and `key="main_map"`. The map rebuilds on filter changes (which is a full rerun anyway) but does not self-trigger additional reruns.

**Warning signs:** Map flickers twice when a selectbox is changed; console shows repeated component messages.

### Pitfall 2: Cascade Filter Invalid Selection After Parent Changes

**What goes wrong:** User selects Data="2024-01-15" and VP="VP-03". Then changes Data to "2024-01-20" where VP-03 does not exist. The VP selectbox still shows "VP-03" as the selected value even though it's not in the new options list — Streamlit may auto-reset it or may hold the stale value depending on version.

**Why it happens:** Streamlit's selectbox preserves `index=0` when options change, so the selection resets to the first available option. But if the user had typed or the value was set via session_state it can persist.

**How to avoid:** Do not store filter values in `st.session_state` with explicit keys unless necessary. Let Streamlit manage selectbox state naturally — it will reset to index 0 when options change, which is the correct behavior for cascade filters. Never use `st.session_state["selected_vp"] = "VP-03"` pattern for cascade filters.

**Warning signs:** Filtered DataFrame shows 0 rows even though the user sees a valid-looking selection.

### Pitfall 3: Empty DataFrame Crash

**What goes wrong:** If `get_or_process_data()` returns an empty DataFrame (no XLS files found), accessing `df["Data"].unique()` works but `sorted(...)` on an empty array is fine. However, if the code tries to compute bounds from an empty df without checking, `df["Latitude"].min()` returns NaN and `fit_bounds([[nan, nan], [nan, nan]])` causes a JavaScript error in the browser.

**Why it happens:** NaN values propagate silently until they hit the Leaflet bounds calculation.

**How to avoid:** Guard all map construction with `if not filtered_df.empty` checks. The `render_map()` function should handle the `empty=True` case (show only the perimeter polygon) explicitly.

**Warning signs:** Map renders as a grey blank; no error in Python but browser console shows JS errors.

### Pitfall 4: Shapely Coordinate Order Swap

**What goes wrong:** Shapely `polygon.exterior.coords` returns `(lon, lat)` pairs. Folium `Polygon(locations=...)` expects `(lat, lon)` pairs. If passed as-is, the polygon renders in the wrong hemisphere (mirrored across the equator/prime meridian).

**Why it happens:** Shapely follows the mathematical (x, y) convention; geo libraries (Folium, Leaflet) follow geographic (lat, lon) convention.

**How to avoid:** Always convert: `[(lat, lon) for lon, lat in polygon.exterior.coords]`.

**Warning signs:** Polygon renders in the ocean far from the expected location; markers and polygon do not overlap.

### Pitfall 5: Data Column Name "Horário" with Accent

**What goes wrong:** The column is named `Horário` (with accent). Python dict/DataFrame access is fine but it can cause encoding issues in `st.dataframe` column headers or `to_csv` exports on some Windows locales.

**Why it happens:** The column name was established in Phase 1 from the source XLS schema.

**How to avoid:** Access this column only as `df["Horário"]` (with accent) — it is correct and consistent. Do not rename it. For the OUTSIDE table (UI-05), this column is not included anyway (only Data_Hora, Endereco, Latitude, Longitude).

---

## Code Examples

### Complete map_renderer.py skeleton

```python
# Source: patterns VERIFIED via Context7 /python-visualization/folium + /randyzwitch/streamlit-folium
from pathlib import Path

import folium
import pandas as pd
from shapely.geometry import Polygon


def render_map(df: pd.DataFrame, polygon: Polygon) -> folium.Map:
    """Build Folium map with perimeter, route, and colored markers.

    Args:
        df: Filtered DataFrame (10 cols). If empty, renders perimeter only.
        polygon: Shapely Polygon from geo_engine.load_perimeter().

    Returns:
        Configured folium.Map for st_folium().
    """
    m = folium.Map(tiles="OpenStreetMap")

    # Always draw the perimeter (UI-02)
    _add_perimeter(m, polygon)

    if not df.empty:
        # Draw route (UI-03)
        _add_route(m, df)
        # Draw colored markers (UI-04)
        _add_markers(m, df)
        # Fit bounds to perimeter + route (D-06)
        bounds = _compute_bounds(polygon, df)
    else:
        # Initial state: center on perimeter only (D-01, D-06)
        bounds = _compute_bounds(polygon)

    m.fit_bounds(bounds)
    return m


def _add_perimeter(m: folium.Map, polygon: Polygon) -> None:
    coords = [(lat, lon) for lon, lat in polygon.exterior.coords]
    folium.Polygon(
        locations=coords,
        color="#e67e22",
        weight=3,
        fill=True,
        fill_color="#e67e22",
        fill_opacity=0.08,
        tooltip="Perímetro autorizado",
    ).add_to(m)


def _add_route(m: folium.Map, df: pd.DataFrame) -> None:
    df_sorted = df.sort_values("Data_Hora")
    coords = list(zip(df_sorted["Latitude"], df_sorted["Longitude"]))
    if len(coords) >= 2:
        folium.PolyLine(
            locations=coords,
            color="#2980b9",
            weight=3,
            opacity=0.7,
        ).add_to(m)


def _add_markers(m: folium.Map, df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        is_outside = row["Status"] == "OUTSIDE"
        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6 if is_outside else 4,
            color="#c0392b" if is_outside else "#27ae60",
            fill=True,
            fill_color="#e74c3c" if is_outside else "#2ecc71",
            fill_opacity=0.9 if is_outside else 0.6,
            popup=folium.Popup(
                f"<b>{row['Data_Hora']}</b><br>{row['Endereco']}",
                max_width=250,
            ),
            tooltip=row["Status"],
        ).add_to(m)


def _compute_bounds(polygon: Polygon, df: pd.DataFrame | None = None):
    poly_lons = [c[0] for c in polygon.exterior.coords]
    poly_lats = [c[1] for c in polygon.exterior.coords]
    min_lat, max_lat = min(poly_lats), max(poly_lats)
    min_lon, max_lon = min(poly_lons), max(poly_lons)

    if df is not None and not df.empty:
        min_lat = min(min_lat, df["Latitude"].min())
        max_lat = max(max_lat, df["Latitude"].max())
        min_lon = min(min_lon, df["Longitude"].min())
        max_lon = max(max_lon, df["Longitude"].max())

    return [[min_lat, min_lon], [max_lat, max_lon]]
```

### app.py skeleton (critical flow)

```python
# Source: pattern VERIFIED via Context7 /streamlit/streamlit + /randyzwitch/streamlit-folium
import streamlit as st
from cache_manager import get_or_process_data, delete_cache
from geo_engine import load_perimeter
from map_renderer import render_map
from streamlit_folium import st_folium

st.set_page_config(page_title="VP-GPS", layout="wide")
st.title("Rastreador de Viaturas — VP-GPS")

# Load polygon once (cached below or just called once per rerun — it's fast)
polygon = load_perimeter()

# Load data (from cache or process — D-10: no extra welcome screen)
df = get_or_process_data()

# Sidebar filters
with st.sidebar:
    st.header("Filtros")

    if st.button("Recarregar Banco de Dados"):
        delete_cache()
        st.rerun()

    st.divider()

    available_dates = sorted(df["Data"].unique())
    selected_date = st.selectbox("Data", options=available_dates)

    df_by_date = df[df["Data"] == selected_date]
    available_vps = sorted(df_by_date["VP"].unique())
    selected_vp = st.selectbox("VP", options=available_vps)

    df_by_vp = df_by_date[df_by_date["VP"] == selected_vp]
    available_cmts = sorted(df_by_vp["CMT"].unique())
    selected_cmt = st.selectbox("CMT (opcional)", options=["Todos"] + list(available_cmts))

    if selected_cmt == "Todos":
        df_by_cmt = df_by_vp
    else:
        df_by_cmt = df_by_vp[df_by_vp["CMT"] == selected_cmt]

    available_motoristas = sorted(df_by_cmt["Motorista"].unique())
    selected_motorista = st.selectbox(
        "Motorista (opcional)", options=["Todos"] + list(available_motoristas)
    )

    if selected_motorista == "Todos":
        filtered_df = df_by_cmt
    else:
        filtered_df = df_by_cmt[df_by_cmt["Motorista"] == selected_motorista]

# Main area
if selected_date and selected_vp:
    m = render_map(filtered_df, polygon)
    st_folium(m, use_container_width=True, height=500, returned_objects=[], key="main_map")

    # OUTSIDE table (UI-05, D-07, D-08)
    outside_df = filtered_df[filtered_df["Status"] == "OUTSIDE"]
    st.subheader(f"VP-{selected_vp}: {len(outside_df)} registros fora do perímetro")

    if outside_df.empty:
        st.success(f"VP {selected_vp} permaneceu dentro do perímetro em todo o turno.")
    else:
        st.dataframe(
            outside_df[["Data_Hora", "Endereco", "Latitude", "Longitude"]],
            use_container_width=True,
        )
else:
    # Initial empty state (D-01)
    m = render_map(pd.DataFrame(), polygon)
    st_folium(m, use_container_width=True, height=500, returned_objects=[], key="main_map")
    st.info("Selecione uma Data e VP na sidebar para visualizar a rota.")
```

---

## Integration Approach: app.py + map_renderer.py

The split between the two files is determined by a single rule: **map_renderer.py knows nothing about Streamlit**. It imports only `folium`, `pandas`, and `shapely`. It never calls `st.*`. It receives data as arguments and returns a `folium.Map`.

This separation enables:
1. Testing map_renderer.py independently (no Streamlit server needed)
2. Clear responsibility: app.py owns state, map_renderer.py owns rendering

**Import chain:**
```
app.py
  ├── from cache_manager import get_or_process_data, delete_cache
  ├── from geo_engine import load_perimeter
  ├── from map_renderer import render_map
  └── from streamlit_folium import st_folium
```

`map_renderer.py`:
```
  ├── import folium
  ├── import pandas as pd
  └── from shapely.geometry import Polygon
```

`map_renderer.py` does NOT import `geo_engine`, `cache_manager`, or `streamlit`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.12 (Windows) | — |
| streamlit | app.py | ✓ | 1.57.0 (installed) | — |
| folium | map_renderer.py | ✗ (not installed) | 0.20.0 latest | — |
| streamlit-folium | app.py | ✗ (not installed) | 0.27.2 latest | — |
| pandas | filter logic | ✓ (Phase 1 dep) | — | — |
| shapely | polygon coords | ✓ (Phase 1 dep) | — | — |

**Missing dependencies with no fallback:**
- `folium` — must be installed: `pip install folium`
- `streamlit-folium` — must be installed: `pip install streamlit-folium`

Both must be added to `requirements.txt` (Phase 3 task).

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Manual smoke test + visual inspection |
| Config file | none |
| Quick run command | `streamlit run app.py` |
| Full suite command | `streamlit run app.py` + manual checklist |

This phase has no automated unit test framework established (Phase 1 did not set one up). Validation is through Streamlit smoke tests.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | How to Verify |
|--------|----------|-----------|---------------|
| UI-01 | Cascade: selecting Date X shows only VPs active on X | Manual | Select 2 different dates; confirm VP list changes |
| UI-01 | CMT/Motorista optional: map renders with only Date+VP | Manual | Select Date+VP, leave CMT=Todos; map must appear |
| UI-02 | KML perimeter polygon appears on map at all times | Visual | Orange polygon visible even without VP selected |
| UI-03 | PolyLine connects all points of selected VP | Visual | Blue line connecting dots visible after VP selection |
| UI-04 | INSIDE = green markers, OUTSIDE = red markers | Visual | Color contrast clearly distinct; counts match Status col |
| UI-05 | Table shows only OUTSIDE rows with exactly 4 columns | Manual | Compare table row count to `df[df.Status=='OUTSIDE']` count |
| D-08 | Title shows correct count | Manual | "VP-XYZ: N registros" matches table row count |
| D-09 | Zero OUTSIDE → green success box, no table | Visual | Test with a VP that has only INSIDE records |
| D-06 | fit_bounds zooms to perimeter on empty state | Visual | On load, perimeter polygon fills map viewport |
| D-06 | fit_bounds re-zooms to perimeter+route after VP select | Visual | Route + perimeter both visible without manual zoom |

### Wave 0 Gaps

- [ ] `app.py` — does not exist yet (Wave 0 creates it)
- [ ] `map_renderer.py` — does not exist yet (Wave 0 creates it)
- No test framework installation needed (manual validation only)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `folium_static()` function | `st_folium()` function | streamlit-folium v0.7+ | `st_folium` returns interaction data; `folium_static` was display-only |
| `st.cache` decorator | `st.cache_data` / `st.cache_resource` | Streamlit 1.18 | Old `st.cache` removed; not applicable here (Map not cached) |

**Deprecated/outdated:**
- `folium_static()`: The old display-only function from early streamlit-folium. Still importable but superseded by `st_folium()`. Do NOT use `folium_static` — it does not support `returned_objects`, `feature_group_to_add`, or `key` parameters.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `Data_Hora` strings from SQLite are ISO format (YYYY-MM-DD HH:MM:SS) making lexicographic sort safe for chronological order | Pattern 5 (PolyLine) | Route connects points out of order if format is different |
| A2 | The `Endereco` column name in the DataFrame matches exactly — no accent or casing variation | Pattern 6 (Markers) | KeyError when building popup |
| A3 | Number of telemetry points per VP per day is small enough (< 5000) that per-row CircleMarker loop is acceptable | Pattern 6 | Slow map render; may need MarkerCluster |

**Assumption A1 mitigation:** Phase 1 cache_manager saves `Data_Hora` as a string from the XLS telemetry. Confirm the actual format in a real `.xls` file before relying on lexicographic sort — or unconditionally use `pd.to_datetime()` before `.sort_values()`.

---

## Open Questions

1. **Data_Hora sort safety**
   - What we know: Column is stored as string in SQLite
   - What's unclear: Whether the source XLS uses ISO format "YYYY-MM-DD HH:MM:SS" or Brazilian format "DD/MM/YYYY HH:MM:SS"
   - Recommendation: Use `pd.to_datetime(df['Data_Hora'], dayfirst=True)` for the sort in `_add_route()` to be format-safe, then convert back to string for the popup display

2. **Marker count performance**
   - What we know: No production data available to test with
   - What's unclear: How many telemetry records a typical VP generates per day (100? 10,000?)
   - Recommendation: Implement with individual CircleMarkers first; add `folium.plugins.MarkerCluster` for INSIDE markers only if the map becomes sluggish in practice

---

## Sources

### Primary (HIGH confidence)
- Context7 `/randyzwitch/streamlit-folium` — st_folium API, returned_objects, feature_group_to_add, on_change
- Context7 `/python-visualization/folium` — PolyLine, Polygon, CircleMarker, Marker, Icon, fit_bounds, Popup
- Context7 `/streamlit/streamlit` — st.selectbox, st.sidebar, st.session_state, st.dataframe
- GitHub raw source `randyzwitch/streamlit-folium/__init__.py` — full st_folium parameter list [VERIFIED: 2026-05-18]
- PyPI `folium` — version 0.20.0 confirmed current [VERIFIED: 2026-05-18]

### Secondary (MEDIUM confidence)
- GitHub `randyzwitch/streamlit-folium` — version 0.27.2 (April 2026) [VERIFIED via WebFetch 2026-05-18]
- Streamlit community gist (asehmi) — cascade selectbox pattern [CITED: gist.github.com]

### Tertiary (LOW confidence)
- WebSearch results on cascade filter patterns — corroborates Context7 findings

---

## Metadata

**Confidence breakdown:**
- st_folium API: HIGH — verified from source code
- Folium map elements (Polygon, PolyLine, CircleMarker, fit_bounds): HIGH — verified via Context7
- Cascade filter pattern: HIGH — verified via Context7 + community examples
- Performance with large marker counts: LOW — no production data to test against

**Research date:** 2026-05-18
**Valid until:** 2026-06-18 (folium and streamlit-folium are stable; Streamlit releases frequently but API is stable)
