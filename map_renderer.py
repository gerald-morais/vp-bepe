import folium
import pandas as pd
import streamlit as st
from shapely.geometry import Polygon


def render_map(df: pd.DataFrame, polygon: Polygon, highlight_rows: pd.DataFrame = None) -> folium.Map:
    """Instancia o mapa base e orquestra a adição de camadas e marcadores.

    Args:
        df: DataFrame filtrado com dados de telemetria. Deve conter as colunas
            (VP, CMT, Motorista, Data, Horário, Data_Hora, Endereco,
            Latitude, Longitude, Status). Se vazio, renderiza apenas
            o perímetro (estado inicial D-01/D-06).
        polygon: Shapely Polygon do perímetro de atuação, obtido de
            geo_engine.load_perimeter(). Coords em ordem (lon, lat).
        highlight_rows: DataFrame contendo as linhas selecionadas para focar.

    Returns:
        Objeto folium.Map configurado com polígono KML desenhado,
        PolyLine de rota (se df não-vazio), marcadores coloridos por
        Status e fit_bounds aplicado.
    """
    m = folium.Map(tiles="OpenStreetMap")

    _add_perimeter(m, polygon)

    df_gps = df[df["Status"] != "VIATURA SEM GPS"].copy() if not df.empty else df

    if not df_gps.empty:
        _add_route(m, df_gps)
        _add_markers(m, df_gps)
        bounds = _compute_bounds(polygon, df_gps)
    else:
        bounds = _compute_bounds(polygon)

    if highlight_rows is not None and not highlight_rows.empty:
        hl_bounds = []
        for _, row in highlight_rows.iterrows():
            lat, lon = row["Latitude"], row["Longitude"]
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="black", icon="star"),
                tooltip=f"Ponto Selecionado: {row['Data_Hora']} ({row['Status']})"
            ).add_to(m)
            hl_bounds.append([lat, lon])
            
        if len(hl_bounds) == 1:
            lat, lon = hl_bounds[0]
            m.fit_bounds([[lat - 0.0015, lon - 0.0015], [lat + 0.0015, lon + 0.0015]])
        else:
            min_lat = min(b[0] for b in hl_bounds) - 0.0015
            min_lon = min(b[1] for b in hl_bounds) - 0.0015
            max_lat = max(b[0] for b in hl_bounds) + 0.0015
            max_lon = max(b[1] for b in hl_bounds) + 0.0015
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    else:
        m.fit_bounds(bounds)
        
    return m


def _add_perimeter(m: folium.Map, polygon: Polygon) -> None:
    """Desenha o polígono do perímetro autorizado no mapa.

    Converte as coordenadas do Shapely Polygon (lon, lat) para o formato
    esperado pelo Folium (lat, lon) e adiciona um folium.Polygon com
    estilo laranja semi-transparente.

    Args:
        m: Objeto folium.Map onde o polígono será adicionado.
        polygon: Shapely Polygon com coords em ordem (lon, lat).
    """
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
    """Desenha PolyLine conectando todos os pontos em ordem cronológica.

    Ordena o DataFrame por Data_Hora usando pd.to_datetime(dayfirst=True)
    para suportar formatos brasileiros (DD/MM/YYYY). Inclui guard para
    evitar PolyLine com menos de 2 pontos.

    Args:
        m: Objeto folium.Map onde a rota será adicionada.
        df: DataFrame não-vazio com colunas Latitude, Longitude e Data_Hora.
    """
    df_sorted = df.copy()
    df_sorted["_sort_key"] = pd.to_datetime(df_sorted["Data_Hora"], dayfirst=True)
    df_sorted = df_sorted.sort_values("_sort_key").drop(columns=["_sort_key"])

    coords = list(zip(df_sorted["Latitude"], df_sorted["Longitude"]))

    if len(coords) < 2:
        return

    folium.PolyLine(
        locations=coords,
        color="#2980b9",
        weight=3,
        opacity=0.7,
        tooltip="Rota da VP",
    ).add_to(m)


