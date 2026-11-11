
from datetime import datetime, timezone
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"

def main():
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if STATE_PATH.exists():
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    else:
        state = {
            "agent_name": "Digital Income Agent",
            "run_count": 0,
            "status": "initialized"
        }

    state["run_count"] += 1
    state["status"] = "heartbeat_ok"
    state["last_run_utc"] = datetime.now(timezone.utc).isoformat()

    STATE_PATH.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )

    print("Digital Income Agent: OK")
    print("Run:", state["run_count"])
    print("State saved.")

if __name__ == "__main__":
    main()
