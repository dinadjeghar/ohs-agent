"""Tools the OHS agent can call. Each returns JSON-serializable data."""
import json
import time
from pathlib import Path

from .simulator import Plant
from .standards import FATIGUE_GUIDANCE, OXYGEN, PPE_REQUIREMENTS, STANDARDS

PLANT = Plant()
INCIDENT_LOG = Path("incident_log.jsonl")

LEVELS = ["normal", "warning", "danger", "critical"]


def _level_for(key: str, value: float) -> str:
    s = STANDARDS[key]
    if value >= s["critical"]:
        return "critical"
    if value >= s["danger"]:
        return "danger"
    if value >= s["warn"]:
        return "warning"
    return "normal"


def _oxygen_level(value: float) -> str:
    if value < OXYGEN["low_critical"]:
        return "critical"
    if value < OXYGEN["low_danger"] or value > OXYGEN["high_danger"]:
        return "danger"
    return "normal"


def list_zones() -> dict:
    return {"zones": PLANT.zones()}


def read_sensors(zone: str) -> dict:
    """Latest environmental readings for a zone."""
    if zone not in PLANT.zones():
        return {"error": f"Unknown zone '{zone}'. Valid zones: {PLANT.zones()}"}
    return {"zone": zone, "readings": PLANT.read_zone(zone)}


def assess_environment(zone: str, readings: dict) -> dict:
    """Compare readings with exposure limits; return per-metric level and overall level."""
    findings, worst = [], 0
    for key, value in readings.items():
        if key == "o2_pct":
            level = _oxygen_level(value)
            name, unit, src = OXYGEN["name"], OXYGEN["unit"], OXYGEN["source"]
        elif key in STANDARDS:
            level = _level_for(key, value)
            s = STANDARDS[key]
            name, unit, src = s["name"], s["unit"], s["source"]
        else:
            continue
        worst = max(worst, LEVELS.index(level))
        if level != "normal":
            findings.append({"metric": key, "name": name, "value": value, "unit": unit,
                             "level": level, "basis": src})
    return {"zone": zone, "overall": LEVELS[worst], "findings": findings}


def list_workers() -> dict:
    return {"workers": PLANT.workers()}


def check_worker(worker_id: str) -> dict:
    """PPE compliance + fatigue + shift-length assessment for one worker."""
    w = next((x for x in PLANT.workers() if x["id"] == worker_id), None)
    if not w:
        return {"error": f"Unknown worker '{worker_id}'"}
    required = set(PPE_REQUIREMENTS.get(w["task"], PPE_REQUIREMENTS["general"]))
    missing = sorted(required - set(w["ppe_detected"]))
    perclos = w["perclos"]
    if perclos >= FATIGUE_GUIDANCE["danger_perclos"]:
        fatigue = "danger"
    elif perclos >= FATIGUE_GUIDANCE["warn_perclos"]:
        fatigue = "warning"
    else:
        fatigue = "normal"
    overlong = w["shift_hours"] > 10
    return {
        "worker": worker_id, "zone": w["zone"], "task": w["task"],
        "ppe_missing": missing, "ppe_compliant": not missing,
        "perclos": perclos, "fatigue_level": fatigue,
        "shift_hours": w["shift_hours"], "overlong_shift": overlong,
        "fatigue_basis": FATIGUE_GUIDANCE["source"],
    }


def lookup_guidance(metric: str) -> dict:
    """Standard, thresholds and recommended action for a metric (e.g. co_ppm, h2s_ppm, o2_pct, fatigue)."""
    if metric == "o2_pct":
        return OXYGEN
    if metric == "fatigue":
        return FATIGUE_GUIDANCE
    if metric in STANDARDS:
        return STANDARDS[metric]
    return {"error": f"Unknown metric '{metric}'", "known": list(STANDARDS) + ["o2_pct", "fatigue"]}


def log_incident(zone: str, severity: str, summary: str, recommended_actions: list) -> dict:
    """Append a structured incident record to the log."""
    record = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "zone": zone, "severity": severity,
              "summary": summary, "recommended_actions": recommended_actions}
    with INCIDENT_LOG.open("a") as f:
        f.write(json.dumps(record) + "\n")
    return {"logged": True, "record": record}


FUNCTIONS = {
    "list_zones": list_zones,
    "read_sensors": read_sensors,
    "assess_environment": assess_environment,
    "list_workers": list_workers,
    "check_worker": check_worker,
    "lookup_guidance": lookup_guidance,
    "log_incident": log_incident,
}

TOOL_SCHEMAS = [
    {"name": "list_zones", "description": "List monitored plant zones.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "read_sensors", "description": "Get latest gas, noise, temperature and oxygen readings for a zone.",
     "input_schema": {"type": "object", "properties": {"zone": {"type": "string"}}, "required": ["zone"]}},
    {"name": "assess_environment",
     "description": "Compare a zone's readings with exposure limits. Returns overall level and findings with the standard each is based on.",
     "input_schema": {"type": "object", "properties": {"zone": {"type": "string"}, "readings": {"type": "object"}},
                      "required": ["zone", "readings"]}},
    {"name": "list_workers", "description": "List workers on shift with zone and task.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "check_worker",
     "description": "Check one worker's PPE compliance, fatigue (PERCLOS) and shift length.",
     "input_schema": {"type": "object", "properties": {"worker_id": {"type": "string"}}, "required": ["worker_id"]}},
    {"name": "lookup_guidance",
     "description": "Get the standard, thresholds and recommended action for a metric (co_ppm, h2s_ppm, lel_pct, noise_dba, temp_c, o2_pct, fatigue).",
     "input_schema": {"type": "object", "properties": {"metric": {"type": "string"}}, "required": ["metric"]}},
    {"name": "log_incident",
     "description": "Record an incident or near-miss. Use only for warning level or above.",
     "input_schema": {"type": "object", "properties": {
         "zone": {"type": "string"}, "severity": {"type": "string", "enum": ["warning", "danger", "critical"]},
         "summary": {"type": "string"}, "recommended_actions": {"type": "array", "items": {"type": "string"}}},
         "required": ["zone", "severity", "summary", "recommended_actions"]}},
]


def run_tool(name: str, args: dict) -> dict:
    fn = FUNCTIONS.get(name)
    if not fn:
        return {"error": f"Unknown tool '{name}'"}
    try:
        return fn(**args)
    except TypeError as e:
        return {"error": f"Bad arguments for {name}: {e}"}
