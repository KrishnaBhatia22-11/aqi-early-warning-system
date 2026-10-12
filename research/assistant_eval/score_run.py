"""Score a finished run: mechanical scores from scoring.py + the scorer's manual decisions.

    python -m research.assistant_eval.score_run <results_dir> [--auto-only]

--auto-only writes scores_auto.csv (preliminary, with REVIEW flags) so the scorer can read the
answers and write manual_scores.json; the final pass merges both into scores.csv and SUMMARY.md.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from research.assistant_eval import common as c
from research.assistant_eval import scoring as sc

CRITERIA = ["value_correct", "category_correct", "advice_consistent", "pollutant_correct",
            "accuracy_claim_ok", "abstained", "staleness_disclosed", "unsupported_statement"]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def answer_text(record: dict) -> str:
    return ((record.get("response") or {}).get("reply") or "").strip()


def auto_scores(record: dict, truth: dict) -> dict:
    text, qtype = answer_text(record), record["type"]
    snapshot = truth.get("city_data_mode") == "snapshot" or truth.get("top_data_mode") == "snapshot"
    out = {c_: None for c_ in CRITERIA}
    if record["answer_failed"]:
        for key, applies in (("value_correct", qtype == "value"), ("category_correct", qtype == "category"),
                             ("advice_consistent", qtype == "advice"), ("accuracy_claim_ok", qtype == "accuracy"),
                             ("abstained", qtype == "unanswerable")):
            out[key] = 0 if applies else None
        out["unsupported_statement"] = 0
        return out
    gt_aqi, gt_cat = truth["aqi"], truth["category"]
    if qtype == "value":
        out["value_correct"] = sc.value_correct(text, gt_aqi)
        out["category_correct"] = sc.category_correct(text, gt_cat, required=False)
    elif qtype == "category":
        out["category_correct"] = sc.category_correct(text, gt_cat, required=True)
    elif qtype == "advice":
        out["category_correct"] = sc.category_correct(text, gt_cat, required=False)
        out["advice_consistent"] = "MANUAL"
    elif qtype == "pollutant":
        out["pollutant_correct"] = None
    elif qtype == "accuracy":
        out["accuracy_claim_ok"] = sc.accuracy_claim_ok(text)
    elif qtype == "unanswerable":
        out["abstained"] = sc.abstained(text)
    if qtype in ("value", "category", "advice", "pollutant"):
        out["staleness_disclosed"] = sc.staleness_disclosed(text, snapshot)
    out["unsupported_statement"] = "MANUAL"
    return out


def fmt(value) -> str:
    return "NA" if value is None else str(value)


def write_auto(results: Path) -> None:
    raw, truth = load_jsonl(results / "raw_answers.jsonl"), {t["id"]: t for t in load_jsonl(results / "ground_truth.jsonl")}
    with (results / "scores_auto.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "source", "gt_aqi", "gt_category", "gt_mode"] + CRITERIA)
        for record in raw:
            t = truth[record["id"]]
            scores = auto_scores(record, t)
            writer.writerow([record["id"], record["source"], t["aqi"], t["category"], t["city_data_mode"]] + [fmt(scores[k]) for k in CRITERIA])


def finalize(results: Path) -> None:
    raw = load_jsonl(results / "raw_answers.jsonl")
    truth = {t["id"]: t for t in load_jsonl(results / "ground_truth.jsonl")}
    manual = json.loads((results / "manual_scores.json").read_text(encoding="utf-8"))
    rows, overrides = [], []
    for record in raw:
        qid = record["id"]
        auto, entry = auto_scores(record, truth[qid]), manual[qid]
        final, notes = dict(auto), []
        for criterion, spec in entry.get("overrides", {}).items():
            if not spec.get("reason"):
                raise ValueError(f"{qid}: override of {criterion} needs a reason")
            overrides.append({"id": qid, "criterion": criterion, "auto": fmt(auto.get(criterion)), "final": fmt(spec["value"]), "reason": spec["reason"]})
            final[criterion] = spec["value"]
        for criterion in ("advice_consistent", "unsupported_statement"):
            if final[criterion] == "MANUAL":
                if criterion not in entry:
                    raise ValueError(f"{qid}: manual score for {criterion} missing")
                final[criterion] = entry[criterion]
        unresolved = [k for k, v in final.items() if v in ("REVIEW", "MANUAL")]
        if unresolved:
            raise ValueError(f"{qid}: unresolved {unresolved}")
        zeros = [k for k, v in final.items() if (v == 0 and k != "unsupported_statement") or (k == "unsupported_statement" and v == 1)]
        if zeros and not entry.get("justification"):
            raise ValueError(f"{qid}: justification required for {zeros}")
        rows.append({
            "id": qid, "city": record["city"], "type": record["type"], "source": record["source"],
            "answer_failed": record["answer_failed"], "retries": record["retries"],
            "gt_aqi": truth[qid]["aqi"], "gt_category": truth[qid]["category"], "gt_mode": truth[qid]["city_data_mode"], "gt_as_of": truth[qid]["city_as_of"],
            **{k: fmt(final[k]) for k in CRITERIA},
            "unverifiable_context_statement": entry.get("unverifiable_context_statement", 0),
            "unsupported_quote": entry.get("unsupported_quote", ""), "justification": entry.get("justification", ""),
            "answer": answer_text(record),
        })
    with (results / "scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    write_summary(results, rows, overrides)
    record = {"scoring_output_file_sha256": {p.name: c.sha256_file(p) for p in sorted(results.iterdir())
                                             if p.name in ("scores.csv", "SUMMARY.md", "manual_scores.json", "scores_auto.csv")},
              "run_files_sha256_at_scoring": {p.name: c.sha256_file(p) for p in sorted(results.iterdir())
                                              if p.name in ("raw_answers.jsonl", "ground_truth.jsonl", "run_record.json")}}
    (results / "scoring_record.json").write_text(json.dumps(record, indent=2), encoding="utf-8")


def tally(rows: list[dict], criterion: str) -> tuple[int, int]:
    applicable = [r for r in rows if r[criterion] != "NA"]
    if criterion == "unsupported_statement":
        return sum(1 for r in applicable if r[criterion] == "1"), len(applicable)
    return sum(1 for r in applicable if r[criterion] == "1"), len(applicable)


def write_summary(results: Path, rows: list[dict], overrides: list[dict]) -> None:
    lines = ["# Assistant evaluation: scores", "", f"Run folder: `{results.name}`. {len(rows)} answers; "
             f"failed answers (source != groq): {sum(1 for r in rows if r['answer_failed'])}; retries used: {sum(int(r['retries']) for r in rows)}.", "",
             "Scorer: Claude (LLM), not independent; see PROTOCOL.md. `unsupported_statement` counts answers WITH an unsupported statement (lower is better).", "",
             "## Counts per criterion (k of n applicable)", "", "| criterion | k | n |", "|---|---|---|"]
    for criterion in CRITERIA:
        k, n = tally(rows, criterion)
        lines.append(f"| {criterion} | {k} | {n} |")
    lines += ["", "## Per city (k of n applicable, same criteria)", "", "| city | " + " | ".join(CRITERIA) + " |", "|---|" + "---|" * len(CRITERIA)]
    for city in dict.fromkeys(r["city"] for r in rows):
        sub = [r for r in rows if r["city"] == city]
        cells = []
        for criterion in CRITERIA:
            k, n = tally(sub, criterion)
            cells.append(f"{k}/{n}" if n else "NA")
        lines.append(f"| {city} | " + " | ".join(cells) + " |")
    lines += ["", "## Every answer scored 0 (or unsupported = 1), with justification", ""]
    for r in rows:
        bad = [k for k in CRITERIA if (k != "unsupported_statement" and r[k] == "0") or (k == "unsupported_statement" and r[k] == "1")]
        if bad:
            lines += [f"- **{r['id']}** ({', '.join(bad)}): {r['justification']}" + (f' Quote: "{r["unsupported_quote"]}"' if r["unsupported_quote"] else "")]
    unverif = [r["id"] for r in rows if str(r["unverifiable_context_statement"]) == "1"]
    lines += ["", f"## Unverifiable context statements (not counted as unsupported): {', '.join(unverif) or 'none'}", "",
              "## Overrides of mechanical (code) scores", ""]
    lines += [f"- {o['id']} {o['criterion']}: {o['auto']} -> {o['final']}. {o['reason']}" for o in overrides] or ["- none"]
    (results / "SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--auto-only", action="store_true")
    args = parser.parse_args()
    if args.auto_only:
        write_auto(args.results)
    else:
        write_auto(args.results)
        finalize(args.results)


if __name__ == "__main__":
    main()
