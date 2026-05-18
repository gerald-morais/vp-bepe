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


def filter_by_shift_window(df: pd.DataFrame, horario_str: str) -> pd.DataFrame:
    """Remove linhas (pontos de GPS) que estão fora do horário do turno.
    
    Args:
        df: DataFrame com coluna 'Data_Hora' (str DD/MM/YYYY HH:MM:SS)
        horario_str: String do turno no formato 'HH:MM - HH:MM'
        
    Returns:
        DataFrame contendo apenas os pontos dentro do horário do turno.
    """
    import re
    import datetime

    try:
        horario_norm = str(horario_str).replace("h", ":").replace("H", ":")
        matches = re.findall(r"(\d{1,2}:\d{2})", horario_norm)
        if len(matches) < 2:
            return df
            
        inicio = datetime.datetime.strptime(matches[0].strip(), "%H:%M").time()
        fim = datetime.datetime.strptime(matches[-1].strip(), "%H:%M").time()
    except (ValueError, AttributeError):
        return df

    gps_times = pd.to_datetime(
        df["Data_Hora"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    ).dt.time

    inicio_min = inicio.hour * 60 + inicio.minute
    fim_min = fim.hour * 60 + fim.minute

    def _in_shift(gps_time):
        if pd.isna(gps_time):
            return True  # Mantém se não conseguir parsear
            
        t_min = gps_time.hour * 60 + gps_time.minute
        if inicio_min <= fim_min:
            return inicio_min <= t_min <= fim_min
        else:
            # Turno vira a noite (ex: 23:00 as 07:00)
            return t_min >= inicio_min or t_min <= fim_min

    mask = gps_times.apply(_in_shift)
    return df[mask].reset_index(drop=True)


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


def apply_displacement_window(df: pd.DataFrame, horario_str: str) -> pd.DataFrame:
    """Reclassifica OUTSIDE → DESLOCAMENTO nos períodos de deslocamento do turno.

    Os primeiros 60 minutos após o início do turno (batalhão → perímetro) e
    os últimos 60 minutos antes do fim (perímetro → batalhão) são considerados
    deslocamento operacional legítimo e não contam como infração.

    Trata corretamente horários que cruzam a meia-noite (ex: 15:00 - 01:30).

    Args:
        df: DataFrame com colunas 'Data_Hora' (str DD/MM/YYYY HH:MM:SS)
            e 'Status' (INSIDE | OUTSIDE).
        horario_str: String do turno no formato 'HH:MM - HH:MM', ex: '07:00 - 16:30'.

    Returns:
        Cópia do DataFrame com OUTSIDE → DESLOCAMENTO nas janelas de deslocamento.
        Linhas INSIDE nunca são alteradas.
    """
    import datetime

    import re
    # Extrai horários no formato HH:MM usando regex
    try:
        horario_norm = str(horario_str).replace("h", ":").replace("H", ":")
        matches = re.findall(r"(\d{1,2}:\d{2})", horario_norm)
        if len(matches) < 2:
            return df
            
        inicio = datetime.datetime.strptime(matches[0].strip(), "%H:%M").time()
        fim = datetime.datetime.strptime(matches[-1].strip(), "%H:%M").time()
    except (ValueError, AttributeError):
        return df

    inicio_min = inicio.hour * 60 + inicio.minute
    fim_min = fim.hour * 60 + fim.minute

    gps_times = pd.to_datetime(
        df["Data_Hora"], format="%d/%m/%Y %H:%M:%S", errors="coerce"
    ).dt.time

    df = df.copy()

    def _reclassificar(status: str, gps_time) -> str:
        if status != "OUTSIDE":
            return status
        if gps_time is None or not hasattr(gps_time, "hour"):
            return status
            
        t_min = gps_time.hour * 60 + gps_time.minute
        
        # Aritmética modular (1440 min = 24h) resolve a virada da meia-noite.
        # Diferença positiva de 'inicio' até 't_min':
        diff_from_inicio = (t_min - inicio_min) % 1440
        if diff_from_inicio <= 60:
            return "DESLOCAMENTO"
            
        # Diferença positiva de 't_min' até 'fim':
        diff_to_fim = (fim_min - t_min) % 1440
        if diff_to_fim <= 60:
            return "DESLOCAMENTO"
            
        return status

    df["Status"] = [
        _reclassificar(s, t) for s, t in zip(df["Status"], gps_times)
    ]
    return df

