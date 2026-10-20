"""
Turn a promptfoo results.json into a markdown PR comment.

Usage:
    python evals/summarize.py results.json <workflow_run_url>
"""
import json
import sys
from collections import defaultdict


def _results_list(output: dict) -> list:
    return output.get("results", {}).get("results", [])


def _case_name(result: dict) -> str:
    description = result.get("description") or (result.get("testCase") or {}).get("description", "unknown")
    return description.split(":")[0].strip()


def _group_by_provider(results: list) -> dict[str, dict[str, list]]:
    """Return {provider_label: {case_name: [result, ...]}}."""
    groups: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in results:
        provider = (r.get("provider") or {}).get("label", "unknown")
        groups[provider][_case_name(r)].append(r)
    return groups


def _run_totals(results: list) -> tuple[int, int, float, int]:
    """Return (total_runs, passing_runs, total_cost_usd, total_tokens)."""
    passing = sum(1 for r in results if r.get("success"))
    cost = sum(r.get("cost") or 0.0 for r in results)
    tokens = sum((r.get("tokenUsage") or {}).get("total", 0) for r in results)
    return len(results), passing, cost, tokens


def _header(groups: dict, results: list, run_url: str) -> str:
    total_runs, passing_runs, cost, tokens = _run_totals(results)

    passing_cases = sum(
        1
        for provider_cases in groups.values()
        for runs in provider_cases.values()
        if all(r.get("success") for r in runs)
    )
    total_cases = sum(len(cases) for cases in groups.values())

    cost_str = f" · ${cost:.4f}" if cost else ""
    token_str = f" · {tokens:,} tokens" if tokens else ""
    return (
        f"**{passing_cases}/{total_cases} cases passing** "
        f"({passing_runs}/{total_runs} runs)"
        f"{cost_str}{token_str} · [workflow run]({run_url})"
    )


def _case_table(provider_cases: dict[str, list]) -> str:
    header = "| Case | Runs | Accuracy | Hallucinations |"
    sep    = "|------|------|----------|----------------|"

    def sort_key(item):
        name, runs = item
        return (all(r.get("success") for r in runs), name)

    rows = []
    for name, runs in sorted(provider_cases.items(), key=sort_key):
        n = len(runs)
        passing = sum(1 for r in runs if r.get("success"))
        accuracy = sum((r.get("namedScores") or {}).get("field_accuracy", 0.0) for r in runs) / n
        hallucinations = sum(int((r.get("namedScores") or {}).get("hallucinations", 0)) for r in runs)
        icon = "✅" if passing == n else "❌"
        rows.append(f"| {icon} `{name}` | {passing}/{n} | {accuracy:.0%} | {hallucinations} |")

    return "\n".join([header, sep] + rows)


def _failure_details(groups: dict) -> str:
    lines = []
    for provider, cases in sorted(groups.items()):
        for name, runs in sorted(cases.items()):
            failing = [r for r in runs if not r.get("success")]
            if not failing:
                continue
            reasons = sorted({(r.get("gradingResult") or {}).get("reason", "") for r in failing} - {""})
            for reason in reasons:
                lines.append(f"**`{name}`** ({provider}) — {reason}")
    return "\n".join(lines)


def build_summary(output: dict, run_url: str) -> str:
    results = _results_list(output)
    groups = _group_by_provider(results)

    parts = [_header(groups, results, run_url)]

    for provider, cases in sorted(groups.items()):
        if len(groups) > 1:
            parts += ["", f"### {provider}"]
        parts += ["", _case_table(cases)]

    failures = _failure_details(groups)
    if failures:
        parts += [
            "",
            "<details>",
            "<summary>Failure details</summary>",
            "",
            failures,
            "",
            "</details>",
        ]

    return "\n".join(parts)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: summarize.py results.json <run_url>", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    print(build_summary(data, sys.argv[2]))