def _add_markers(m: folium.Map, df: pd.DataFrame) -> None:
    """Desenha CircleMarkers coloridos por Status em cada ponto do DataFrame.

    Pontos OUTSIDE recebem marcador vermelho maior (radius=6).
    Pontos INSIDE recebem marcador verde menor (radius=4).
    Cada marcador tem popup com Data_Hora e Endereço.

    Args:
        m: Objeto folium.Map onde os marcadores serão adicionados.
        df: DataFrame não-vazio com colunas Latitude, Longitude,
            Status, Data_Hora e Endereco.
    """
    for _, row in df.iterrows():
        if pd.isna(row["Latitude"]) or pd.isna(row["Longitude"]):
            continue
            
        status = row["Status"]
        if status == "OUTSIDE":
            color, fill_color, radius, opacity = "#c0392b", "#e74c3c", 6, 0.9
        elif status == "DESLOCAMENTO":
            color, fill_color, radius, opacity = "#e67e22", "#f39c12", 4, 0.85
        else:  # INSIDE
            color, fill_color, radius, opacity = "#27ae60", "#2ecc71", 4, 0.6

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=fill_color,
            fill_opacity=opacity,
            popup=folium.Popup(
                f"<b>{row['Data_Hora']}</b><br>{row['Endereco']}",
                max_width=250,
            ),
            tooltip=status,
        ).add_to(m)


def _compute_bounds(
    polygon: Polygon, df: pd.DataFrame | None = None
) -> list[list[float]]:
    """Calcula os limites geográficos para fit_bounds().

    Com df=None, retorna bounds cobrindo apenas o polígono do perímetro.
    Com df fornecido, expande os bounds para incluir todos os pontos da rota.

    Args:
        polygon: Shapely Polygon com coords em ordem (lon, lat).
        df: DataFrame opcional com colunas Latitude e Longitude.
            Se None ou vazio, apenas o polígono é considerado.

    Returns:
        Lista [[min_lat, min_lon], [max_lat, max_lon]] para folium.Map.fit_bounds().
    """
    poly_lons = [c[0] for c in polygon.exterior.coords]
    poly_lats = [c[1] for c in polygon.exterior.coords]

    min_lat, max_lat = min(poly_lats), max(poly_lats)
    min_lon, max_lon = min(poly_lons), max(poly_lons)

    if df is not None and not df.empty:
        valid_df = df.dropna(subset=["Latitude", "Longitude"])
        if not valid_df.empty:
            min_lat = min(min_lat, valid_df["Latitude"].min())
            max_lat = max(max_lat, valid_df["Latitude"].max())
            min_lon = min(min_lon, valid_df["Longitude"].min())
            max_lon = max(max_lon, valid_df["Longitude"].max())

    return [[min_lat, min_lon], [max_lat, max_lon]]


def render_heatmap(df: pd.DataFrame, polygon: Polygon, only_outside: bool = False, highlight_rows: pd.DataFrame = None) -> folium.Map:
    """Instancia o mapa com um HeatMap dos pontos em vez de rotas e marcadores.

    Args:
        df: DataFrame filtrado com dados de telemetria.
        polygon: Shapely Polygon do perímetro autorizado.
        only_outside: Se True, usa apenas pontos OUTSIDE no heatmap.
        highlight_rows: DataFrame contendo as linhas selecionadas para focar.

    Returns:
        Objeto folium.Map com polígono e camada HeatMap.
    """
    from folium.plugins import HeatMap

    m = folium.Map(tiles="OpenStreetMap")
    _add_perimeter(m, polygon)

    df_gps = df[df["Status"] != "VIATURA SEM GPS"].copy() if not df.empty else df

    if not df_gps.empty:
        source = df_gps[df_gps["Status"] == "OUTSIDE"] if only_outside else df_gps
        heat_data = (
            source[["Latitude", "Longitude"]]
            .dropna()
            .values
            .tolist()
        )
        if heat_data:
            HeatMap(heat_data, radius=15, blur=12, max_zoom=14).add_to(m)
        bounds = _compute_bounds(polygon, df_gps)
    else:
        bounds = _compute_bounds(polygon)

    if highlight_rows is not None and not highlight_rows.empty:
        hl_bounds = []
        for _, row in highlight_rows.iterrows():
            lat, lon = row["Latitude"], row["Longitude"]
            folium.Marker(
                [lat, lon],
                icon=folium.Icon(color="black", icon="star"),
                tooltip=f"Ponto Selecionado: {row['Data_Hora']} ({row['Status']})"
            ).add_to(m)
            hl_bounds.append([lat, lon])
            
        if len(hl_bounds) == 1:
            lat, lon = hl_bounds[0]
            m.fit_bounds([[lat - 0.0015, lon - 0.0015], [lat + 0.0015, lon + 0.0015]])
        else:
            min_lat = min(b[0] for b in hl_bounds) - 0.0015
            min_lon = min(b[1] for b in hl_bounds) - 0.0015
            max_lat = max(b[0] for b in hl_bounds) + 0.0015
            max_lon = max(b[1] for b in hl_bounds) + 0.0015
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]])
    else:
        m.fit_bounds(bounds)

    return m


if __name__ == "__main__":
    print("map_renderer.py importado com sucesso.")
    print("Funções exportadas: render_map, render_heatmap")

