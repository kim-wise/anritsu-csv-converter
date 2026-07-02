"""
Folium 기반 채널 파워 지도 시각화 모듈
"""
import numpy as np
import pandas as pd
import folium
from folium.plugins import MousePosition, MiniMap
import branca.colormap as cm
from pathlib import Path


def generate_map(
    df: pd.DataFrame,
    output_path: Path,
    lat_col: str = "Latitude",
    lon_col: str = "Longitude",
    pwr_col: str = "Total_CH_power_dBm",
    ts_col: str | None = "DateTime",
):
    """
    DataFrame → HTML 지도 파일 생성

    Parameters
    ----------
    df : 최소 lat, lon, power 컬럼 포함
    output_path : 저장할 .html 경로
    """
    data = df[[lat_col, lon_col, pwr_col]].copy()
    if ts_col and ts_col in df.columns:
        data[ts_col] = df[ts_col]

    data.rename(columns={lat_col: "lat", lon_col: "lon", pwr_col: "pwr"}, inplace=True)

    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data["pwr"] = pd.to_numeric(data["pwr"], errors="coerce")

    clean = data.dropna(subset=["lat", "lon", "pwr"])
    clean = clean[(clean["lat"].between(-90, 90)) & (clean["lon"].between(-180, 180))]
    clean = clean.reset_index(drop=True)

    if clean.empty:
        print("⚠️ 유효한 GPS 데이터가 없습니다.")
        return

    center = [clean["lat"].mean(), clean["lon"].mean()]
    vmin, vmax = clean["pwr"].min(), clean["pwr"].max()

    m = folium.Map(location=center, zoom_start=15, control_scale=True, tiles=None)
    folium.TileLayer("CartoDB positron", name="CartoDB Positron").add_to(m)

    MiniMap(toggle_display=True, position="bottomleft").add_to(m)
    MousePosition(position="bottomright", separator=" | ", prefix="Lat/Lon", num_digits=6).add_to(m)

    # Color scale
    cmap = cm.LinearColormap(
        colors=["#0000ff", "#00ffff", "#00ff00", "#ffff00", "#ff7f00", "#ff0000"],
        vmin=vmin,
        vmax=vmax,
    )
    cmap.caption = "Total Channel Power (dBm)"
    cmap.add_to(m)

    # Layers
    fg_trace = folium.FeatureGroup(name="Trace (Polyline)", show=True)
    fg_points = folium.FeatureGroup(name="Power Points", show=True)

    coords = clean[["lat", "lon"]].values.tolist()
    if len(coords) >= 2:
        folium.PolyLine(coords, weight=2, opacity=0.6).add_to(fg_trace)

    has_ts = ts_col and ts_col in clean.columns
    for _, r in clean.iterrows():
        color = cmap(r["pwr"])
        popup_txt = f"Power: {r['pwr']:.2f} dBm"
        if has_ts and pd.notna(r.get(ts_col, np.nan)):
            popup_txt += f"<br>Time: {r[ts_col]}"
        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=3,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            opacity=0.85,
            popup=popup_txt,
        ).add_to(fg_points)

    fg_trace.add_to(m)
    fg_points.add_to(m)
    folium.LayerControl(position="topright", collapsed=False).add_to(m)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))
    print(f"✅ 지도 저장: {output_path.resolve()}")
