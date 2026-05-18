# Phase 2: Interface Streamlit - Pattern Map

**Mapped:** 2026-05-18
**Files analyzed:** 2 new files
**Analogs found:** 2 / 2

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `app.py` | controller (entry point) | request-response | `cache_manager.py` | role-match (both are top-level orchestrators with st.* calls) |
| `map_renderer.py` | utility / renderer | transform (DataFrame + Polygon → folium.Map) | `geo_engine.py` | role-match (pure-function module, no st.*, receives data returns result) |

---

## Pattern Assignments

### `app.py` (controller / entry point, request-response)

**Primary analog:** `cache_manager.py`

**Imports pattern** (`cache_manager.py` lines 1–8):
```python
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from data_loader import load_schedule, load_telemetry
from geo_engine import load_perimeter, apply_geofencing
```

**Imports for `app.py`** — derived from analog + RESEARCH.md integration map:
```python
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from cache_manager import delete_cache, get_or_process_data
from geo_engine import load_perimeter
from map_renderer import render_map
```

Note: No `BASE_DIR` needed in `app.py` because it does no file I/O of its own. All path resolution stays in the modules that own the files.

**Progress bar / st.* usage pattern** (`cache_manager.py` lines 54–86):
```python
progress_bar = st.progress(0, text="Iniciando processamento...")

for idx, row in enumerate(schedule.itertuples(index=False), start=1):
    progress_bar.progress(
        idx / total_vps,
        text=f"Processando VP {vp_name} ({idx}/{total_vps})..."
    )
    try:
        telem_df = load_telemetry(arquivo_num)
    except FileNotFoundError:
        st.warning(
            f"VP **{vp_name}**: arquivo `planilha {arquivo_num}.xls` "
            f"não encontrado. Pulando esta viatura."
        )
        continue

progress_bar.progress(1.0, text="Processamento concluído. Salvando banco...")
progress_bar.empty()
```

Copy the `st.warning()` call style (bold VP name, backtick-quoted filename, Portuguese text) for any error messages in `app.py`.

**Empty-DataFrame guard pattern** (`cache_manager.py` lines 88–92):
```python
if not all_frames:
    return pd.DataFrame(columns=[
        "VP", "CMT", "Motorista", "Data", "Horário",
        "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"
    ])
```

Apply the same column-list guard in `app.py` before accessing `df["Data"].unique()` — if `get_or_process_data()` returns an empty DataFrame, the sidebar should degrade gracefully (empty selectboxes, no crash).

**Core cascade filter pattern** (from RESEARCH.md Pattern 1, lines 169–198):
```python
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
```

Key rule: each level's `options` derives from the narrowed slice of the previous level. No `st.session_state` keys for filter values — Streamlit's re-run model handles cascade reset automatically.

**Map rendering + table pattern** (from RESEARCH.md skeleton, lines 604–623):
```python
if selected_date and selected_vp:
    m = render_map(filtered_df, polygon)
    st_folium(m, use_container_width=True, height=500, returned_objects=[], key="main_map")

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

**Critical st_folium rules (from RESEARCH.md Pattern 2):**
- Always pass `returned_objects=[]` — prevents map pan/zoom from triggering Streamlit reruns
- Always pass `key="main_map"` — prevents component remount (white flash) on each rerun
- Never pass `returned_objects=None` (default) — it returns all interaction data and doubles reruns

---

### `map_renderer.py` (utility / renderer, transform)

**Primary analog:** `geo_engine.py`

**Imports pattern** (`geo_engine.py` lines 1–6):
```python
from pathlib import Path

import fastkml
import pandas as pd
from shapely.geometry import Point, Polygon

BASE_DIR = Path(__file__).parent
```

**Imports for `map_renderer.py`** — no `BASE_DIR` needed (no file I/O):
```python
import folium
import pandas as pd
from shapely.geometry import Polygon
```

`map_renderer.py` must NOT import `streamlit`, `geo_engine`, `cache_manager`, or `data_loader`. It is a pure-function module.

**Function signature pattern** (`geo_engine.py` lines 10–12, 64–65, 83–84):
```python
def load_perimeter() -> Polygon:
def check_status(lat: float, lon: float, polygon: Polygon) -> str:
def apply_geofencing(df: pd.DataFrame, polygon: Polygon) -> pd.DataFrame:
```

Follow the same pattern: typed arguments, typed return, docstring with Args/Returns/Raises sections.

**Public function signature for `map_renderer.py`** (from RESEARCH.md Pattern 3):
```python
def render_map(df: pd.DataFrame, polygon: Polygon) -> folium.Map:
    """Build Folium map with perimeter, route, and colored markers.

    Args:
        df: Filtered DataFrame (10 cols). If empty, renders perimeter only.
        polygon: Shapely Polygon from geo_engine.load_perimeter().

    Returns:
        Configured folium.Map for st_folium().
    """
