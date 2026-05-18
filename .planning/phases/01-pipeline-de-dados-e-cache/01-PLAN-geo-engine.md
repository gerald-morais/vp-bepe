---
phase: 01-pipeline-de-dados-e-cache
plan: 02
type: execute
wave: 1
depends_on: []
files_modified:
  - geo_engine.py
autonomous: true
requirements:
  - GEO-01
  - GEO-02
  - GEO-03

must_haves:
  truths:
    - "load_perimeter() retorna um objeto shapely.geometry.Polygon carregado de perimetro.kml"
    - "check_status(lat, lon, polygon) retorna a string 'INSIDE' ou 'OUTSIDE'"
    - "apply_geofencing(df, polygon) retorna o DataFrame com coluna 'Status' adicionada, cada valor sendo 'INSIDE' ou 'OUTSIDE'"
    - "Se perimetro.kml não existir, FileNotFoundError é levantado com mensagem clara"
  artifacts:
    - path: "geo_engine.py"
      provides: "Carregamento de KML e verificação de geofencing por ponto e por DataFrame"
      exports: ["load_perimeter", "check_status", "apply_geofencing"]
  key_links:
    - from: "geo_engine.load_perimeter"
      to: "perimetro.kml"
      via: "fastkml.KML().from_string() e shapely.geometry.Polygon"
      pattern: "fastkml"
    - from: "geo_engine.apply_geofencing"
      to: "DataFrame com Latitude/Longitude"
      via: "polygon.contains(Point(lon, lat)) para cada linha"
      pattern: "polygon.contains"
---

<objective>
Criar geo_engine.py com três funções: load_perimeter() carrega o polígono KML em um objeto Shapely; check_status() verifica um ponto único; apply_geofencing() aplica a verificação a um DataFrame inteiro e adiciona a coluna Status.

Purpose: Fornece a lógica de geofencing que cache_manager.py aplica a cada registro de telemetria antes de salvar no SQLite.
Output: geo_engine.py com funções load_perimeter, check_status e apply_geofencing documentadas.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
@.planning/phases/01-pipeline-de-dados-e-cache/01-CONTEXT.md
@CLAUDE.md

<interfaces>
<!-- Contrato público de geo_engine.py que cache_manager.py vai consumir -->

```python
# geo_engine.py — interface pública

from pathlib import Path
import pandas as pd
from shapely.geometry import Point, Polygon

BASE_DIR = Path(__file__).parent

def load_perimeter() -> Polygon:
    """
    Lê perimetro.kml com fastkml, extrai o primeiro (e único) polígono,
    retorna shapely.geometry.Polygon.
    Levanta FileNotFoundError se perimetro.kml não existir.
    """

def check_status(lat: float, lon: float, polygon: Polygon) -> str:
    """
    Verifica se o ponto (lat, lon) está dentro do polígono.
    Retorna 'INSIDE' se polygon.contains(Point(lon, lat)) else 'OUTSIDE'.
    Nota: Shapely usa (longitude, latitude) — ordem (x, y).
    """

def apply_geofencing(df: pd.DataFrame, polygon: Polygon) -> pd.DataFrame:
    """
    Adiciona coluna 'Status' ao DataFrame df com 'INSIDE' ou 'OUTSIDE'
    para cada linha, baseado nas colunas Latitude e Longitude.
    Retorna df com coluna Status adicionada.
    """
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Criar load_perimeter() — carregamento do KML com fastkml</name>
  <files>geo_engine.py</files>
  <read_first>
    - CLAUDE.md (fastkml para parsing, Shapely para geometria, paths relativos)
    - .planning/REQUIREMENTS.md (GEO-01)
  </read_first>
  <action>
Criar geo_engine.py com as funções load_perimeter() e check_status():

```python
from pathlib import Path

import fastkml
from shapely.geometry import Point, Polygon
import pandas as pd

BASE_DIR = Path(__file__).parent


