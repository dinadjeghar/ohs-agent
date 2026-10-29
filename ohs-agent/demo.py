"""Run the OHS agent. Uses Claude if ANTHROPIC_API_KEY is set, otherwise offline mode.

    python demo.py            # auto
    python demo.py --offline  # force offline
"""
import argparse

from ohs_agent.agent import run

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--offline", action="store_true")
    p.add_argument("--task", default="Run a full safety sweep of the site and brief the shift supervisor.")
    args = p.parse_args()
    print("Tool calls:")
    print("\n" + run(args.task, offline=args.offline))
