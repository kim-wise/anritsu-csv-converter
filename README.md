# UHD 채널 파워 분석 도구

Anritsu 계측기에서 수집한 UHD 대역 CSV 데이터를 파싱하여 총 채널 파워(dBm)를 계산하고,
지도 시각화 및 통계 분석을 수행합니다.

## 프로젝트 구조

```
anritsu_uhd/
├── data/                   # 원본 측정 데이터
│   ├── 251103_UHD/
│   ├── 251105_UHD/
│   └── Way_UHD/
├── output/                 # 산출물 (git 제외)
│   ├── edit/               # 개별 변환 xlsx
│   ├── results/            # 통합 xlsx
│   ├── plots/              # 통계 그래프 (PDF/CDF)
│   └── maps/               # HTML 지도
├── src/                    # 핵심 모듈
│   ├── convert.py          # CSV 파싱 + 채널파워 계산
│   ├── visualize_map.py    # Folium 지도 생성
│   ├── stats.py            # 통계 + KDE 플롯
│   └── run_all.py          # CLI 파이프라인
├── web/                    # 브라우저 기반 변환기
│   └── index.html
├── csv_edit.ipynb          # 대화형 노트북
└── README.md
```

## 사용법

### CLI (일괄 처리)

```bash
python -m src.run_all --data data/251105_UHD --name 251105
```

### 노트북

`csv_edit.ipynb`를 열어 셀 단위로 실행합니다.

### 웹 변환기

`web/index.html`을 브라우저로 열면 서버 없이 CSV 변환 + 지도 시각화가 가능합니다.

## 의존성

```
pandas
openpyxl
folium
matplotlib
numpy
```