```

**Private helper naming convention** (`geo_engine.py` lines 46, 99):
```python
def _extract_polygon(node) -> Polygon | None:
def _row_status(row) -> str:
```

Follow the same `_underscore_prefix` convention for private helpers:
- `_add_perimeter(m, polygon)` — draws the KML boundary overlay
- `_add_route(m, df)` — draws the PolyLine chronological route
- `_add_markers(m, df)` — draws per-point CircleMarkers colored by Status
- `_compute_bounds(polygon, df)` — returns `[[min_lat, min_lon], [max_lat, max_lon]]`

**Error guard pattern** (`geo_engine.py` lines 25–30, 38–43):
```python
if not kml_path.exists():
    raise FileNotFoundError(
        f"Arquivo KML não encontrado: {kml_path.name}"
    )
# ...
if polygon is None:
    raise ValueError(
        "Nenhum polígono encontrado em perimetro.kml. ..."
    )
```

Apply the same guard in `_add_route`: check `len(coords) >= 2` before calling `folium.PolyLine` (a line with fewer than 2 points is invalid).

**Defensive copy pattern** (`geo_engine.py` line 97):
```python
df = df.copy()
```

Apply in `_add_route` before calling `.sort_values()` to avoid mutating the caller's DataFrame.

**Core map construction** (from RESEARCH.md complete skeleton, lines 460–546):
```python
def render_map(df: pd.DataFrame, polygon: Polygon) -> folium.Map:
    m = folium.Map(tiles="OpenStreetMap")
    _add_perimeter(m, polygon)
    if not df.empty:
        _add_route(m, df)
        _add_markers(m, df)
        bounds = _compute_bounds(polygon, df)
    else:
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
    df_sorted = df.copy().sort_values("Data_Hora")
    coords = list(zip(df_sorted["Latitude"], df_sorted["Longitude"]))
    if len(coords) >= 2:
        folium.PolyLine(
            locations=coords,
            color="#2980b9",
            weight=3,
            opacity=0.7,
            tooltip="Rota da VP",
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

**Critical coordinate order rule** (RESEARCH.md Pitfall 4):
Shapely `polygon.exterior.coords` yields `(lon, lat)`. Folium `Polygon(locations=...)` expects `(lat, lon)`. Always swap: `[(lat, lon) for lon, lat in polygon.exterior.coords]`.

**Do NOT pass `location=` + `zoom_start=` to `folium.Map()`** when using `fit_bounds()` — they conflict and cause a visual jump. Let `fit_bounds()` own both center and zoom.

---

## Shared Patterns

### BASE_DIR path pattern
**Source:** All three Phase 1 files (`data_loader.py` line 5, `geo_engine.py` line 7, `cache_manager.py` line 10)
**Apply to:** Any file that reads files from the project directory

```python
# data_loader.py line 5 / geo_engine.py line 7 / cache_manager.py line 10
BASE_DIR = Path(__file__).parent
```

`app.py` and `map_renderer.py` do NOT need `BASE_DIR` because neither performs file I/O directly. File paths are resolved inside `cache_manager.py` and `geo_engine.py` before data reaches Phase 2.

### Error message style (st.warning)
**Source:** `cache_manager.py` lines 70–73
**Apply to:** Any `st.warning()` or `st.error()` call in `app.py`

```python
st.warning(
    f"VP **{vp_name}**: arquivo `planilha {arquivo_num}.xls` "
    f"não encontrado. Pulando esta viatura."
)
```

Convention: bold entity name with `**`, backtick-quoted filenames, Portuguese text, period at end.

### Docstring style
**Source:** `cache_manager.py` lines 16–27, `geo_engine.py` lines 11–22, `data_loader.py` lines 9–17
**Apply to:** All public functions in `app.py` (if any are extracted) and `map_renderer.py`

```python
def function_name(arg: Type) -> ReturnType:
    """One-line summary.

    Longer explanation if needed.

    Args:
        arg: Description.

    Returns:
        Description of return value.

    Raises:
        ErrorType: When this error occurs.
    """
```

### Empty-DataFrame column list
**Source:** `cache_manager.py` lines 89–92
**Apply to:** `app.py` empty-state guard before accessing DataFrame columns

```python
# The 10-column schema — reference when building empty DataFrame guards
["VP", "CMT", "Motorista", "Data", "Horário",
 "Data_Hora", "Endereco", "Latitude", "Longitude", "Status"]
```

### `if __name__ == "__main__"` diagnostic block
**Source:** `cache_manager.py` lines 131–135
**Apply to:** `map_renderer.py` (optional but consistent with project style)

```python
if __name__ == "__main__":
    print("map_renderer.py importado com sucesso.")
    print("Funções exportadas: render_map")
```

---

## No Analog Found

No files in this phase lack an analog. Both `app.py` and `map_renderer.py` have strong role-match analogs in Phase 1.

The folium-specific patterns (`folium.Polygon`, `folium.PolyLine`, `folium.CircleMarker`, `fit_bounds`, `st_folium`) have no codebase analog (Phase 1 did not use folium) — the planner must use RESEARCH.md patterns for those, which are fully specified above in the Pattern Assignments section.

---

## Metadata

**Analog search scope:** `cache_manager.py`, `geo_engine.py`, `data_loader.py` (all Phase 1 files)
**Files scanned:** 3
**Pattern extraction date:** 2026-05-18
