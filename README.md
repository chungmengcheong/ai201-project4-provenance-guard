# Provenance Guard

Provenance Guard is a Flask backend API that classifies submitted text as AI-generated, human-written, or uncertain. It combines two detection signals — an LLM classifier and a stylometric heuristic — into a single confidence score, applies a transparency label, logs every decision to a structured audit log, and handles creator appeals.

The two main design constraints were: (1) false positives are worse than false negatives on a creative platform, so the thresholds are asymmetric in favor of humans; and (2) the two signals had to be genuinely independent to be worth combining. An LLM signal and a structural/statistical signal satisfy that independence requirement; two LLM signals would not.

## Architecture

Two flows:

**Submission:** `POST /submit` → rate limiter → `detect_signal()` → `apply_label()` → `log_event()` → response. `detect_signal()` calls `assess_signal_llm()` and `assess_signal_stylometric()` in sequence and averages the results.

**Appeal:** `POST /appeal` → `log_event()` with `status="appeal"` and `creator_reasoning` → response message.

The audit log is shared between both flows. A submission produces a `scored` entry; an appeal produces a separate `appeal` entry referencing the same `content_id`. The log is JSONL — one JSON object per line, append-only.

### Endpoints

- `POST /submit` — accepts `text` (str) and `creator_id` (str); returns `content_id`, `status`, `label`, `confidence_score`, `signals`, and `message`
- `POST /appeal` — accepts `content_id`, `creator_id`, `label`, `confidence_score`, `signals`, and `creator_reasoning`; returns a confirmation message
- `GET /log` — returns all audit log entries as `{"entries": [...]}`

## Detection Signals

### Signal 1: LLM Classification

`assess_signal_llm()` calls Groq's `llama-3.3-70b-versatile` with a prompt that enumerates specific AI stylistic tells:

- Contrastive rhetorical framing ("This isn't about X, it's about Y")
- Self-answering rhetorical questions ("What changed? The math did.")
- Triplet framing ("Fast, cheap, and out of control.")
- Inspirational pivots ("This isn't just about AI. It's about humanity.")
- Universal authority without source ("Studies show that storytelling is 22 times more memorable.")
- Quotes with incorrect attribution

The LLM returns one of five categories, which are mapped to fixed scores:

| Category | Score |
|---|---|
| `clearly_ai` | 0.95 |
| `likely_ai` | 0.75 |
| `uncertain` | 0.50 |
| `likely_human` | 0.25 |
| `clearly_human` | 0.05 |

The mapping to fixed midpoints is intentional. Asking the LLM to return a raw float between 0 and 1 would produce numbers that look like probabilities but aren't calibrated. A categorical judgment that is then mapped to ordinal scores returns the probability score used by rest of the detection pipeline. 

Why this signal: LLMs capture semantic and stylistic coherence holistically. They can recognize AI tells that no simple statistic would catch — things like the rhetorical structure of a paragraph or the combination of formal vocabulary with inspirational framing.

Blind spot: formal or carefully-edited human writing can resemble AI output. Academic prose, business writing, and structured writing by non-native English speakers all hit some of the same patterns the LLM is looking for. The signal has no way to distinguish "AI-like style" from "human who writes formally."

### Signal 2: Stylometric Heuristics

`assess_signal_stylometric()` is pure Python with no external libraries. It computes two metrics:

- **Sentence length variance** — split on `.!?`, compute word counts per sentence, then variance across sentences. Higher variance means more human-like rhythm.
- **Type-token ratio (TTR)** — unique words divided by total words. Higher TTR means more diverse vocabulary.

Each metric is normalized and inverted so that low variance and low TTR both produce high scores (more AI-like):

```
variance_score = 1 - min(variance / 50, 1)
diversity_score = 1 - min(TTR / 0.95, 1)
stylometric_score = (variance_score + diversity_score) / 2
```

The divisors (50 and 0.95) were calibrated empirically rather than chosen by intuition. The original spec values (100 and 0.7) caused the TTR component to contribute nothing — all four test texts had TTR above 0.7, so `diversity_score` was 0 for every input. To fix this, I printed the raw variance and TTR values for each test case (observed ranges: variance 24–45, TTR 0.86–0.92) and set divisors that map those ranges to the active part of the score window.

Why this signal: it is structurally independent of the LLM signal. The LLM operates on meaning and style holistically; the stylometric signal operates on measurable structural properties. Their combination is more informative than either alone.

Blind spot: for short texts (3–5 sentences), sentence length variance has too few data points to separate anything meaningfully. In testing, stylometric scores clustered between 0.09–0.27 across all four test cases — the signal correctly orders them but produces narrow separation. The LLM signal carries most of the discriminative weight for short inputs.

## Confidence Scoring

Combined score = (LLM score + stylometric score) / 2. Simple average, no weighting.

