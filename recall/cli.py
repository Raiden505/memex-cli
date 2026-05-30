import sys

from supabase import Client

from recall.config import Config, ConfigError, load_config
from recall import embeddings, llm, router, store

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

Or just type naturally — statements are stored, questions are answered automatically.
"""


def _do_store(text: str, cfg: Config, client: Client) -> None:
    embedding = embeddings.embed(text, cfg, task_type="RETRIEVAL_DOCUMENT")
    mem_id = store.add_memory(client, text, embedding, cfg.user_id)
    print(f"Saved. (id: {mem_id})")


def _do_query(text: str, cfg: Config, client: Client) -> None:
    embedding = embeddings.embed(text, cfg, task_type="RETRIEVAL_QUERY")
    results = store.search_memories(client, embedding, cfg.user_id, cfg.top_k)
    answer = llm.synthesize_answer(text, results, cfg)
    print(f"bot › {answer}")


def _dispatch(line: str, cfg: Config, client: Client) -> bool:
    """Handle one line of input. Returns False to exit the loop."""
    line = line.strip()
    if not line:
        return True

    # --- Natural language input: route automatically ---
    if not line.startswith("/"):
        try:
            intent = router.route(line, cfg)
            if intent == "store":
                _do_store(line, cfg, client)
            else:
                _do_query(line, cfg, client)
        except Exception as exc:
            print(f"Error: {exc}")
        return True

    # --- Slash commands ---
    parts = line.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/quit":
        print("Goodbye.")
        return False

    if cmd == "/help":
        print(_HELP)
        return True

    if cmd == "/add":
        if not arg:
            print("Usage: /add <text>")
            return True
        try:
            _do_store(arg, cfg, client)
        except Exception as exc:
            print(f"Error saving memory: {exc}")
        return True

    if cmd == "/ask":
        if not arg:
            print("Usage: /ask <question>")
            return True
        try:
            _do_query(arg, cfg, client)
        except Exception as exc:
            print(f"Error answering question: {exc}")
        return True

    if cmd == "/search":
        if not arg:
            print("Usage: /search <text>")
            return True
        try:
            embedding = embeddings.embed(arg, cfg, task_type="RETRIEVAL_QUERY")
            results = store.search_memories(client, embedding, cfg.user_id, cfg.top_k)
            if not results:
                print("No matching memories found.")
            else:
                for r in results:
                    date = r.created_at[:10]
                    print(f"[{r.similarity:.2f}] {date}  {r.content}")
        except Exception as exc:
            print(f"Error searching memories: {exc}")
        return True

    if cmd == "/list":
        try:
            memories = store.list_memories(client, cfg.user_id)
            if not memories:
                print("No memories stored yet.")
            else:
                for m in memories:
                    date = m.created_at[:10]
                    print(f"{m.id}  {date}  {m.content}")
        except Exception as exc:
            print(f"Error listing memories: {exc}")
        return True

    if cmd == "/count":
        try:
            n = store.count_memories(client, cfg.user_id)
            print(f"Memories stored: {n}")
        except Exception as exc:
            print(f"Error counting memories: {exc}")
        return True

    if cmd == "/forget":
        if not arg:
            print("Usage: /forget <id>")
            return True
        try:
            deleted = store.delete_memory(client, arg, cfg.user_id)
            print("Forgotten." if deleted else f"No memory found with id {arg!r}.")
        except Exception as exc:
            print(f"Error deleting memory: {exc}")
        return True

    print(f"Unknown command: {cmd}  (type /help for a list)")
    return True


def main() -> None:
    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"\nSetup required:\n{exc}")
        sys.exit(1)

    try:
        client = store.get_client(cfg)
        count = store.count_memories(client, cfg.user_id)
    except Exception as exc:
        print(f"Could not connect to Supabase: {exc}")
        sys.exit(1)

    print("Recall — your personal memory CLI")
    print(f"Memories stored: {count}")
    print("Type /help for commands or /quit to exit.\n")

    while True:
        try:
            line = input("you › ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not _dispatch(line, cfg, client):
            break