def load_perimeter() -> Polygon:
    """Carrega o polígono único de perimetro.kml.

    Usa fastkml para parsing do KML e extrai as coordenadas do primeiro
    Placemark encontrado, convertendo para shapely.geometry.Polygon.

    Returns:
        Shapely Polygon representando o perímetro de atuação.

    Raises:
        FileNotFoundError: Se perimetro.kml não existir no diretório base.
        ValueError: Se nenhum polígono for encontrado no KML.
    """
    kml_path = BASE_DIR / "perimetro.kml"

    if not kml_path.exists():
        raise FileNotFoundError(
            f"Arquivo KML não encontrado: {kml_path.name}"
        )

    kml_content = kml_path.read_bytes()

    kml_obj = fastkml.KML()
    kml_obj.from_string(kml_content)

    # Navegar pela hierarquia KML para encontrar o primeiro polígono
    # fastkml: kml_obj.features() → Document → features() → Folder/Placemark
    polygon = _extract_polygon(kml_obj)

    if polygon is None:
        raise ValueError(
            "Nenhum polígono encontrado em perimetro.kml. "
            "Verifique se o arquivo contém um Placemark com geometria Polygon."
        )

    return polygon


def _extract_polygon(node) -> Polygon | None:
    """Percorre recursivamente os nós KML e retorna o primeiro Polygon encontrado."""
    # Verificar se este nó tem geometria diretamente (Placemark)
    if hasattr(node, "geometry") and node.geometry is not None:
        geom = node.geometry
        # Pode ser Polygon diretamente ou MultiPolygon
        if geom.geom_type == "Polygon":
            return geom
        elif geom.geom_type == "MultiPolygon":
            return list(geom.geoms)[0]

    # Percorrer features filhas (Document, Folder, Placemark aninhado)
    if hasattr(node, "features"):
        for feature in node.features():
            result = _extract_polygon(feature)
            if result is not None:
                return result

    return None


def check_status(lat: float, lon: float, polygon: Polygon) -> str:
    """Verifica se o ponto está dentro do perímetro.

    Args:
        lat: Latitude do ponto.
        lon: Longitude do ponto.
        polygon: Shapely Polygon do perímetro.

    Returns:
        'INSIDE' se o ponto estiver dentro ou na borda do polígono,
        'OUTSIDE' caso contrário.

    Note:
        Shapely Point usa ordem (x, y) = (longitude, latitude).
    """
    point = Point(lon, lat)  # Shapely: x=longitude, y=latitude
    return "INSIDE" if polygon.contains(point) else "OUTSIDE"
