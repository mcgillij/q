from __future__ import annotations

import sys
from typing import NoReturn

import click
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.status import Status
from rich.table import Table

from q import config as cmod
from q.client import APIError, Client

console = Console()


def _build_client(cfg: dict) -> Client:
    return Client(
        base_url=cfg["server"]["base_url"],
        api_key=cfg["server"].get("api_key", ""),
    )


def _get_model(cfg: dict, model_flag: str | None) -> str | None:
    if model_flag:
        return model_flag
    return cfg["server"].get("model") or None


def _list_models(cfg: dict) -> None:
    client = _build_client(cfg)
    try:
        models = client.list_models()
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not models:
        console.print("[yellow]No models reported by the endpoint.[/yellow]")
        return

    table = Table(title="Available Models", title_style="bold cyan")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("ID")

    for i, m in enumerate(models, 1):
        table.add_row(str(i), m["id"])
    console.print(table)


def _set_model(cfg: dict) -> None:
    client = _build_client(cfg)
    try:
        models = client.list_models()
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)

    if not models:
        console.print("[yellow]No models available from the endpoint.[/yellow]")
        raise SystemExit(1)

    table = Table(title="Available Models", title_style="bold cyan")
    table.add_column("#", style="dim", no_wrap=True)
    table.add_column("ID")
    for i, m in enumerate(models, 1):
        table.add_row(str(i), m["id"])
    console.print(table)

    choices = [str(i) for i in range(1, len(models) + 1)] + [m["id"] for m in models]
    default_hint = cfg["server"].get("model") or ""
    answer = Prompt.ask(
        "Select model",
        choices=choices,
        default=default_hint or None,
        show_choices=False,
    )
    if not answer:
        console.print("[yellow]No model selected.[/yellow]")
        raise SystemExit(1)

    if answer.isdigit() and 1 <= int(answer) <= len(models):
        selected = models[int(answer) - 1]["id"]
    else:
        selected = answer

    cfg["server"]["model"] = selected
    cmod.save(cfg)
    console.print(f"[green]Default model set to:[/green] {selected}")


def _send_query(cfg: dict, model: str, query_text: str) -> None:
    client = _build_client(cfg)
    messages = [
        {"role": "system", "content": cfg["prompt"]["system"]},
        {"role": "user", "content": query_text},
    ]

    buffer = ""
    live = None
    spinning = True
    status = Status("Thinking...", console=console, spinner="dots")
    status.start()

    try:
        for token in client.stream_chat(model, messages):
            if live is None:
                status.stop()
                spinning = False
                live = Live(Markdown(""), console=console, refresh_per_second=15)
                live.start()
            buffer += token
            live.update(Markdown(buffer))

        if live is not None:
            live.stop()
        else:
            status.stop()
        print()
    except APIError as e:
        if live is not None:
            live.stop()
        elif spinning:
            status.stop()
        console.print(f"\n[red]Error:[/red] {e}")
        raise SystemExit(1)
    except KeyboardInterrupt:
        if live is not None:
            live.stop()
        elif spinning:
            status.stop()
        print()
        console.print("[yellow]Interrupted.[/yellow]")
        raise SystemExit(130)


@click.command(context_settings={"ignore_unknown_options": False})
@click.argument("query", nargs=-1, required=False)
@click.option("--model", "-m", help="Model to use (overrides config)")
@click.option("--list-models", is_flag=True, help="List available models and exit")
@click.option("--set-model", is_flag=True, help="Interactively set the default model")
@click.option("--config", type=click.Path(), help="Path to config file")
def main(
    query: tuple[str, ...],
    model: str | None,
    list_models: bool,
    set_model: bool,
    config: str | None,
) -> None:
    cfg = cmod.load(config)

    if list_models:
        _list_models(cfg)
        return

    if set_model:
        _set_model(cfg)
        return

    if not query:
        click.echo(main.get_help(click.Context(main)))
        return

    model_name = _get_model(cfg, model)
    if not model_name:
        console.print(
            "[yellow]No model configured.[/yellow] "
            "Use [bold]--set-model[/bold] to pick one, "
            "or [bold]--model <name>[/bold] to specify one."
        )
        raise SystemExit(1)

    query_text = " ".join(query)
    _send_query(cfg, model_name, query_text)


if __name__ == "__main__":
    main()
