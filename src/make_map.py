"""Interactive district map (Leaflet via folium) with one switchable layer per indicator.

Output: docs/index.html (served by GitHub Pages when Pages is set to the /docs folder)
Usage:  python src/make_map.py
"""
import json
from pathlib import Path

import folium
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LAYERS = [  # column, layer name, legend caption
    ("total_reported", "Crimes reported (2021)", "Five major crimes reported, 2021"),
    ("crime_per_km2", "Crimes per km²", "Five major crimes per km², 2021"),
    ("cctv_per_km2", "CCTV per km²", "CCTV units per km², end of 2022"),
    ("nightlife_per_km2", "Nightlife venues per km²", "Nightlife venues per km², 2013 list"),
    ("clearance_rate", "Clearance rate", "Cleared cases / reported cases, 2021"),
]
TOOLTIP = [("district_en", "District"), ("total_reported", "Crimes reported"), ("theft_reported", "Theft"),
           ("violence_reported", "Violence"), ("sexual_assault_reported", "Sexual assault"),
           ("robbery_reported", "Robbery"), ("murder_reported", "Murder"), ("clearance_pct", "Clearance rate"),
           ("cctv_total", "CCTV units"), ("nightlife_venues", "Nightlife venues"), ("area", "Area")]


def build():
    d = pd.read_csv(ROOT / "data" / "processed" / "district.csv")
    gj = json.load(open(ROOT / "data" / "geo" / "seoul_municipalities.json", encoding="utf-8"))
    rows = d.set_index("district")
    for f in gj["features"]:                       # copy indicators into the GeoJSON for tooltips
        r = rows.loc[f["properties"]["name"]]
        p = f["properties"]
        for col, _ in TOOLTIP[:-2] + [("cctv_total", ""), ("nightlife_venues", "")]:
            if col in r.index:
                p[col] = r[col] if isinstance(r[col], str) else f"{int(r[col]):,}"
        p["clearance_pct"] = f"{r['clearance_rate']:.0%}"
        p["area"] = f"{r['area_km2']:.1f} km²"

    m = folium.Map(location=[37.5642, 126.99], zoom_start=11, tiles="OpenStreetMap")
    for i, (col, name, caption) in enumerate(LAYERS):
        ch = folium.Choropleth(geo_data=gj, data=d, columns=["district", col], key_on="feature.properties.name",
                               fill_color="Blues", fill_opacity=0.8, line_color="white", line_weight=1.5,
                               legend_name=caption, name=name, overlay=False, show=(i == 0), highlight=True)
        folium.GeoJsonTooltip(fields=[c for c, _ in TOOLTIP], aliases=[a for _, a in TOOLTIP], sticky=True).add_to(ch.geojson)
        ch.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    # folium draws every layer's colour legend at once; show only the legend of the active layer
    names = json.dumps([name for _, name, _ in LAYERS])
    m.get_root().html.add_child(folium.Element(f"""
<script>
window.addEventListener("load", function () {{
  var names = {names};
  var map = {m.get_name()};
  function show(i) {{
    document.querySelectorAll(".legend.leaflet-control svg").forEach(function (s, k) {{
      s.style.display = k === i ? "block" : "none";
    }});
  }}
  show(0);
  map.on("baselayerchange", function (e) {{ show(names.indexOf(e.name)); }});
}});
</script>"""))
    return m


if __name__ == "__main__":
    out = ROOT / "docs" / "index.html"
    out.parent.mkdir(exist_ok=True)
    build().save(str(out))
    print("wrote", out, f"({out.stat().st_size / 1024:.0f} KB)")
