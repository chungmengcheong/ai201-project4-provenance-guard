"""
Provenance Guard — end-to-end demo

Requires the Flask server to be running:
    python app.py

Then run this script in a separate terminal:
    python demo.py
"""

import json
import urllib.request

BASE_URL = "http://localhost:5001"

BORDERLINE_EDITED_AI = (
    "I've been thinking a lot about remote work lately. There are genuine tradeoffs — "
    "flexibility and no commute on one side, isolation and blurred work-life boundaries "
    "on the other. Studies show productivity varies widely by individual and role type."
)

USER_REASON = (
    "I wrote this myself from personal experience. "
    "I am a non-native English speaker and my writing style may appear more formal than typical."
)


def post(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def show(label, payload, response):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"\nRequest payload:\n{json.dumps(payload, indent=2)}")
    print(f"\nResponse:\n{json.dumps(response, indent=2)}")


# --- Step 1: Submit content ---

submit_payload = {
    "text": BORDERLINE_EDITED_AI,
    "creator_id": "demo-user-1",
}

print("\nProvenance Guard — end-to-end demo")
print("Press Enter after each step to continue.\n")
input("Step 1: POST /submit  (press Enter)")

submit_response = post("/submit", submit_payload)
show("POST /submit", submit_payload, submit_response)

content_id = submit_response.get("content_id")
print(f"\ncontent_id to use in appeal: {content_id}")

# --- Step 2: Appeal ---

appeal_payload = {
    "content_id": content_id,
    "creator_id": "demo-user-1",
    "label": submit_response.get("label"),
    "confidence_score": submit_response.get("confidence_score"),
    "signals": submit_response.get("signals"),
    "creator_reasoning": USER_REASON,
}

input("\nStep 2: POST /appeal  (press Enter)")

appeal_response = post("/appeal", appeal_payload)
show("POST /appeal", appeal_payload, appeal_response)

# --- Step 3: Show audit log ---

input("\nStep 3: GET /log  (press Enter)")

req = urllib.request.Request(f"{BASE_URL}/log")
with urllib.request.urlopen(req) as resp:
    log_response = json.loads(resp.read())

print(f"\n{'='*60}")
print("  GET /log — matched submission + appeal entries")
print(f"{'='*60}")

entries = log_response.get("entries", [])
matched = [e for e in entries if e.get("content_id") == content_id]
print(f"\n{json.dumps(matched, indent=2)}")
