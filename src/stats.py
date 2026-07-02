"""
통계 분석 및 PDF/CDF 플롯 모듈
"""
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# Route 매핑 규칙
ROUTE_MAP = {
    r".*415[-_]?1.*": "415-1",
    r".*345[-_]?5.*": "345-5",
    r".*park.*": "345-5",
    r".*namsan.*": "Namsan",
}
DEFAULT_TARGETS = ["415-1", "345-5", "Namsan"]


def infer_route(source_file: str) -> str | None:
    """파일명에서 라우트 추론"""
    name = str(source_file).lower()
    for pat, lab in ROUTE_MAP.items():
        if re.match(pat, name):
            return lab
    return None


def kde_pdf(v: np.ndarray, x: np.ndarray, h_scale: float = 1.3) -> np.ndarray:
    """가우시안 KDE (Silverman bandwidth)"""
    v = np.asarray(v, dtype=float)
    n = len(v)
    if n < 2:
        h = 1.0
    else:
        std = np.std(v, ddof=1)
        h = (1.06 * std * n ** (-1 / 5)) if std > 0 else 1.0
    h *= h_scale
    z = (x[:, None] - v[None, :]) / (h + 1e-12)
    pdf = np.exp(-0.5 * z**2).sum(axis=1) / (n * (h + 1e-12) * np.sqrt(2 * np.pi))
    return pdf


def compute_stats_and_plots(
    df: pd.DataFrame,
    output_dir: Path,
    power_col: str = "Total_CH_power_dBm",
    targets: list[str] | None = None,
    h_scale: float = 1.3,
):
    """
    라우트별 통계 + PDF/CDF 플롯 생성

    Parameters
    ----------
    df : source_file 컬럼 포함된 통합 DataFrame
    output_dir : 출력 폴더 (예: output/plots)
    """
    if targets is None:
        targets = DEFAULT_TARGETS

    output_dir.mkdir(parents=True, exist_ok=True)

    # Route 추론
    if "route_norm" not in df.columns:
        if "source_file" not in df.columns:
            raise ValueError("route 판별을 위한 source_file 컬럼이 없습니다.")
        df = df.copy()
        df["route_norm"] = df["source_file"].apply(infer_route)

    df = df[df["route_norm"].isin(targets)].copy()
    df["uhd_dBm"] = pd.to_numeric(df[power_col], errors="coerce")
    df = df.dropna(subset=["uhd_dBm"])

    if df.empty:
        print("⚠️ 유효한 데이터가 없습니다.")
        return None

    # 통계
    stats = df.groupby("route_norm")["uhd_dBm"].agg(
        mean="mean", std="std", var="var", count="count", min="min", max="max"
    ).reindex(targets)
    print("\nUHD 파워 통계(dBm):\n", stats.round(3))

    stats_path = output_dir / "uhd_stats.csv"
    stats.round(6).to_csv(stats_path, encoding="utf-8-sig")
    print(f"✅ 통계 저장: {stats_path.resolve()}")

    # 공통 x-그리드
    vals_all = df["uhd_dBm"].values
    xmin = np.percentile(vals_all, 0.5)
    xmax = np.percentile(vals_all, 99.5)
    x = np.linspace(xmin, xmax, 1000)

    # PDF
    plt.figure(figsize=(8, 5))
    for r in targets:
        v = df.loc[df["route_norm"] == r, "uhd_dBm"].values
        if len(v) == 0:
            continue
        pdf = kde_pdf(v, x, h_scale=h_scale)
        plt.plot(x, pdf, label=r, linewidth=1.5)
    plt.xlabel("UHD Power (dBm)")
    plt.ylabel("PDF")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    pdf_img = output_dir / "uhd_pdf.png"
    plt.savefig(pdf_img, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ PDF 플롯: {pdf_img.resolve()}")

    # CDF
    plt.figure(figsize=(8, 5))
    dx = x[1] - x[0]
    for r in targets:
        v = df.loc[df["route_norm"] == r, "uhd_dBm"].dropna().values
        if len(v) == 0:
            continue
        pdf = kde_pdf(v, x, h_scale=h_scale)
        cdf = np.cumsum(pdf) * dx
        cdf = np.clip(cdf, 0, 1)
        plt.plot(x, cdf, label=r, linewidth=1.5)
    plt.xlabel("UHD Power (dBm)")
    plt.ylabel("CDF")
    plt.legend(ncol=2)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    cdf_img = output_dir / "uhd_cdf.png"
    plt.savefig(cdf_img, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"✅ CDF 플롯: {cdf_img.resolve()}")

    return stats
