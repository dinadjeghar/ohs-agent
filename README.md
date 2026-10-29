[README (1).md](https://github.com/user-attachments/files/34116945/README.1.md)
# OHS Agent: AI Agent for Occupational Health & Safety Monitoring

An LLM agent that runs a safety sweep of an industrial site: it reads sensor feeds, checks worker PPE and fatigue, compares everything against exposure limits, logs incidents, and briefs the shift supervisor with prioritized corrective actions. A chart dashboard shows the same results visually.

Built with Claude tool use. Includes an offline mode so it runs without an API key.

![Dashboard](docs/dashboard-light.png)

## What it does

| Capability | Tool | Notes |
|---|---|---|
| Environmental monitoring | `read_sensors`, `assess_environment` | CO, H2S, %LEL, O2, noise, temperature |
| Worker safety | `check_worker` | PPE vs task requirements, fatigue (PERCLOS), shift length |
| Standards grounding | `lookup_guidance` | Every finding cites the limit it is based on |
| Incident logging | `log_incident` | Writes structured JSONL records |

The agent plans its own sweep: list zones, read and assess each, check workers, look up guidance for anything abnormal, log incidents, then write a prioritized briefing.

## Architecture

```
ESP32 / MQTT feed (simulated)      Camera PPE + fatigue signals (simulated)
            \                              /
             ----> tools.py (typed functions) <---- standards.py (limits)
                          |
                  agent.py: Claude tool-use loop
                          |
   Prioritized briefing + incident_log.jsonl + export_data.py -> dashboards
```

To go from demo to real: replace `simulator.py` with an MQTT subscriber (e.g. `paho-mqtt`) and feed `check_worker` from a YOLO PPE detector and an eye-aspect-ratio fatigue model.

## Run the agent

```bash
pip install -r requirements.txt
python demo.py --offline                  # no API key needed
export ANTHROPIC_API_KEY=...              # optional: use Claude as the planner
python demo.py
python -m pytest
```

Set `OHS_MODEL` to change the model (default `claude-sonnet-5-5`).

## Dashboards

There are two versions with the same charts: readings against limits, zone trends, worker PPE and fatigue, and prioritized findings.

**Static HTML (no server, works anywhere)**
```bash
python build_html.py            # writes docs/ohs-dashboard.html; open it in a browser
```

**Streamlit (interactive, with a real CSV download)**
```bash
streamlit run dashboard.py      # opens http://localhost:8501
```

### Google Colab

Open `notebooks/ohs_agent_colab.ipynb` in Colab. It runs the agent and shows the dashboard inline in a notebook cell, with no tunnel. To run the Streamlit version in Colab you need a public tunnel; Cloudflare's `cloudflared` works better than localtunnel, which can break Streamlit's lazily loaded widgets.

## Important limitations

- Sensor and worker data are simulated.
- Thresholds in `standards.py` are illustrative defaults based on commonly cited OSHA/NIOSH values. Verify against the regulations that apply to your site before any real use.
- This is a decision-support tool. It assists human safety officers and does not replace them or authorize entry into hazardous areas.

## Ideas for extension

- Live MQTT ingestion and a time-series store for trend and TWA (time-weighted average) calculations
- Human-in-the-loop approvals before escalation
- A combined worker risk score (fatigue, environment, PPE) for Industry 5.0 human-centric safety, validated against scenarios
- Multi-language briefings (English / French / Arabic)
