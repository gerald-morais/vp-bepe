---
plan: 01-02
phase: 01-pipeline-de-dados-e-cache
status: complete
---

# Summary: Plan 01-02 — Geo Engine

## What Was Built

`geo_engine.py` com três funções para carregamento de KML e verificação de geofencing por ponto e por DataFrame.

## Files Created

- `geo_engine.py`

## Functions Exported

- `load_perimeter()` — lê `perimetro.kml` com `fastkml.KML().from_string()`, extrai o primeiro polígono via traversal recursivo, retorna `shapely.geometry.Polygon`; levanta `FileNotFoundError` se KML ausente, `ValueError` se nenhum polígono encontrado
- `check_status(lat, lon, polygon)` — cria `Point(lon, lat)` (ordem Shapely: x=longitude, y=latitude) e retorna `'INSIDE'` ou `'OUTSIDE'`
- `apply_geofencing(df, polygon)` — aplica `check_status` a cada linha via `df.apply()`, trata `NaN` e erros de tipo como `'OUTSIDE'`, retorna cópia do DataFrame com coluna `'Status'`

## Decisions Made

- Traversal recursivo do KML (`_extract_polygon`) para suportar estruturas KML aninhadas (Document → Folder → Placemark)
- `Point(lon, lat)` — longitude primeiro, conforme convenção Shapely (x=lon, y=lat)
- Coordenadas NaN ou inválidas → `'OUTSIDE'` por segurança (não interrompe o processamento)
- `df = df.copy()` em `apply_geofencing` — não modifica o DataFrame original

## Note: fastkml lxml Warning

`fastkml` emite `UserWarning: Package 'lxml' missing. Pretty print will be disabled` se `lxml` não estiver instalado. Isso não afeta o parsing — apenas desabilita pretty-print. Não é necessário instalar `lxml` para o funcionamento correto.

## Self-Check: PASSED

- `from geo_engine import load_perimeter, check_status, apply_geofencing` — importa sem erro
- `import fastkml` e `from shapely.geometry import Point, Polygon` presentes
- `Point(lon, lat)` — ordem correta
- `polygon.contains(point)` presente
- Tratamento de NaN com `pd.isna()` presente
- `df = df.copy()` presente
