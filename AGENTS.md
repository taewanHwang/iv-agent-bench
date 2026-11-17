# IV Agent Bench contributor instructions

- Read README.md and docs/local-workflow.md before running an evaluation.
- The benchmark runner is separate from the agent under test. Do not repair an evaluated answer without recording a human/Codex intervention.
- Current CLI imports completed Hermes sessions; it does not launch Hermes or connect accounts. Never change the user's live gateway/provider as a side effect.
- Keep original trajectories, account data, credentials and judge packets under `.private/` or outside Git. Do not commit private data or send it to an external judge without checking scope.
- Shared data requires human review. No automatic publication or claim that regex redaction guarantees privacy.
- Each task must link its source evidence and state authorization, environment and success conditions. Candidate tasks are not calibrated benchmarks.
- Accept different valid tool paths. Prefer independently observed state to final-answer claims; unknown is distinct from fail. LLM judgments cite event IDs and retain uncertainty.
- Preserve task/run/scoring versions. Re-scoring creates a new result. Never silently replace raw trajectories or historical scores.
- Synthetic examples test the evaluation pipeline, not model performance. Label them accordingly.
- Validate changes with `python3 -m unittest discover -s tests -v` and the documented demo. Do not call paid APIs or write to real services during these checks.
