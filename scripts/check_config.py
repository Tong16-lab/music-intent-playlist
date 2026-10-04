"""Security preflight; prints statuses only, never secret values."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=False)


def parse_env(path: Path) -> dict[str, tuple[int, str]]:
    values = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"invalid_env_line:{path.name}:{number}")
        name, value = line.split("=", 1)
        values[name.strip()] = (number, value.strip().strip("'\""))
    return values


def check() -> tuple[bool, list[str]]:
    messages = []
    example = ROOT / ".env.example"
    env = ROOT / ".env"
    if not example.is_file() or not env.is_file():
        return False, ["missing_env_or_example"]
    example_values = parse_env(example)
    if set(example_values) != {"OPENROUTER_API_KEY", "OPENROUTER_MODEL"} or any(value for _, value in example_values.values()):
        messages.append("example_not_blank")
    ignored = git("check-ignore", "-q", ".env").returncode == 0
    tracked = git("ls-files", "--error-unmatch", ".env").returncode == 0
    ever_tracked = bool(git("log", "--all", "--format=%h", "--", ".env").stdout.strip())
    if not ignored or tracked or ever_tracked:
        messages.append("env_git_exposure_risk")
    if any((ROOT / name).exists() for name in (".env.rtf", ".env.txt", ".env.example.rtf", ".env.example.txt")):
        messages.append("unprotected_env_variant_present")
    for name in git("ls-files").stdout.splitlines():
        file = ROOT / name
        if not file.is_file():
            continue
        try:
            content = file.read_text(encoding="utf-8")
        except UnicodeError:
            continue
        assignments = re.findall(r"^OPENROUTER_API_KEY\s*=\s*(\S+)", content, re.MULTILINE)
        non_placeholders = [value for value in assignments if not (value.startswith("<") and value.endswith(">"))]
        if "sk" + "-or-" in content or non_placeholders:
            messages.append("tracked_possible_secret")
            break
    local = parse_env(env)
    if not local.get("OPENROUTER_API_KEY", (None, ""))[1]:
        messages.append("missing_key")
    model_line, model = local.get("OPENROUTER_MODEL", (None, ""))
    if not model:
        messages.append("missing_model")
    if model == "google/gemini-2.5-flash":
        messages.append(f"legacy_model_at_line:{model_line}")
    return not messages, messages


if __name__ == "__main__":
    try:
        passed, issues = check()
    except (ValueError, OSError) as error:
        passed, issues = False, [str(error)]
    print("config_check=" + ("passed" if passed else "failed"))
    for issue in issues:
        print("issue=" + issue)
    raise SystemExit(0 if passed else 1)