```
  </action>
  <verify>
    python -c "from geo_engine import load_perimeter, check_status; print('geo_engine Task 1 imports OK')"
  </verify>
  <acceptance_criteria>
    - geo_engine.py existe em C:\Users\hdusa\Documents\Github\vp-gps\geo_engine.py
    - Contém: `import fastkml`
    - Contém: `from shapely.geometry import Point, Polygon`
    - Contém: `BASE_DIR = Path(__file__).parent`
    - Contém: `kml_path = BASE_DIR / "perimetro.kml"`
    - Contém: `FileNotFoundError` com mensagem incluindo o nome do arquivo
    - Contém: `fastkml.KML()` e `.from_string(`
    - Contém: `Point(lon, lat)` — longitude primeiro, latitude segundo (ordem Shapely)
    - Contém: `polygon.contains(point)`
    - Contém: `return "INSIDE"` e `return "OUTSIDE"`
    - Importação sem erro: python -c "from geo_engine import load_perimeter, check_status; print('OK')"
  </acceptance_criteria>
  <done>load_perimeter() e check_status() definidas em geo_engine.py. KML carregado com fastkml, polígono extraído recursivamente, verificação de ponto com Shapely na ordem correta (lon, lat).</done>
</task>

<task type="auto">
  <name>Task 2: Criar apply_geofencing() — aplicação em massa ao DataFrame</name>
  <files>geo_engine.py</files>
  <read_first>
    - geo_engine.py (estado atual após Task 1 — para não sobrescrever load_perimeter e check_status)
    - .planning/REQUIREMENTS.md (GEO-02, GEO-03)
    - .planning/REQUIREMENTS.md — GEO-03: "Status salvo como coluna 'Status' em cada registro"
  </read_first>
  <action>
Adicionar apply_geofencing() ao final de geo_engine.py existente:

```python
def apply_geofencing(df: pd.DataFrame, polygon: Polygon) -> pd.DataFrame:
    """Aplica verificação de geofencing a cada linha do DataFrame.

    Para cada linha, verifica se o ponto (Latitude, Longitude) está dentro
    do polígono e registra 'INSIDE' ou 'OUTSIDE' na coluna 'Status'.

    Args:
        df: DataFrame com colunas 'Latitude' (float) e 'Longitude' (float).
        polygon: Shapely Polygon do perímetro (de load_perimeter()).

    Returns:
        Cópia do DataFrame com coluna 'Status' adicionada.
        Linhas com Latitude ou Longitude NaN recebem Status='OUTSIDE'.
    """
    df = df.copy()

    def _row_status(row) -> str:
        lat = row["Latitude"]
        lon = row["Longitude"]
        # Tratar coordenadas inválidas como OUTSIDE
        try:
            if pd.isna(lat) or pd.isna(lon):
                return "OUTSIDE"
            return check_status(float(lat), float(lon), polygon)
        except (TypeError, ValueError):
            return "OUTSIDE"

    df["Status"] = df.apply(_row_status, axis=1)
    return df
```

Acrescentar ao final do arquivo (não substituir as funções da Task 1).
  </action>
  <verify>
    python -c "from geo_engine import load_perimeter, check_status, apply_geofencing; print('geo_engine completo OK')"
  </verify>
  <acceptance_criteria>
    - geo_engine.py contém as três funções: load_perimeter, check_status, apply_geofencing
    - Contém: `def apply_geofencing(df: pd.DataFrame, polygon: Polygon) -> pd.DataFrame:`
    - Contém: `df["Status"] = df.apply(`
    - Contém: tratamento de NaN (pd.isna ou equivalente) dentro de apply_geofencing
    - Contém: `return "OUTSIDE"` como fallback para coordenadas inválidas
    - Contém: `df = df.copy()` — não modifica o DataFrame original
    - Importação completa sem erro:
      python -c "from geo_engine import load_perimeter, check_status, apply_geofencing; print('OK')"
  </acceptance_criteria>
  <done>apply_geofencing() adicionada. Processa cada linha do DataFrame, trata NaN/inválidos como OUTSIDE, retorna DataFrame com coluna Status preenchida com 'INSIDE' ou 'OUTSIDE'.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| filesystem → Python | perimetro.kml lido do disco — pode estar malformado ou ausente |
| DataFrame → geofencing | Coordenadas vêm do pipeline de limpeza — podem ser NaN ou fora de range |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-02-01 | Tampering | load_perimeter — parsing KML | accept | App de uso interno; KML é arquivo fixo criado pelo operador |
| T-02-02 | Denial of Service | load_perimeter — arquivo ausente | mitigate | FileNotFoundError explícito com nome do arquivo; Phase 3 captura e exibe mensagem ao usuário |
| T-02-03 | Tampering | apply_geofencing — coordenadas inválidas | mitigate | try/except + pd.isna() → fallback para OUTSIDE; não interrompe o processamento |
</threat_model>

<verification>
1. python -c "from geo_engine import load_perimeter, check_status, apply_geofencing; print('Imports OK')"
2. Verificar que geo_engine.py contém `import fastkml` e `from shapely.geometry import Point, Polygon`
3. Verificar que check_status usa `Point(lon, lat)` — longitude primeiro (ordem Shapely x,y)
4. Verificar que apply_geofencing retorna DataFrame com coluna 'Status' contendo apenas 'INSIDE' ou 'OUTSIDE'
</verification>

<success_criteria>
- geo_engine.py existe com load_perimeter(), check_status() e apply_geofencing() exportadas
- load_perimeter() usa fastkml.KML().from_string(), extrai Shapely Polygon, levanta FileNotFoundError
- check_status() usa Point(lon, lat) — ordem correta para Shapely — e retorna 'INSIDE' ou 'OUTSIDE'
- apply_geofencing() adiciona coluna 'Status' ao DataFrame, trata NaN como 'OUTSIDE'
- Todos os paths são relativos a Path(__file__).parent
</success_criteria>

<output>
Após conclusão, criar `.planning/phases/01-pipeline-de-dados-e-cache/01-02-SUMMARY.md` com:
- Arquivos criados: geo_engine.py
- Funções exportadas: load_perimeter, check_status, apply_geofencing
- Decisão de traversal recursivo do KML documentada
- Nota sobre ordem (lon, lat) no Shapely Point
</output>
