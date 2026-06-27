import uuid
from flask import Flask, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
from datetime import datetime, timezone
import config

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

@app.route("/")
def home():
    return "Provenance Guard is running."

@app.route("/submit", methods=["POST"])
@limiter.limit("10 per minute;100 per day")
def submit():
    """Handle content submission and return a placeholder response."""
    data = request.get_json()
    text = data.get("text")
    creator_id = data.get("creator_id")
    content_id = str(uuid.uuid4())

    # Placeholder response — wire in your detection signal next.
    return jsonify({
        "content_id": content_id,
        "attribution": "uncertain",
        "confidence": 0.5,
        "label": "We're not sure who wrote this.",
    })

@app.route("/appeal", methods=["POST"])
def appeal():
    """Handle content appeal and return a placeholder response."""
    data = request.get_json()
    content_id = data.get("content_id")
    reasoning = data.get("creator_reasoning")

    # Update the content's status and log the appeal (see section 6).
    return jsonify({
        "content_id": content_id,
        "status": "under_review",
        "message": "Your appeal was received and is under review.",
    })

def log_event(entry):
    """Log an event to the audit log."""
    entry["timestamp"] = datetime.now(timezone.utc).isoformat()
    with open(config.LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

@app.route("/logs", methods=["GET"])
def read_log(limit=20):
    """Read the last `limit` entries from the audit log.

    The `limit` can be provided as a query param, e.g. /logs?limit=10
    """
    # allow override from query parameter
    try:
        limit = int(request.args.get("limit", limit))
    except (TypeError, ValueError):
        limit = 20

    try:
        with open(config.LOG_FILE) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return jsonify([])

    # parse each non-empty line as JSON
    entries = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            # skip malformed lines
            continue

    # return only the most recent `limit` entries
    if limit is not None and isinstance(limit, int) and limit > 0:
        entries = entries[-limit:]

    return jsonify(entries)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
