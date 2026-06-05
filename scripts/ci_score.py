#!/usr/bin/env python3
"""Lance pytest et affiche un score lisible X/Y pour la CI et en local."""

import re
import subprocess
import sys


def main():
    test_path = sys.argv[1] if len(sys.argv) > 1 else "tests"
    result = subprocess.run(
        ["pytest", test_path, "-v", "--tb=short"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    out = result.stdout + result.stderr

    passed = failed = 0
    m = re.search(r"(\d+) passed", out)
    if m:
        passed = int(m.group(1))
    m = re.search(r"(\d+) failed", out)
    if m:
        failed = int(m.group(1))
    total = passed + failed if (passed + failed) > 0 else "?"

    banner = "=" * 52
    def _out(msg):
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode("ascii", errors="replace").decode("ascii"))

    _out(banner)
    _out(f"  SCORE HACKATHON (tests publics) : {passed}/{total}")
    _out(banner)
    _out("")
    _out(out)

    if result.returncode != 0:
        print("::error::Des tests ont échoué. Corrigez votre implémentation.")
    else:
        print(f"::notice::Tous les tests publics sont passés ({passed}/{total}).")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
