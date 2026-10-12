# ABORTED attempt (not a result)

Run started 2026-10-12 ~15:26 UTC against the deployed API under `PROTOCOL.md` (commit 43351b43). It was stopped after 3 of 30 questions
(Delhi Q1, Q2, Q3) because every answer was `source = "error"`: the server's Groq call fails with
`Error code: 404 - model_not_found: The model llama-3.1-8b-instant does not exist or you do not have access to it`.

Also observed: Delhi Q1 needed 3 retries (two 120 s read timeouts and one HTTP 502) before a 200 response; later calls took 15-26 s.

No scores were computed and none of these three answers is a result. Delhi Q1-Q3 have therefore been asked once in a broken state;
any full re-run after the assistant is fixed must be a new 30-question run in a new results folder, and its report must disclose this aborted attempt.
Hashes: see `aborted_record.json`.