The case for simple averaging: both signals are on the same scale (0–1 where 1 = AI-like), and they are genuinely independent. A weighted approach would have required a labeled validation set I didn't have. The unweighted average produces one behavior worth noting: the stylometric signal acts as a moderating force that pulls the LLM's high-confidence AI calls toward the center. This is desirable — it reduces the rate at which the system reaches `high-confidence AI` from a single short paragraph.

What I'd change for real deployment: the stylometric divisors were calibrated against four test inputs by hand. They work directionally, but they're not validated against a labeled distribution. Before deploying, I'd want to measure signal correlation and calibration error across a labeled dataset, and consider dropping the stylometric signal entirely if it turns out to add noise rather than signal for the content types the platform actually sees.

### Example Submissions

**High-confidence human** — casual restaurant review:

```
ok so i finally tried that new ramen place downtown and honestly? underwhelming. the broth was fine but they put WAY too much sodium in it and i was thirsty for like three hours after...
```

LLM score: 0.05 (`clearly_human`) | Stylometric: 0.089 | **Combined: 0.069** → `high-confidence human`

The LLM correctly identifies informal, personal language with no AI stylistic tells. The stylometric signal agrees: the text has high sentence variance (the one-word sentence "underwhelming." pulls the variance up) and relatively diverse vocabulary for its length.

**Uncertain** — AI-written paragraph on AI ethics:

```
Artificial intelligence represents a transformative paradigm shift in modern society. It is important to note that while the benefits of AI are numerous, it is equally essential to consider the ethical implications. Furthermore, stakeholders across various sectors must collaborate to ensure responsible deployment.
```

LLM score: 0.75 (`likely_ai`) | Stylometric: 0.239 | **Combined: 0.495** → `uncertain`

The LLM flags the formal structure and transitional phrases ("Furthermore", "It is important to note"). The stylometric signal is moderate — the sentences are more uniform than the ramen review but not extreme. The average brings the score to 0.495, just under the uncertain/AI boundary. This is the right behavior: the system shouldn't call a short paragraph `high-confidence AI` when the stylometric evidence is ambiguous.

## Transparency Labels

| Score | Label | Displayed text |
|---|---|---|
| 0.90–1.0 | `high-confidence AI` | "There is a high likelihood that the text is by an AI. We estimate that there is roughly 9 in 10 chance of this being AI generated." |
| 0.26–0.89 | `uncertain` | "It is difficult to say with high confidence whether the text is generated by an AI or written by a human." |
| 0.00–0.25 | `high-confidence human` | "There is a strong likelihood that the text is by a human. We estimate that there is a roughly 3 in 4 chance of this being written by a human." |

The thresholds are deliberately asymmetric. Reaching `high-confidence AI` requires a score of 0.90 or above — a 9-in-10 AI likelihood. Reaching `high-confidence human` only requires a score below 0.26, which corresponds to roughly a 3-in-4 human likelihood. The `uncertain` band is wide (0.26–0.89) by design. On a creative platform, a false positive — labeling a human creator's work as AI-generated — is a more damaging error than a false negative. The asymmetric thresholds mean the system defaults toward `uncertain` rather than toward `high-confidence AI` when the evidence is mixed.

## Rate Limiting

10 submissions per 3-minute window via Flask-Limiter with in-memory storage. On breach, the endpoint returns HTTP 429 with the message "There are too many submissions. Please try again later." The window resets naturally — no custom timeout state is needed.

Rationale: the detection pipeline takes roughly 15 seconds end-to-end (Groq API call plus stylometric computation). A legitimate creator submitting their own work wouldn't hit 10 submissions in 3 minutes under normal use. A script flooding the endpoint at that rate would exhaust the limit after 10 requests. Using Flask-Limiter's window semantics rather than a custom timeout keeps the implementation simple and testable.

Rate limit behavior under 12 rapid requests:

```
200 200 200 200 200 200 200 200 200 200 429 429
```

## Audit Log

Every submission, error, and appeal is appended to `audit_log.jsonl` as a single JSON object. The log is append-only — appeals add a new entry with `status="appeal"` rather than modifying the original scored entry.

Sample entries:

