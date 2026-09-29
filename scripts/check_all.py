"""Run isolated, credential-free project checks from any working directory."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = (
    "investment-risk-monitor-unified",
    "wealth-agent",
    "business-analytics-agent",
    "database-job-mutex",
)


def main():
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ENABLE_EXTERNAL_SERVICES": "false", "ENABLE_HISTORY": "false"}
    subprocess.run([sys.executable, 'scripts/check_publishable_tree.py'], cwd=ROOT, env=env, check=True)
    for project in PROJECTS:
        print(f"\nChecking {project}", flush=True)
        for args in (("scripts/check_privacy.py",), ("-m", "unittest", "discover", "-s", "tests", "-v"), ("demo.py",)):
            subprocess.run([sys.executable, *args], cwd=ROOT / project, env=env, check=True)
    print("\nAll four projects passed their offline checks.")


if __name__ == "__main__":
    main()
