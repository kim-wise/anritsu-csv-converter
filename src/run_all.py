"""
전체 파이프라인 실행 스크립트
사용법: python -m src.run_all --data data/251105_UHD --name 251105
"""
import argparse
from pathlib import Path

from src.convert import batch_convert
from src.visualize_map import generate_map
from src.stats import compute_stats_and_plots


def main():
    parser = argparse.ArgumentParser(description="UHD 채널 파워 분석 파이프라인")
    parser.add_argument("--data", type=str, required=True, help="CSV 데이터 폴더 경로 (예: data/251105_UHD)")
    parser.add_argument("--name", type=str, default=None, help="출력 파일 접두사 (예: 251105)")
    parser.add_argument("--output", type=str, default="output", help="출력 루트 폴더 (기본: output)")
    args = parser.parse_args()

    data_dir = Path(args.data)
    output_dir = Path(args.output)
    name = args.name or data_dir.name

    if not data_dir.exists():
        print(f"❌ 데이터 폴더가 없습니다: {data_dir}")
        return

    print(f"\n{'='*50}")
    print(f"  UHD 채널 파워 분석 파이프라인")
    print(f"  데이터: {data_dir}")
    print(f"  출력:   {output_dir}")
    print(f"{'='*50}\n")

    # Step 1: CSV → Excel 변환
    print("[1/3] CSV 파싱 및 변환...")
    combined_df = batch_convert(
        data_dir=data_dir,
        output_dir=output_dir,
        combined_name=f"{name}_all_combined.xlsx",
    )

    # Step 2: 지도 생성
    print("\n[2/3] 지도 시각화...")
    map_path = output_dir / "maps" / f"{name}_power_map.html"
    generate_map(combined_df, output_path=map_path)

    # Step 3: 통계 및 플롯
    print("\n[3/3] 통계 분석 및 플롯...")
    try:
        compute_stats_and_plots(combined_df, output_dir=output_dir / "plots")
    except ValueError as e:
        print(f"⚠️ 통계 스킵: {e}")

    print(f"\n{'='*50}")
    print(f"  ✅ 완료!")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
