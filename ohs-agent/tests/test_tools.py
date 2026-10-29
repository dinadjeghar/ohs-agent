import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ohs_agent import tools
from ohs_agent.agent import run_offline


def test_assess_flags_h2s_and_low_oxygen():
    r = tools.assess_environment("Zone C", {"h2s_ppm": 24, "o2_pct": 19.2, "co_ppm": 5})
    metrics = {f["metric"]: f["level"] for f in r["findings"]}
    assert metrics["h2s_ppm"] == "danger"
    assert metrics["o2_pct"] == "danger"
    assert "co_ppm" not in metrics
    assert r["overall"] == "danger"


def test_normal_environment():
    r = tools.assess_environment("Z", {"co_ppm": 5, "o2_pct": 20.9, "noise_dba": 70})
    assert r["overall"] == "normal" and r["findings"] == []


def test_worker_ppe_and_fatigue():
    c = tools.check_worker("W-103")
    assert "gas_monitor" in c["ppe_missing"] and "harness" in c["ppe_missing"]
    assert c["fatigue_level"] == "danger" and c["overlong_shift"]


def test_unknown_inputs_return_errors():
    assert "error" in tools.read_sensors("Nowhere")
    assert "error" in tools.check_worker("W-999")
    assert "error" in tools.run_tool("nope", {})


def test_offline_briefing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_offline(verbose=False)
    assert "W-103" in out and "Hydrogen sulfide" in out
    assert (tmp_path / "incident_log.jsonl").exists()
