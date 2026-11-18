"""Build one tidy district-level table from the raw files.

Output: data/processed/district.csv (25 rows, one per autonomous district)
Usage:  python src/prepare.py
"""
import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=UserWarning)   # openpyxl style warning
ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"

CRIMES = ["murder", "robbery", "sexual_assault", "theft", "violence"]


def load_names():
    """Korean district name -> English name, from the boundary file."""
    gj = json.load(open(ROOT / "data" / "geo" / "seoul_municipalities.json", encoding="utf-8"))
    return {f["properties"]["name"]: f["properties"]["name_eng"] for f in gj["features"]}


def load_crime():
    """Five major crimes, 2021: reported and cleared cases per district."""
    df = pd.read_excel(RAW / "Seoul_crime.xlsx", sheet_name="데이터", header=None)
    body = df.iloc[5:, 1:].reset_index(drop=True)          # rows 0-3 are headers, row 4 is the Seoul total
    cols = ["district", "total_reported", "total_cleared"]
    for c in CRIMES:
        cols += [f"{c}_reported", f"{c}_cleared"]
    body.columns = cols
    body[cols[1:]] = body[cols[1:]].apply(pd.to_numeric)
    return body


def load_cctv_years():
    """CCTV units installed per district and year (as of 31 Dec 2022)."""
    df = pd.read_csv(RAW / "CCTV_years.csv", thousands=",")
    df = df.rename(columns={"구분": "district", "총계": "cctv_total", "2013년 이전": "cctv_before_2013"})
    df = df[df["district"] != "계"].copy()
    df.columns = [c.replace("년", "") if c[:2] == "20" else c for c in df.columns]
    df = df.rename(columns={c: f"cctv_{c}" for c in df.columns if c.isdigit()})
    return df


def load_night():
    """Nightlife venues per district (list as of 31 Aug 2013)."""
    out = {}
    for sheet, key in [("자치구별 단란주점 현황", "karaoke_bars"), ("자치구별 유흥주점 현황", "hostess_bars")]:
        df = pd.read_excel(RAW / "Seoul_night.xlsx", sheet_name=sheet, header=None, skiprows=3)
        df = df[pd.to_numeric(df[0], errors="coerce").notna()]      # keep numbered venue rows
        # one row (no. 913, Suyu-dong) has an empty district cell; the list is ordered by district,
        # so the value of the row above (Gangbuk-gu) is carried down
        out[key] = df[2].ffill().str.strip().value_counts()
    night = pd.DataFrame(out).fillna(0).astype(int)
    night["nightlife_venues"] = night.sum(axis=1)
    return night.rename_axis("district").reset_index()


def load_area():
    """District area in km2, summed from the dong-level table."""
    df = pd.read_excel(RAW / "CCTV_pt.xlsx", usecols=["SIGUNGU_NM", "adm_ha"])
    return (df.groupby("SIGUNGU_NM")["adm_ha"].sum() / 100).rename("area_km2").rename_axis("district").reset_index()


def build():
    d = load_crime().merge(load_cctv_years(), on="district").merge(load_night(), on="district").merge(load_area(), on="district")
    assert len(d) == 25, len(d)
    d.insert(1, "district_en", d["district"].map(load_names()))
    d["clearance_rate"] = d["total_cleared"] / d["total_reported"]
    d["crime_per_km2"] = d["total_reported"] / d["area_km2"]
    d["cctv_per_km2"] = d["cctv_total"] / d["area_km2"]
    d["nightlife_per_km2"] = d["nightlife_venues"] / d["area_km2"]
    d["crime_per_cctv"] = d["total_reported"] / d["cctv_total"]
    return d


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    d = build()
    d.to_csv(OUT / "district.csv", index=False, encoding="utf-8-sig")
    print(f"wrote {OUT / 'district.csv'}: {d.shape}")
    print(d[["district_en", "total_reported", "cctv_total", "nightlife_venues", "area_km2"]].round(1).to_string(index=False))
