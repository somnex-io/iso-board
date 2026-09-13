"""PostToolUse hook for mcp__perfboarder__export_board: save the board to perfboarder/<name>.json.

Commit that file to keep a history of the Perfboarder layout. `updatedAt` is dropped so an
export of an unchanged board leaves the file unchanged.
"""
import json
import os
import re
import sys


def board_from(resp):
    # MCP results reach hooks as a JSON string, a list of content blocks, or {"content": [...]}.
    if isinstance(resp, dict) and "content" in resp:
        resp = resp["content"]
    if isinstance(resp, list):
        resp = "".join(b.get("text", "") for b in resp if isinstance(b, dict))
    return json.loads(resp) if isinstance(resp, str) else resp


board = board_from(json.load(sys.stdin).get("tool_response"))
if not isinstance(board, dict) or "parts" not in board:
    sys.exit("save_perfboarder_export: tool_response is not a board export")
board.pop("updatedAt", None)
root = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
# The board name comes from the browser: keep it to one plain file name inside perfboarder/.
name = re.sub(r"[^A-Za-z0-9_-]+", "_", str(board.get("name") or "board"))
path = os.path.join(root, "perfboarder", f"{name}.json")
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, "w") as f:
    json.dump(board, f, indent=2)
    f.write("\n")
print(json.dumps({"systemMessage": f"Perfboarder board saved to {os.path.relpath(path, root)}"}))
