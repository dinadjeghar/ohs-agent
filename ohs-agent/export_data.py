"""Export one agent sweep (readings, history, worker checks, findings, thresholds) as JSON for dashboards."""
import json

from ohs_agent import tools
from ohs_agent.standards import OXYGEN, PPE_REQUIREMENTS, STANDARDS

LEVELS = tools.LEVELS


def build_snapshot(history_ticks: int = 12) -> dict:
    zones = tools.list_zones()["zones"]
    snap = {"zones": [], "workers": [], "thresholds": {}, "history": {}, "findings": []}

    for key, s in STANDARDS.items():
        snap["thresholds"][key] = {"name": s["name"], "unit": s["unit"], "warn": s["warn"],
                                   "danger": s["danger"], "critical": s["critical"],
                                   "source": s["source"], "action": s["action"]}
    snap["thresholds"]["o2_pct"] = {"name": OXYGEN["name"], "unit": "%",
                                    "low_danger": OXYGEN["low_danger"], "high_danger": OXYGEN["high_danger"],
                                    "low_critical": OXYGEN["low_critical"],
                                    "source": OXYGEN["source"], "action": OXYGEN["action"]}

    # Short simulated time series per zone for trend charts; the last tick is the current reading.
    for z in zones:
        snap["history"][z] = [tools.read_sensors(z)["readings"] for _ in range(history_ticks)]

    for z in zones:
        readings = snap["history"][z][-1]
        a = tools.assess_environment(z, readings)
        snap["zones"].append({"zone": z, "readings": readings, "overall": a["overall"]})
        for f in a["findings"]:
            g = snap["thresholds"][f["metric"]]
            snap["findings"].append({
                "level": f["level"], "location": z,
                "title": f"{f['name']} {f['value']} {f['unit']}",
                "basis": f["basis"], "action": g["action"],
            })

    raw = {w["id"]: w for w in tools.list_workers()["workers"]}
    for wid, w in raw.items():
        c = tools.check_worker(wid)
        c["ppe_required"] = sorted(PPE_REQUIREMENTS.get(w["task"], PPE_REQUIREMENTS["general"]))
        c["ppe_detected"] = sorted(w["ppe_detected"])
        snap["workers"].append(c)

        issues = []
        if c["ppe_missing"]:
            issues.append("missing PPE: " + ", ".join(c["ppe_missing"]))
        if c["fatigue_level"] != "normal":
            issues.append(f"fatigue {c['fatigue_level']} (PERCLOS {c['perclos']})")
        if c["overlong_shift"]:
            issues.append(f"shift length {c['shift_hours']} h")
        if issues:
            if c["ppe_missing"] and c["fatigue_level"] == "danger":
                level = "critical"
            elif c["ppe_missing"]:
                level = "danger"
            else:
                level = "warning"
            snap["findings"].append({
                "level": level, "location": c["zone"],
                "title": f"Worker {wid} ({c['task'].replace('_', ' ')}): " + "; ".join(issues),
                "basis": "Co-occurring PPE gap, fatigue and shift-length indicators. " + c["fatigue_basis"],
                "action": "Pull from the task until PPE is corrected, enforce rest and rotation, supervisor check-in.",
            })

    snap["findings"].sort(key=lambda f: -LEVELS.index(f["level"]))
    return snap


if __name__ == "__main__":
    print(json.dumps(build_snapshot(), indent=2))
