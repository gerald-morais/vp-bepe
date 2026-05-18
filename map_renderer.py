import folium
import pandas as pd
from shapely.geometry import Polygon


def render_map(df: pd.DataFrame, polygon: Polygon) -> folium.Map:
    """Constrói mapa Folium com perímetro, rota e marcadores coloridos.

    Recebe um DataFrame filtrado e o polígono do perímetro autorizado,
    retornando um objeto folium.Map configurado e pronto para uso com
    st_folium(). Não importa streamlit nem outros módulos do projeto.

    Args:
        df: DataFrame filtrado com 10 colunas
            (VP, CMT, Motorista, Data, Horário, Data_Hora, Endereco,
            Latitude, Longitude, Status). Se vazio, renderiza apenas
            o perímetro (estado inicial D-01/D-06).
        polygon: Shapely Polygon do perímetro de atuação, obtido de
            geo_engine.load_perimeter(). Coords em ordem (lon, lat).

    Returns:
        Objeto folium.Map configurado com polígono KML desenhado,
        PolyLine de rota (se df não-vazio), marcadores coloridos por
        Status e fit_bounds aplicado.
    """
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
        min_lat = min(min_lat, df["Latitude"].min())
        max_lat = max(max_lat, df["Latitude"].max())
        min_lon = min(min_lon, df["Longitude"].min())
        max_lon = max(max_lon, df["Longitude"].max())

    return [[min_lat, min_lon], [max_lat, max_lon]]


if __name__ == "__main__":
    print("map_renderer.py importado com sucesso.")
    print("Funções exportadas: render_map")
