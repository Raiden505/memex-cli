import sys

from recall.config import Config, ConfigError, load_config

_HELP = """
Commands:
  /add <text>     Force-store text as a memory
  /ask <text>     Force-treat text as a question
  /search <text>  Show raw matching memories (no AI answer)
  /list           Show all stored memories with their ids
  /forget <id>    Delete a memory by id
  /count          How many memories are stored
  /help           Show this help
  /quit           Exit

Or just type naturally — statements are stored, questions are answered (Phase 4+).
"""

_NOT_YET = "[not implemented yet — coming in a later phase]"


def _dispatch(line: str, cfg: Config) -> bool:
    """Handle one line of input. Returns False to exit the loop."""
    line = line.strip()
    if not line:
        return True

    if not line.startswith("/"):
        print(_NOT_YET)
        return True

    parts = line.split(None, 1)
    cmd = parts[0].lower()

    if cmd == "/quit":
        print("Goodbye.")
        return False

    if cmd == "/help":
        print(_HELP)
        return True

    if cmd in ("/add", "/ask", "/search", "/list", "/forget", "/count"):
        print(_NOT_YET)
        return True

    print(f"Unknown command: {cmd}  (type /help for a list)")
    return True


def main() -> None:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"\nSetup required:\n{exc}")
        sys.exit(1)

    print("Recall — your personal memory CLI")
    print("Memories stored: 0")
    print('Type /help for commands or /quit to exit.\n')

    while True:
        try:
            line = input("you › ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not _dispatch(line, cfg):
            break
