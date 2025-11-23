"""Interactive simulation runner for WishlistOps.

Prompts user for Gemini API key (format validation only) then runs a
fully mocked end-to-end workflow:
 1. Simulated git commits
 2. AI text (mock Gemini) generation using model: models/gemini-flash-lite-latest
 3. AI image (mock Gemini) banner generation using model: models/imagen-4.0-generate-001
 4. Discord preview + approval (mocked)
 5. Steam announcement compliance validation + publish simulation
 6. Artifact persistence under simulation/output/

Outputs a concise summary to stdout and writes detailed JSON + files.
No network calls are performed; the API key is not stored.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from wishlistops.models import Config, AIConfig

from simulation.mock_services import run_simulation


CONFIG_PATH = Path("wishlistops/config.json")
OUTPUT_PATH = Path("simulation/output")


def load_config() -> Config:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Override models with user requested simulation models
    raw["ai"]["model_text"] = "models/gemini-flash-lite-latest"
    raw["ai"]["model_image"] = "models/imagen-4.0-generate-001"
    cfg = Config(**raw)
    return cfg


def obtain_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key:
        print("Using GEMINI_API_KEY from environment (not persisted).")
        return env_key
    # Prompt user
    key = input("Enter Gemini API Key (format AIza...): ").strip()
    if not key.startswith("AIza"):
        raise SystemExit("Invalid key format. Expected to start with 'AIza'. Aborting.")
    return key


def main() -> None:
    print("WishlistOps Simulation Runner")
    print("--------------------------------")
    api_key = obtain_api_key()  # Format check only
    # Immediately discard reference after format validation – no network calls.
    del api_key

    config = load_config()
    summary = run_simulation(config, OUTPUT_PATH)

    print("\nSimulation Complete ✔")
    print("Artifacts written to:", OUTPUT_PATH)
    print("Steam Compliance:")
    for k, v in summary["steam_compliance"].items():
        print(f" - {k}: {v}")
    print("\nAnnouncement Title:")
    print(" ", summary["announcement"]["title"])
    print("\nAnnouncement Body Excerpt:")
    print(" ", summary["announcement"]["body_excerpt"])
    print("\nBanner Path:")
    print(" ", summary["banner"]["path"])
    print("\nSteam Publish (Simulated):")
    print(" ", summary["steam_publish"]["steam_url"])
    print("\nCommit Summary:")
    print(f" Total Commits: {summary['commits'].__len__()}")
    features = [c for c in summary['commits'] if c['commit_type'] == 'feature']
    bugfixes = [c for c in summary['commits'] if c['commit_type'] == 'bugfix']
    internal = [c for c in summary['commits'] if c['commit_type'] == 'internal']
    print(f"  Features: {len(features)} | Bug Fixes: {len(bugfixes)} | Internal: {len(internal)}")
    print("\nRun complete. Review JSON for full details: workflow_summary.json")


if __name__ == "__main__":
    main()
