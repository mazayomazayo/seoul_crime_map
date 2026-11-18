"""Correlations and static figures from data/processed/district.csv.

Outputs: results/correlations.csv, figures/*.png
Usage:   python src/analyze.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FIG, RES = ROOT / "figures", ROOT / "results"
INK, MUTED, GRID, BLUE = "#1f2933", "#6b7280", "#e5e7eb", "#2563a8"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight"})

PAIRS = [("cctv_total", "total_reported"), ("nightlife_venues", "total_reported"),
         ("cctv_per_km2", "crime_per_km2"), ("nightlife_per_km2", "crime_per_km2"),
         ("nightlife_venues", "violence_reported"), ("nightlife_venues", "theft_reported"),
         ("nightlife_venues", "sexual_assault_reported"), ("cctv_total", "clearance_rate"),
         ("cctv_total", "nightlife_venues")]
LABELS = {"total_reported": "Five major crimes reported, 2021", "crime_per_km2": "Crimes per km²",
          "cctv_total": "CCTV units, end of 2022", "cctv_per_km2": "CCTV units per km²",
          "nightlife_venues": "Nightlife venues, 2013 list", "nightlife_per_km2": "Nightlife venues per km²",
          "clearance_rate": "Clearance rate"}


def correlations(d):
    rows = []
    for x, y in PAIRS:
        r, p = stats.pearsonr(d[x], d[y]); rho, p_s = stats.spearmanr(d[x], d[y])
        rows.append({"x": x, "y": y, "n": len(d), "pearson_r": r, "pearson_p": p, "spearman_rho": rho, "spearman_p": p_s})
    return pd.DataFrame(rows)


def partial_corr(d, x, y, z):
    """Pearson correlation of x and y after removing the linear effect of z from both."""
    rx = d[x] - np.polyval(np.polyfit(d[z], d[x], 1), d[z])
    ry = d[y] - np.polyval(np.polyfit(d[z], d[y], 1), d[z])
    return stats.pearsonr(rx, ry)


def _polys(geom):
    parts = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [np.array(p[0]) for p in parts]


def fig_maps(d, gj):
    panels = ["total_reported", "crime_per_km2", "cctv_per_km2", "nightlife_per_km2"]
    val = d.set_index("district")
    fig, axes = plt.subplots(2, 2, figsize=(11, 9))
    for ax, col in zip(axes.ravel(), panels):
        patches, vals = [], []
        for f in gj["features"]:
            for xy in _polys(f["geometry"]):
                patches.append(Polygon(xy, closed=True)); vals.append(val.loc[f["properties"]["name"], col])
        pc = PatchCollection(patches, cmap="Blues", edgecolor="white", linewidth=1.2)
        pc.set_array(np.array(vals)); ax.add_collection(pc)
        top = val[col].nlargest(3).index
        lo, hi = val[col].min(), val[col].max()
        for f in gj["features"]:
            name = f["properties"]["name"]
            if name in top:
                xy = max(_polys(f["geometry"]), key=len); cx, cy = (xy.min(axis=0) + xy.max(axis=0)) / 2
                dark_fill = (val.loc[name, col] - lo) / (hi - lo) > 0.55
                ax.text(cx, cy, f["properties"]["name_eng"].replace("-gu", ""), ha="center", va="center", fontsize=8,
                        color="white" if dark_fill else INK, fontweight="bold")
        ax.autoscale_view(); ax.set_aspect(1 / np.cos(np.radians(37.55))); ax.axis("off")
        ax.set_title(LABELS[col], loc="left", fontsize=11, fontweight="bold")
        cb = fig.colorbar(pc, ax=ax, fraction=0.035, pad=0.01); cb.outline.set_visible(False); cb.ax.tick_params(labelsize=8)
    fig.suptitle("Seoul by district: crime, CCTV and nightlife (top three districts labelled)", x=0.02, ha="left", fontsize=13)
    fig.savefig(FIG / "maps.png"); plt.close(fig)


def fig_scatter(d):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), sharey=True)
    for ax, x in zip(axes, ["cctv_total", "nightlife_venues"]):
        y = "total_reported"
        ax.scatter(d[x], d[y], s=42, color=BLUE, edgecolor="white", linewidth=1.2, zorder=3)
        b, a = np.polyfit(d[x], d[y], 1); xs = np.linspace(d[x].min(), d[x].max(), 50)
        ax.plot(xs, a + b * xs, color=MUTED, linewidth=1.2, linestyle="--", zorder=2)
        resid = (d[y] - (a + b * d[x])).abs()
        for i in set(resid.nlargest(3).index) | set(d[y].nlargest(3).index) | set(d[x].nlargest(2).index):
            ax.annotate(d.loc[i, "district_en"].replace("-gu", ""), (d.loc[i, x], d.loc[i, y]), xytext=(6, 5),
                        textcoords="offset points", fontsize=8, color=INK)
        r, p = stats.pearsonr(d[x], d[y])
        ax.set_title(f"r = {r:.2f} (n = 25)", loc="left", fontsize=10, color=MUTED)
        ax.set_xlabel(LABELS[x]); ax.grid(color=GRID, linewidth=0.8); ax.set_axisbelow(True)
    axes[0].set_ylabel(LABELS["total_reported"])
    fig.suptitle("Reported crime against CCTV units and nightlife venues, by district", x=0.02, ha="left", fontsize=13)
    fig.savefig(FIG / "scatter.png"); plt.close(fig)


def fig_ranked(d):
    s = d.sort_values("total_reported")
    names = s["district_en"].str.replace("-gu", "")
    fig, axes = plt.subplots(1, 2, figsize=(11, 7), sharey=True, gridspec_kw={"width_ratios": [3, 2]})
    axes[0].barh(names, s["total_reported"], color=BLUE, height=0.62)
    for v, n in zip(s["total_reported"], names):
        axes[0].text(v + 60, n, f"{v:,}", va="center", fontsize=8, color=MUTED)
    axes[0].set_xlabel(LABELS["total_reported"]); axes[0].set_xlim(0, s["total_reported"].max() * 1.1)
    axes[1].hlines(names, s["clearance_rate"].min() - 0.02, s["clearance_rate"], color=GRID, linewidth=1.5)
    axes[1].scatter(s["clearance_rate"], names, s=40, color=BLUE, edgecolor="white", linewidth=1.2, zorder=3)
    axes[1].axvline(d["total_cleared"].sum() / d["total_reported"].sum(), color=MUTED, linewidth=1, linestyle="--")
    axes[1].text(d["total_cleared"].sum() / d["total_reported"].sum(), len(s) - 0.3, " Seoul average", fontsize=8, color=MUTED)
    axes[1].set_xlabel("Cleared cases / reported cases"); axes[1].xaxis.set_major_formatter(lambda v, _: f"{v:.0%}")
    for ax in axes:
        ax.grid(axis="x", color=GRID, linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
    fig.suptitle("Five major crimes by district, 2021: volume and clearance", x=0.02, ha="left", fontsize=13)
    fig.savefig(FIG / "ranked.png"); plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(exist_ok=True); RES.mkdir(exist_ok=True)
    d = pd.read_csv(ROOT / "data" / "processed" / "district.csv")
    gj = json.load(open(ROOT / "data" / "geo" / "seoul_municipalities.json", encoding="utf-8"))
    c = correlations(d); c.round(4).to_csv(RES / "correlations.csv", index=False)
    print(c.round(3).to_string(index=False))
    r, p = partial_corr(d, "cctv_total", "total_reported", "nightlife_venues")
    print(f"\npartial r(CCTV, crime | nightlife) = {r:.3f}, p = {p:.3f}")
    r, p = partial_corr(d, "nightlife_venues", "total_reported", "cctv_total")
    print(f"partial r(nightlife, crime | CCTV) = {r:.3f}, p = {p:.3f}")
    fig_maps(d, gj); fig_scatter(d); fig_ranked(d)
    print("figures written to", FIG)
