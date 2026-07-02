"""
CSV 파싱 및 채널 파워 계산 모듈
- Anritsu 계측 CSV → 총 채널 파워(dBm) 요약 DataFrame
"""
import math
from pathlib import Path
import pandas as pd


def compute_total_ch_dbm(dbm_values: list[float]) -> float:
    """dBm 리스트 → mW 합산 → dBm 변환"""
    if dbm_values is None or len(dbm_values) == 0:
        return float("nan")

    lin = [10 ** (v / 10.0) for v in dbm_values if pd.notna(v)]
    if not lin:
        return float("nan")

    s = sum(lin)
    if s <= 0:
        return float("nan")

    return 10.0 * math.log10(s)


def parse_csv(csv_path: Path) -> pd.DataFrame:
    """
    CSV 1개 → 요약 DataFrame
    Columns: DateTime, Longitude, Latitude, Total_CH_power_dBm
    """
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.rstrip("\n") for ln in f]

    # 'Ref Level' 행 이후 데이터 시작
    ref_idx = None
    for i, ln in enumerate(lines):
        first = ln.split(",", 1)[0].strip().lower()
        if first in ("ref level", "reflevel", "ref level(dbm)", "reflevel(dbm)"):
            ref_idx = i
            break

    start = (ref_idx + 1) if ref_idx is not None else 19
    while start < len(lines) and not lines[start].strip():
        start += 1

    if len(lines) <= start:
        return pd.DataFrame(columns=["DateTime", "Longitude", "Latitude", "Total_CH_power_dBm"])

    lines = lines[start:]
    rows = [ln.strip() for ln in lines if ln.strip()]
    tokens = [r.split(",") for r in rows]
    if not tokens:
        return pd.DataFrame(columns=["DateTime", "Longitude", "Latitude", "Total_CH_power_dBm"])

    lengths = [len(t) for t in tokens]
    ncols_mode = max(set(lengths), key=lengths.count)
    wide_rows = [t for t in tokens if len(t) == ncols_mode]
    if len(wide_rows) < 3:
        return pd.DataFrame(columns=["DateTime", "Longitude", "Latitude", "Total_CH_power_dBm"])

    out = []
    for wr in wide_rows[2:]:
        try:
            _ = int(wr[0])
        except (ValueError, IndexError):
            continue

        dt = wr[1] if len(wr) > 1 else ""
        try:
            lon = float(wr[2]) if wr[2] else float("nan")
        except (ValueError, IndexError):
            lon = float("nan")
        try:
            lat = float(wr[3]) if wr[3] else float("nan")
        except (ValueError, IndexError):
            lat = float("nan")

        vals_tokens = wr[5:-1] if len(wr) > 6 else []
        vals = []
        for x in vals_tokens:
            try:
                vals.append(float(x))
            except ValueError:
                vals.append(float("nan"))

        total_dbm = compute_total_ch_dbm(vals) if vals else float("nan")
        out.append({
            "DateTime": dt,
            "Longitude": lon,
            "Latitude": lat,
            "Total_CH_power_dBm": total_dbm,
        })

    return pd.DataFrame(out)


def batch_convert(data_dir: Path, output_dir: Path, combined_name: str = "all_combined.xlsx"):
    """
    폴더 내 모든 CSV → 개별 xlsx + 통합 xlsx 생성

    Parameters
    ----------
    data_dir : 원본 CSV가 있는 폴더 (예: data/251105_UHD)
    output_dir : 출력 폴더 루트 (예: output/)
    combined_name : 통합 파일명
    """
    edit_dir = output_dir / "edit" / data_dir.name
    edit_dir.mkdir(parents=True, exist_ok=True)

    all_list = []
    for csv_file in sorted(data_dir.glob("*.csv")):
        df_sum = parse_csv(csv_file)

        out_xlsx = edit_dir / f"{csv_file.stem}_edit.xlsx"
        with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xlw:
            df_sum.to_excel(xlw, sheet_name="summary", index=False)

        if not df_sum.empty:
            df_tmp = df_sum.copy()
            df_tmp["source_file"] = csv_file.name
            all_list.append(df_tmp)

    if all_list:
        combined_df = pd.concat(all_list, ignore_index=True)
    else:
        combined_df = pd.DataFrame(
            columns=["DateTime", "Longitude", "Latitude", "Total_CH_power_dBm", "source_file"]
        )

    results_dir = output_dir / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    combined_path = results_dir / combined_name
    with pd.ExcelWriter(combined_path, engine="openpyxl") as xlw:
        combined_df.to_excel(xlw, sheet_name="summary_all", index=False)

    print(f"✅ 개별 파일 저장: {edit_dir.resolve()}")
    print(f"✅ 통합 파일 생성: {combined_path.resolve()}")
    return combined_df
