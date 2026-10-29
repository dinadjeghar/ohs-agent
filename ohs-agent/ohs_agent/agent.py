"""OHS agent: Claude tool-use loop, plus a deterministic offline mode for demos without an API key."""
import json
import os

from .tools import TOOL_SCHEMAS, run_tool, LEVELS

MODEL = os.environ.get("OHS_MODEL", "claude-sonnet-5-5")

SYSTEM_PROMPT = """You are an occupational health and safety (OHS) monitoring agent for an industrial site.

Process for a safety sweep:
1. List zones and read sensors for each; assess every zone against exposure limits.
2. List workers and check each one for PPE compliance, fatigue and shift length.
3. For any warning/danger/critical finding, look up the guidance for that metric and log an incident.
4. Finish with a short shift-supervisor briefing: highest-priority risks first, each with the reading,
   the standard it is based on, and a concrete corrective action.

Rules: never invent readings or limits, only use tool results. Treat critical findings as stop-work.
State that thresholds are illustrative defaults and must be verified against site and local regulations.
You assist human safety officers; you do not replace their judgement."""


def run_online(task: str, max_steps: int = 25, verbose: bool = True) -> str:
    import anthropic

    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        resp = client.messages.create(model=MODEL, max_tokens=2048, system=SYSTEM_PROMPT,
                                      tools=TOOL_SCHEMAS, messages=messages)
        messages.append({"role": "assistant", "content": resp.content})
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        results = []
        for block in resp.content:
            if block.type == "tool_use":
                if verbose:
                    print(f"  -> {block.name}({json.dumps(block.input)[:100]})")
                out = run_tool(block.name, block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": json.dumps(out)})
        messages.append({"role": "user", "content": results})
    return "Stopped: step limit reached."


def run_offline(verbose: bool = True) -> str:
    """Rule-based sweep that calls the same tools in the same order the LLM would."""
    def call(name, **kw):
        if verbose:
            print(f"  -> {name}({json.dumps(kw)[:100]})")
        return run_tool(name, kw)

    items = []  # (priority, text)
    for zone in call("list_zones")["zones"]:
        readings = call("read_sensors", zone=zone)["readings"]
        a = call("assess_environment", zone=zone, readings=readings)
        if a["overall"] == "normal":
            continue
        actions = []
        for f in a["findings"]:
            g = call("lookup_guidance", metric=f["metric"])
            actions.append(g.get("action", ""))
            items.append((LEVELS.index(f["level"]),
                          f"[{f['level'].upper()}] {zone}: {f['name']} {f['value']} {f['unit']} "
                          f"({f['basis']}). Action: {g.get('action', '')}"))
        call("log_incident", zone=zone, severity=a["overall"],
             summary="; ".join(f"{f['name']} {f['value']} {f['unit']}" for f in a["findings"]),
             recommended_actions=[x for x in actions if x])

    for w in call("list_workers")["workers"]:
        c = call("check_worker", worker_id=w["id"])
        issues = []
        if c["ppe_missing"]:
            issues.append(f"missing PPE for {c['task']}: {', '.join(c['ppe_missing'])}")
        if c["fatigue_level"] != "normal":
            issues.append(f"fatigue {c['fatigue_level']} (PERCLOS {c['perclos']})")
        if c["overlong_shift"]:
            issues.append(f"shift length {c['shift_hours']} h")
        if issues:
            pri = 3 if (c["ppe_missing"] and c["fatigue_level"] == "danger") else 2
            items.append((pri, f"[{LEVELS[pri].upper()}] Worker {c['worker']} ({c['zone']}): "
                               + "; ".join(issues) + ". Action: pull from task, break/rotation, supervisor check-in."))
            call("log_incident", zone=c["zone"], severity=LEVELS[pri],
                 summary=f"{c['worker']}: " + "; ".join(issues),
                 recommended_actions=["Stop task until PPE corrected", "Mandatory rest and rotation"])

    items.sort(key=lambda x: -x[0])
    lines = ["SHIFT SAFETY BRIEFING (offline rule-based mode)", "=" * 48]
    lines += [f"{i}. {t}" for i, (_, t) in enumerate(items, 1)] or ["No issues found."]
    lines.append("\nNote: thresholds are illustrative defaults; verify against site and local regulations.")
    return "\n".join(lines)


def run(task: str = "Run a full safety sweep of the site and brief the shift supervisor.",
        offline: bool = False, verbose: bool = True) -> str:
    if offline or not os.environ.get("ANTHROPIC_API_KEY"):
        return run_offline(verbose)
    return run_online(task, verbose=verbose)
