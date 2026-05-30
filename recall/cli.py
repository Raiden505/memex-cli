import sys

from supabase import Client
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from recall.config import Config, ConfigError, load_config
from recall import embeddings, llm, router, store

console = Console()


def _show_help() -> None:
    help_text = """[bold]/add <text>[/bold]     Force-store text as a memory
[bold]/ask <text>[/bold]     Force-treat text as a question
[bold]/search <text>[/bold]  Show raw matching memories (no AI answer)
[bold]/list[/bold]           Show all stored memories with their ids
[bold]/forget <id>[/bold]    Delete a memory by id
[bold]/count[/bold]          How many memories are stored
[bold]/help[/bold]           Show this help
[bold]/quit[/bold]           Exit

[dim]Or just type naturally — statements are stored, questions are answered automatically.[/dim]"""
    console.print(Panel(help_text, title="Commands", border_style="cyan"))


def _do_store(text: str, cfg: Config, client: Client) -> None:
    with console.status("[cyan]Saving...[/cyan]"):
        embedding = embeddings.embed(text, cfg, task_type="RETRIEVAL_DOCUMENT")
        mem_id = store.add_memory(client, text, embedding, cfg.user_id)
    console.print(f"[green]Saved.[/green] [dim](id: {mem_id})[/dim]")


def _do_query(text: str, cfg: Config, client: Client) -> None:
    with console.status("[cyan]Thinking...[/cyan]"):
        embedding = embeddings.embed(text, cfg, task_type="RETRIEVAL_QUERY")
        results = store.search_memories(client, embedding, cfg.user_id, cfg.top_k)
        answer = llm.synthesize_answer(text, results, cfg)
    console.print(f"[bold]bot ›[/bold] {answer}")


def _dispatch(line: str, cfg: Config, client: Client) -> bool:
    line = line.strip()
    if not line:
        return True

    if not line.startswith("/"):
        try:
            intent = router.route(line, cfg)
            if intent == "store":
                _do_store(line, cfg, client)
            else:
                _do_query(line, cfg, client)
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")
        return True

    parts = line.split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/quit":
        console.print("[dim]Goodbye.[/dim]")
        return False

    if cmd == "/help":
        _show_help()
        return True

    if cmd == "/add":
        if not arg:
            console.print("[dim]Usage: /add <text>[/dim]")
            return True
        try:
            _do_store(arg, cfg, client)
        except Exception as exc:
            console.print(f"[red]Error saving memory:[/red] {exc}")
        return True

    if cmd == "/ask":
        if not arg:
            console.print("[dim]Usage: /ask <question>[/dim]")
            return True
        try:
            _do_query(arg, cfg, client)
        except Exception as exc:
            console.print(f"[red]Error answering question:[/red] {exc}")
        return True

    if cmd == "/search":
        if not arg:
            console.print("[dim]Usage: /search <text>[/dim]")
            return True
        try:
            with console.status("[cyan]Searching...[/cyan]"):
                embedding = embeddings.embed(arg, cfg, task_type="RETRIEVAL_QUERY")
                results = store.search_memories(client, embedding, cfg.user_id, cfg.top_k)
            if not results:
                console.print("[dim]No matching memories found.[/dim]")
            else:
                table = Table(box=box.ROUNDED)
                table.add_column("Score", style="cyan", justify="right")
                table.add_column("Date", style="cyan")
                table.add_column("Content")
                for r in results:
                    table.add_row(f"{r.similarity:.2f}", r.created_at[:10], r.content)
                console.print(table)
        except Exception as exc:
            console.print(f"[red]Error searching memories:[/red] {exc}")
        return True

    if cmd == "/list":
        try:
            memories = store.list_memories(client, cfg.user_id)
            if not memories:
                console.print("[dim]No memories stored yet.[/dim]")
            else:
                table = Table(box=box.ROUNDED)
                table.add_column("ID", style="dim", no_wrap=True)
                table.add_column("Date", style="cyan")
                table.add_column("Content")
                for m in memories:
                    table.add_row(m.id, m.created_at[:10], m.content)
                console.print(table)
        except Exception as exc:
            console.print(f"[red]Error listing memories:[/red] {exc}")
        return True

    if cmd == "/count":
        try:
            n = store.count_memories(client, cfg.user_id)
            console.print(f"Memories stored: [bold cyan]{n}[/bold cyan]")
        except Exception as exc:
            console.print(f"[red]Error counting memories:[/red] {exc}")
        return True

    if cmd == "/forget":
        if not arg:
            console.print("[dim]Usage: /forget <id>[/dim]")
            return True
        try:
            deleted = store.delete_memory(client, arg, cfg.user_id)
            if deleted:
                console.print("[green]Forgotten.[/green]")
            else:
                console.print(f"[dim]No memory found with id [bold]{arg}[/bold].[/dim]")
        except Exception as exc:
            console.print(f"[red]Error deleting memory:[/red] {exc}")
        return True

    console.print(f"[dim]Unknown command: {cmd}  (type /help for a list)[/dim]")
    return True


def main() -> None:
    try:
        cfg = load_config()
    except ConfigError as exc:
        console.print(f"\n[bold red]Setup required[/bold red]")
        console.print(f"[dim]{exc}[/dim]")
        sys.exit(1)

    try:
        client = store.get_client(cfg)
        count = store.count_memories(client, cfg.user_id)
    except Exception as exc:
        console.print(f"\n[red]Could not connect to Supabase.[/red]")
        console.print(f"[dim]{exc}[/dim]")
        sys.exit(1)

    console.print(Panel.fit(
        "[bold cyan]Recall[/bold cyan] — your personal memory CLI",
        border_style="cyan",
    ))
    console.print(f"[dim]Memories stored: {count}[/dim]")
    console.print("[dim]Type [bold]/help[/bold] for commands or [bold]/quit[/bold] to exit.[/dim]\n")

    while True:
        try:
            line = input("you \u203a ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Goodbye.[/dim]")
            break

        if not _dispatch(line, cfg, client):
            break
