"""Build the standalone HTML dashboard (no server, no tunnel).

    python build_html.py          # writes docs/ohs-dashboard.html, open it in any browser

In Google Colab or Jupyter you can show it inline instead:

    from IPython.display import HTML, display
    from build_html import build
    display(HTML(build()))
"""
import json
from pathlib import Path

from export_data import build_snapshot

ROOT = Path(__file__).parent


def build() -> str:
    template = (ROOT / "dashboard_template.html").read_text()
    return template.replace("__DATA__", json.dumps(build_snapshot(), separators=(",", ":")))


if __name__ == "__main__":
    out = ROOT / "docs" / "ohs-dashboard.html"
    out.parent.mkdir(exist_ok=True)
    head = ('<!doctype html><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"><style>body{margin:0}</style>')
    out.write_text(head + build())
    print(f"Wrote {out}")
