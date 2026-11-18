# seoul_crime_map

Data collection for a district-level map of crime and safety-related factors in Seoul.
The repository holds the source tables for 25 autonomous districts (자치구):
reported crime, CCTV installations, nightlife venues and rent levels.

Course final project (2023).

## Contents

All files are in `upload/`.

| File | Content | Unit | Period | Source |
|---|---|---|---|---|
| `Seoul_crime.xlsx` | Five major crimes (murder, robbery, rape and indecent assault, theft, violence): cases reported and cleared | 25 districts | 2021 | Seoul Metropolitan Government, Seoul Basic Statistics (table DT_201004_L030001) |
| `CCTV_Info.xlsx` | 46,398 CCTV records: managing agency, address, purpose, number of cameras, install date, WGS84 latitude and longitude | camera site | reference dates up to 2023 | Public CCTV standard data |
| `CCTV_pt.xlsx` | Camera counts joined to administrative dong boundaries (424 dong, with polygon geometry and area in ha) | dong | derived from `CCTV_Info.xlsx` | derived |
| `CCTV_years.csv` | CCTV installed per district by year (91,341 in total) | 25 districts | up to 2013, then 2013 to 2022 | Seoul Metropolitan Government, as of 31 Dec 2022 |
| `서울시 자치구 년도별 CCTV 설치 현황_221231기준.csv` | Raw version of the table above | 25 districts | same | same |
| `Seoul_night.xlsx` | Nightlife venues: 3,043 단란주점 and 2,329 유흥주점 with district, dong and address | venue | as of 31 Aug 2013 | Seoul Metropolitan Government |
| `Seoul_house.xlsx` | Officetel monthly rent: mean and median deposit and rent, by region and size | region (Seoul by 5 zones) | Feb to Jun 2020 | Korea Real Estate Board, Officetel Price Trend Survey (table DT_08002_06) |
| `index.html` | Placeholder for the map page (empty) | | | |

## Notes on the data

- Purpose of CCTV sites in `CCTV_Info.xlsx`: crime prevention (생활방범) 30,009, traffic enforcement 4,076, multi-purpose 3,923, child protection 3,356, other.
- The tables cover different years (nightlife 2013, rent 2020, crime 2021, CCTV 2022 to 2023), so comparisons across them are approximate.
- Rent data are at the level of five Seoul zones (도심권, 동북권, 서북권, 서남권, 동남권) and need a zone-to-district mapping before joining.
- Crime figures are counts. Per-capita rates need district population, which is not included.
- The geometry column in `CCTV_pt.xlsx` is stored as text and is truncated by Excel's cell limit for large polygons. Use the original boundary file for mapping.

## Usage

```python
import pandas as pd

crime = pd.read_excel("upload/Seoul_crime.xlsx", sheet_name="데이터", header=None)
cctv = pd.read_excel("upload/CCTV_Info.xlsx")
cctv_years = pd.read_csv("upload/CCTV_years.csv", thousands=",")
```

## Status

Data only. The analysis code and the rendered map are not in this repository.
