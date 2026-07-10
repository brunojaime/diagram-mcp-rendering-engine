from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


SPEC_ID = "016-diagram-mcp-rendering-engine"
EXPECTED_AC_IDS = {f"AC-{index:03d}" for index in range(1, 13)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the Diagram MCP SDD package.")
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[1],
        type=Path,
    )
    parser.add_argument(
        "--bridge-spec-root",
        default=Path("/home/batata/Projects/codex-cli-mobile-bridge") / "specs" / SPEC_ID,
        type=Path,
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    spec_root = repo_root / "specs" / SPEC_ID
    bridge_spec_root = args.bridge_spec_root.resolve()
    failures: list[str] = []

    traceability = _validate_spec_tree(spec_root, failures)
    collected = _collect_pytest_nodeids(repo_root, failures)
    if traceability:
        _validate_traceability_tests(repo_root, traceability, collected, failures)
    if bridge_spec_root.exists():
        _compare_spec_copies(spec_root, bridge_spec_root, failures)
    else:
        print(f"bridge_copy_skipped: {bridge_spec_root} does not exist")

    if failures:
        for failure in failures:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "spec_id": SPEC_ID,
                "pytest_nodeids": len(collected),
                "bridge_copy_compared": bridge_spec_root.exists(),
            },
            sort_keys=True,
        )
    )
    return 0


def _validate_spec_tree(spec_root: Path, failures: list[str]) -> dict[str, Any] | None:
    if not spec_root.is_dir():
        failures.append(f"spec root missing: {spec_root}")
        return None
    tree_path = spec_root / "tree.json"
    try:
        tree = json.loads(tree_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        failures.append(f"tree.json does not parse: {exc}")
        return None

    for rel in ("spec.md", "plan.md", "tasks.md", "metadata.yaml", "traceability.yaml"):
        if not (spec_root / rel).is_file():
            failures.append(f"required spec file missing: {rel}")

    for yaml_path in [spec_root / "metadata.yaml", spec_root / "traceability.yaml", *sorted((spec_root / "diagrams").glob("*.yaml"))]:
        try:
            yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            failures.append(f"YAML does not parse: {yaml_path.relative_to(spec_root)}: {exc}")

    for plan in tree.get("plans", []):
        plan_file = spec_root / str(plan.get("file", ""))
        if not plan_file.is_file():
            failures.append(f"tree plan reference missing: {plan.get('file')}")
        for task in plan.get("tasks", []):
            task_file = spec_root / str(task.get("file", ""))
            if not task_file.is_file():
                failures.append(f"tree task reference missing: {task.get('file')}")

    try:
        return yaml.safe_load((spec_root / "traceability.yaml").read_text(encoding="utf-8"))
    except Exception:
        return None


def _collect_pytest_nodeids(repo_root: Path, failures: list[str]) -> set[str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        failures.append(f"pytest collection failed: {result.stdout}{result.stderr}")
        return set()
    return {line.strip() for line in result.stdout.splitlines() if "::" in line}


def _validate_traceability_tests(
    repo_root: Path,
    traceability: dict[str, Any],
    collected: set[str],
    failures: list[str],
) -> None:
    criteria = traceability.get("acceptance_criteria") or {}
    missing_criteria = EXPECTED_AC_IDS.difference(criteria)
    extra_criteria = set(criteria).difference(EXPECTED_AC_IDS)
    if missing_criteria:
        failures.append(f"acceptance criteria missing: {sorted(missing_criteria)}")
    if extra_criteria:
        failures.append(f"unexpected acceptance criteria: {sorted(extra_criteria)}")

    for ac_id in sorted(EXPECTED_AC_IDS):
        tests = (criteria.get(ac_id) or {}).get("tests") or []
        if not tests:
            failures.append(f"{ac_id} has no real tests mapped")
            continue
        for test_ref in tests:
            path_text, _, name = str(test_ref).partition("::")
            if not (repo_root / path_text).is_file():
                failures.append(f"{ac_id} references missing test file: {test_ref}")
                continue
            if name and str(test_ref) not in collected:
                failures.append(f"{ac_id} references uncollected pytest nodeid: {test_ref}")


def _compare_spec_copies(left: Path, right: Path, failures: list[str]) -> None:
    left_files = sorted(path.relative_to(left).as_posix() for path in left.rglob("*") if path.is_file())
    right_files = sorted(path.relative_to(right).as_posix() for path in right.rglob("*") if path.is_file())
    if left_files != right_files:
        failures.append(f"spec copy file set differs: {sorted(set(left_files) ^ set(right_files))}")
        return
    diffs = [rel for rel in left_files if (left / rel).read_bytes() != (right / rel).read_bytes()]
    if diffs:
        failures.append(f"spec copies are not byte-identical: {diffs}")


if __name__ == "__main__":
    raise SystemExit(main())
