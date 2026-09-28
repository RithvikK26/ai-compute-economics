"""Small offline review gate for documentation links, license hashes and local debris."""

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED = {".venv", ".git", "__pycache__", ".pytest_cache", ".ruff_cache", "artifacts"}


def main():
    errors = []
    files = [
        p
        for p in ROOT.rglob("*")
        if p.is_file() and not IGNORED.intersection(p.relative_to(ROOT).parts)
    ]
    secrets = re.compile(
        r"AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36}|-----BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY-----"
    )
    local_paths = re.compile(r"/(?:Users|home)/[^\s/]+/")
    for path in files:
        relative = path.relative_to(ROOT)
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
        if secrets.search(text):
            errors.append(f"Potential credential: {relative}")
        # Upstream benchmark logs may contain upstream machine paths; they stay immutable.
        if relative.parts[0] != "data" and local_paths.search(text):
            errors.append(f"Local home path: {relative}")
        if path.suffix == ".md":
            for target in re.findall(r"\]\(([^)]+)\)", text):
                target = target.strip("<>")
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.path:
                    continue
                if not (path.parent / unquote(parsed.path)).exists():
                    errors.append(f"Broken local link: {relative} -> {target}")
    license_meta = json.loads((ROOT / "docs/licenses/provenance.json").read_text())
    license_path = ROOT / "docs/licenses" / license_meta["artifact"]
    if hashlib.sha256(license_path.read_bytes()).hexdigest() != license_meta["sha256"]:
        errors.append("Supplementary license hash mismatch")
    if not (ROOT / "LICENSE").read_text().startswith("MIT License"):
        errors.append("Original-code MIT license missing")
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        json.dumps(
            {
                "status": "PASS",
                "reviewed_files": len(files),
                "checks": [
                    "local Markdown targets",
                    "supplementary license hash",
                    "MIT license",
                    "local home paths",
                    "credential patterns",
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