```json
{"content_id": "3f7a2b1e-9d4c-4a1f-b832-7c5e8d2f1a09", "creator_id": "user-42", "status": "scored", "label": "uncertain", "confidence_score": 0.495, "signals": {"LLM": 0.75, "LLM_reasoning": "The text features formal structure and transitional phrases typical of AI writing.", "stylometric": 0.239}, "message": null, "creator_reasoning": null, "timestamp": "2026-06-27T03:24:33Z"}
{"content_id": "3f7a2b1e-9d4c-4a1f-b832-7c5e8d2f1a09", "creator_id": "user-42", "status": "under_review", "label": "uncertain", "confidence_score": 0.495, "signals": {"LLM": 0.75, "LLM_reasoning": "The text features formal structure and transitional phrases typical of AI writing.", "stylometric": 0.239}, "message": null, "creator_reasoning": "I wrote this myself from personal experience. I am a non-native English speaker and my writing style may appear more formal than typical.", "timestamp": "2026-06-27T03:25:41Z"}
{"content_id": "9c4d2e5f-1a7b-4c3d-b053-9e70d4f3c281", "creator_id": "user-17", "status": "scored", "label": "high-confidence human", "confidence_score": 0.069, "signals": {"LLM": 0.05, "LLM_reasoning": "The writing is casual and conversational, lacking typical AI stylistic tendencies.", "stylometric": 0.089}, "message": null, "creator_reasoning": null, "timestamp": "2026-06-27T03:31:07Z"}
```

`GET /log` returns all entries as `{"entries": [...]}`.

## Known Limitations

**Formal human writing is the system's main failure mode.** Academic essays, legal writing, technical documentation, and structured writing by non-native English speakers all score 0.25–0.50 on the LLM signal. In testing, a passage about monetary policy and asset price inflation scored LLM=0.25, stylometric=0.245, combined=0.247 — right at the human/uncertain boundary. A slightly more polished version of the same passage would cross into `uncertain`. This is a property of the LLM signal: it works by pattern-matching stylistic tells, and formal human prose hits many of the same patterns. There is no fix within the current signal set. Addressing it would require a third signal that captures something the LLM can't — authorship fingerprinting, perplexity scoring against known human corpora, or platform metadata (typing cadence, revision history) that a real creative platform might have access to.

**Short texts make the stylometric signal unreliable.** Below 3–4 sentences, sentence length variance has too few data points to distinguish anything. A haiku or a two-sentence excerpt will return a compressed stylometric score regardless of origin, leaving the system dependent entirely on the LLM for short inputs. The `MINIMUM_LENGTH` guard (20 characters) prevents empty submissions but doesn't enforce enough text for the stylometric signal to function. A more appropriate minimum for the stylometric component would be around 100–150 characters (roughly 3 sentences), though this would make the system reject some legitimate short submissions.

## Spec Reflection

The spec helped most by requiring input/output contracts for every component before writing code. Defining exactly what `detect_signal()` returns — and separating it from what `apply_label()` returns — forced me to work through the data flow before touching the implementation. When the time came to wire the signals together, there was no ambiguity about what each function produced or expected. The unit tests followed directly from the contracts, which made them straightforward to write and easy to interpret when they failed.

The implementation diverged from the spec in one place: `user_friendly_description` was removed from both the log entries and the `/submit` response. The spec included it in both. During implementation I decided the `label` field was sufficient for audit purposes — storing a full prose sentence in every log entry is verbose and redundant when the label already identifies which description was shown. The API response dropped it for the same reason: the label alone is machine-readable, and any display layer can reconstruct the description from it. This was a deliberate tradeoff for log compactness over strict spec fidelity.

## AI Usage

**Milestone 3 — Submission endpoint + LLM signal.** I provided Claude with the Architecture, Submission flow, Detection pipeline, Detection signal #1 LLM classification, and Logging sections of `planning.md`. I asked it to generate incrementally: first the Flask app skeleton with a `POST /submit` route stub, then `assess_signal_llm()` in `detect.py`, then `log_event()`. 

**What I revised:**

I verified the output by reading through the function signatures against the spec contracts, confirming the Flask route returned a stub response, and updating the generated unit tests with the project provided examples of human and AI writing to test the generated code. 


**Milestone 4 — Stylometric heuristics + confidence scoring.** I provided Claude with the Architecture, Submission flow, Detection signal #2 stylometrics, and Apply Label sections of `planning.md`. I asked it to generate `assess_signal_stylometric()`. 

**What I revised:**

I verified by reading the function signature, running unit tests against the four test inputs, and inspecting the raw scores. The initial scores clustered between 0.27–0.38 across all four inputs — too narrow to be useful. I asked Claude to help calibrate the normalization divisors: we first printed raw variance and TTR values for each test text (variance 24–45, TTR 0.86–0.92), then set divisors (50 and 0.95) that map those observed ranges to the active part of the score window. I accepted both values. The resulting scores span 0.089–0.268 — still not wide for short texts, but directionally correct.

**Milestone 5 — Production layer.** I provided Claude with the Architecture, Submission flow, Apply Label, and Appeals flow sections of `planning.md`. I asked it to generate incrementally: `apply_label()`, the `POST /appeal` endpoint, and the rate limiter. 

**What I revised:**

I verified by reading through the function signatures, writing unit tests for `apply_label()` with inputs targeting all three label thresholds, and writing a unit test for the `/appeal` endpoint that checks the audit log entry directly.