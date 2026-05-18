import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
from shapely.geometry import Point, Polygon

BASE_DIR = Path(__file__).parent

_KML_NS = "http://www.opengis.net/kml/2.2"


def load_perimeter() -> Polygon:
    """Carrega o polígono único de perimetro.kml.

    Usa xml.etree.ElementTree para parsing do KML e extrai as coordenadas
    do primeiro elemento <coordinates> encontrado, convertendo para
    shapely.geometry.Polygon.

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

    tree = ET.parse(kml_path)
    root = tree.getroot()

    coords_elem = root.find(f".//{{{_KML_NS}}}coordinates")
    if coords_elem is None:
        coords_elem = root.find(".//coordinates")

    if coords_elem is None or not coords_elem.text:
        raise ValueError(
            "Nenhum polígono encontrado em perimetro.kml. "
            "Verifique se o arquivo contém um Placemark com geometria Polygon."
        )

    coords = []
    for triplet in coords_elem.text.strip().split():
        parts = triplet.split(",")
        lon, lat = float(parts[0]), float(parts[1])
        coords.append((lon, lat))

    if len(coords) < 3:
        raise ValueError(
            "Polígono em perimetro.kml tem menos de 3 pontos — arquivo inválido."
        )

    return Polygon(coords)


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
    point = Point(lon, lat)
    return "INSIDE" if polygon.contains(point) else "OUTSIDE"


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
        try:
            if pd.isna(lat) or pd.isna(lon):
                return "OUTSIDE"
            return check_status(float(lat), float(lon), polygon)
        except (TypeError, ValueError):
            return "OUTSIDE"

    df["Status"] = df.apply(_row_status, axis=1)
    return df
