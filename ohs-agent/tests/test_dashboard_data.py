import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from build_html import build
from export_data import LEVELS, build_snapshot


def test_snapshot_shape_and_order():
    s = build_snapshot()
    assert len(s["zones"]) == 3 and len(s["workers"]) == 3
    levels = [LEVELS.index(f["level"]) for f in s["findings"]]
    assert levels == sorted(levels, reverse=True)  # most severe first
    assert s["findings"][0]["level"] == "critical"
    assert all(len(h) == 12 for h in s["history"].values())


def test_html_has_data_and_no_placeholder():
    html = build()
    assert "__DATA__" not in html and "OHS Safety Monitor" in html
