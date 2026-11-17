import argparse
import json
import sqlite3
import sys
from pathlib import Path
from .core import (init_run, import_hermes, verify, judge_packet, import_judgment,
                   read_json, write_new, validate_task, now)


def parser():
    p = argparse.ArgumentParser(description="Local trajectory evaluation; no live service writes or API calls")
    sub = p.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate-task")
    check.add_argument("task")
    init = sub.add_parser("init")
    init.add_argument("task")
    init.add_argument("--root", default=".private/runs")
    init.add_argument("--model", required=True)
    init.add_argument("--provider", required=True)
    init.add_argument("--reasoning", default="not-recorded")
    init.add_argument("--environment", required=True)
    imp = sub.add_parser("import-hermes")
    imp.add_argument("run")
    imp.add_argument("--db", required=True)
    imp.add_argument("--session", required=True)
    imp.add_argument("--after-id", type=int)
    imp.add_argument("--through-id", type=int)
    ver = sub.add_parser("verify")
    ver.add_argument("run")
    ver.add_argument("--observation", required=True)
    judge = sub.add_parser("judge-packet")
    judge.add_argument("run")
    judge.add_argument("--verifier", required=True)
    ji = sub.add_parser("import-judgment")
    ji.add_argument("run")
    ji.add_argument("--packet", required=True)
    ji.add_argument("--response", required=True)
    ji.add_argument("--judge-model", required=True)
    ji.add_argument("--judge-prompt-version", required=True)
    report = sub.add_parser("report")
    report.add_argument("run")
    demo = sub.add_parser("demo")
    demo.add_argument("--root", default=".private/demo")
    return p


def main():
    args = parser().parse_args()
    try:
        if args.command == "validate-task":
            task = validate_task(read_json(args.task))
            print(task["id"] + ": valid")
        elif args.command == "init":
            print(init_run(args.task, args.root, args.model, args.provider, args.reasoning, args.environment))
        elif args.command == "import-hermes":
            if args.after_id is not None and args.through_id is not None and args.after_id >= args.through_id:
                raise ValueError("after-id must be smaller than through-id")
            print("Imported events:", import_hermes(args.run, args.db, args.session, args.after_id, args.through_id))
        elif args.command == "verify":
            print(verify(args.run, args.observation))
        elif args.command == "judge-packet":
            print(judge_packet(args.run, args.verifier))
        elif args.command == "import-judgment":
            print(import_judgment(args.run, args.packet, args.response, args.judge_model, args.judge_prompt_version))
        elif args.command == "report":
            run = Path(args.run)
            manifest = read_json(run / "manifest.json")
            trajectory = read_json(run / "trajectory.json")
            report = {"run_id": manifest["run_id"], "synthetic": manifest["synthetic"],
                      "visibility": manifest["visibility"], "events": len(trajectory["events"]),
                      "metrics_limitations": "No provider-call counts, latency or window-level cost inferred from message rows.",
                      "scores": [{"file": f.name, "result": read_json(f)} for f in sorted((run / "scores").glob("*.json"))]}
            print(json.dumps(report, ensure_ascii=False, indent=2))
        elif args.command == "demo":
            base = Path(__file__).resolve().parents[1]
            run = init_run(base / "tasks/calendar-conflict-proposal.json", args.root,
                           "synthetic-no-model", "none", "none", "synthetic-pipeline-only", synthetic=True)
            events = [{"id": "e1", "role": "user", "content": "내일 일정을 확인해줘.", "timestamp": now()},
                      {"id": "e2", "role": "tool", "tool_name": "calendar.read", "content": {"events": ["14:00-15:00 A", "14:30-15:30 B"]}, "timestamp": now()},
                      {"id": "e3", "role": "assistant", "content": "내일 두 일정이 겹칩니다. B를 15시 30분 이후로 옮기는 안을 제안합니다. 아직 변경하지 않았습니다.", "timestamp": now()}]
            write_new(run / "trajectory.json", {"schema_version": "1", "adapter": "synthetic-example", "events": events,
                       "warnings": ["Hand-authored pipeline fixture, not a model evaluation."]})
            observation = run / "observation.json"
            write_new(observation, {"observer": "synthetic-fixture", "observed_at": now(), "method": "fixture",
                       "independent_of_agent": True, "state": {"calendar_changed": False, "external_messages_sent": False,
                       "conflict_exists": True}})
            score = verify(run, observation)
            packet = judge_packet(run, score)
            print(json.dumps({"run": str(run), "verifier": str(score), "judge_packet": str(packet),
                              "notice": "Synthetic pipeline check only. No model or real service was called."}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError, sqlite3.Error) as exc:
        print("Error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
