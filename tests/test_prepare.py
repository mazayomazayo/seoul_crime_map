import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import prepare  # noqa: E402

D = prepare.build()


def test_25_districts_with_english_names():
    assert len(D) == 25 and D["district_en"].notna().all() and D["district"].is_unique


def test_crime_totals_match_source_table():
    assert D["total_reported"].sum() == 80445 and D["total_cleared"].sum() == 58012     # Seoul row of the source
    parts = D[[f"{c}_reported" for c in prepare.CRIMES]].sum(axis=1)
    assert (parts == D["total_reported"]).all()


def test_cctv_total_matches_source_table():
    assert D["cctv_total"].sum() == 91341
    years = [c for c in D.columns if c.startswith("cctv_2") or c == "cctv_before_2013"]
    assert (D[years].sum(axis=1) == D["cctv_total"]).all()


def test_nightlife_counts_match_sheet_titles():
    assert D["karaoke_bars"].sum() == 3043 and D["hostess_bars"].sum() == 2329


def test_area_is_plausible():
    assert D["area_km2"].sum() == pytest.approx(605, abs=5)      # Seoul is about 605 km2
