"""Illustrative OHS exposure limits and guidance.

These are commonly cited defaults (OSHA / NIOSH / confined-space practice) used to
drive the demo. Always verify against the regulation that applies to your site
(e.g. OSHA 29 CFR 1910 in the US, or national rules elsewhere) before real use.
"""

STANDARDS = {
    "co_ppm": {
        "name": "Carbon monoxide",
        "unit": "ppm",
        "warn": 35,       # NIOSH REL (8h TWA)
        "danger": 50,     # OSHA PEL (8h TWA)
        "critical": 200,  # NIOSH ceiling
        "source": "OSHA PEL 50 ppm (8h TWA); NIOSH REL 35 ppm, ceiling 200 ppm",
        "action": "Ventilate, stop hot work, evacuate if above ceiling, check combustion sources.",
    },
    "h2s_ppm": {
        "name": "Hydrogen sulfide",
        "unit": "ppm",
        "warn": 10,       # NIOSH REL 10 ppm (10-min ceiling)
        "danger": 20,     # OSHA general industry ceiling
        "critical": 50,   # OSHA peak limit
        "source": "OSHA ceiling 20 ppm; NIOSH REL 10 ppm (10 min); IDLH 100 ppm",
        "action": "Don SCBA, evacuate upwind, isolate source, notify emergency response.",
    },
    "lel_pct": {
        "name": "Combustible gas",
        "unit": "% LEL",
        "warn": 10,
        "danger": 20,
        "critical": 40,
        "source": "Common industry alarm practice: 10% LEL alert, 20% LEL evacuate",
        "action": "Eliminate ignition sources, ventilate, evacuate area at danger level.",
    },
    "noise_dba": {
        "name": "Noise",
        "unit": "dBA",
        "warn": 85,       # OSHA action level
        "danger": 90,     # OSHA PEL 8h
        "critical": 115,  # OSHA max continuous
        "source": "OSHA 1910.95: action level 85 dBA, PEL 90 dBA (8h TWA)",
        "action": "Require hearing protection, limit exposure time, enroll in hearing conservation.",
    },
    "temp_c": {
        "name": "Ambient temperature",
        "unit": "C",
        "warn": 32,
        "danger": 38,
        "critical": 41,
        "source": "General heat-stress guidance; use WBGT-based limits for formal assessment",
        "action": "Enforce water/rest/shade cycles, acclimatize workers, watch for heat illness.",
    },
}

# Oxygen is a two-sided limit, handled separately.
OXYGEN = {
    "name": "Oxygen",
    "unit": "%",
    "low_danger": 19.5,
    "high_danger": 23.5,
    "low_critical": 16.0,
    "source": "OSHA confined space guidance: atmosphere below 19.5% or above 23.5% O2 is hazardous",
    "action": "No entry; ventilate and re-test; use supplied air if entry is unavoidable.",
}

PPE_REQUIREMENTS = {
    "welding": ["helmet", "gloves", "face_shield", "boots"],
    "confined_space": ["helmet", "gas_monitor", "harness", "boots"],
    "general": ["helmet", "vest", "boots"],
    "chemical": ["goggles", "gloves", "respirator", "boots"],
}

FATIGUE_GUIDANCE = {
    "source": "Fatigue indicators: PERCLOS (share of time eyes are >80% closed), blink duration, yawning",
    "warn_perclos": 0.15,
    "danger_perclos": 0.30,
    "action": "Mandatory break, task rotation, supervisor check-in; avoid safety-critical tasks.",
}
