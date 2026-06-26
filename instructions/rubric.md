
### Project 4: Provenance Guard

Total Points: **25pts** + 4pts bonus

Required Features

| **3pts** | **Content Submission Endpoint**                                                         |
| -------- | --------------------------------------------------------------------------------------- |
| 1        | Demo or source shows a text submission to the API returning a structured JSON response. |
| 1        | The response includes an attribution result and a confidence score.                     |
| 1        | The response includes transparency label text (not just a raw score).                   |

|**2pts**|**Multi-Signal Detection Pipeline**|
|---|---|
|1|README names 2 or more detection signals and explains what each one captures — not just what tool was used, but what property of the text it measures, and what each signal misses.|
|1|Demo or source shows results that reference or visibly reflect both signals (e.g., individual signal scores shown alongside the combined score).|

|**2pts**|**Confidence Scoring with Uncertainty**|
|---|---|
|1|Demo or source shows at least two submissions with noticeably different confidence scores — a high-confidence case and a lower-confidence case.|
|1|README explains how signals are combined into a confidence score and includes some description of how the student validated that scores are meaningful (e.g., tested inputs that should produce different scores, or described the thresholds separating label categories).|

|**3pts**|**Transparency Label**|
|---|---|
|1|README includes a mockup of the transparency label — a screenshot or a text/markdown mockup showing the actual label text as a user would see it.|
|1|The label uses plain language — no jargon like "classifier output" or "logit score." A non-technical reader could understand what it means.|
|1|The label visibly differs between high-confidence and low-confidence results — different text, not just a different number.|

|**2pts**|**Appeals Workflow**|
|---|---|
|1|Demo or source shows an appeal being submitted with creator reasoning included.|
|1|Demo or source shows the content's status updated to "under review" and the appeal visible in the audit log.|

|**2pts**|**Rate Limiting**|
|---|---|
|1|Demo or source shows rate limiting in action — what happens when the limit is hit (e.g., a 429 response or an error message).|
|1|README documents the specific limits chosen and provides reasoning tied to realistic usage patterns on a writing platform — not just "I used the default."|

|**3pts**|**Audit Log**|
|---|---|
|1|Demo or source shows the audit log with at least 3 entries; each entry visibly includes the attribution result, confidence score, and timestamp.|
|1|Log format is structured — JSON, a table, or a formatted log file. Unformatted console output does not qualify.|
|1|At least one appeal is visible in the log, showing the appeal alongside the original classification entry.|

|**4pts**|**`planning.md`**|
|---|---|
|1|Detection signals are described with explanation of what each measures and how their Output are combined.|
|1|Uncertainty representation is addressed — specific thresholds or score ranges are defined, not just "it will show a score."|
|1|Transparency label variants are written out for at least the high-confidence AI, uncertain, and high-confidence human cases.|
|1|Appeals workflow and at least two anticipated edge cases are described with enough specificity to be useful pre-work; an `## AI Tool Plan` section identifies at least one milestone where AI tools will be used for code generation, specifying what spec sections and diagram will be provided as input.|

|**2pts**|**README**|
|---|---|
|1|Known limitations section names at least one specific content type the system would likely misclassify, with explanation tied to the signals — not a generic disclaimer.|
|1|Spec reflection is present and substantive — describes a real way implementation diverged from the plan and why.|

|**2pts**|**AI Usage**|
|---|---|
|1|Section describes at least 2 specific instances of AI tool use: what the student directed the AI to do and what the output was.|
|1|Each instance includes what the student revised, overrode, or decided differently — not just "I used AI to write this function."|