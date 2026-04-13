from __future__ import annotations

import uuid
from pathlib import Path

import typer
import uvicorn
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from corpus_council.core.chat import run_goal_chat
from corpus_council.core.config import AppConfig, load_config
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
from corpus_council.core.goals import process_goals
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore
from corpus_council.core.validation import validate_id

app = typer.Typer(name="corpus-council", no_args_is_help=True)
goals_app = typer.Typer()
app.add_typer(goals_app, name="goals")

_CONFIG_PATH = Path("config.yaml")


def _load_config_or_exit() -> AppConfig:
    try:
        return load_config(_CONFIG_PATH)
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc
    except (KeyError, ValueError) as exc:
        typer.echo(f"Config error: {exc}", err=True)
        raise typer.Exit(1) from exc


@goals_app.command("process")
def goals_process() -> None:
    """Validate and register all goal files from the configured goals directory."""
    config = _load_config_or_exit()
    try:
        results = process_goals(
            config.goals_dir, config.personas_dir, config.goals_manifest_path
        )
        typer.echo(
            f"Processed {len(results)} goal(s)."
            f" Manifest written to {config.goals_manifest_path}"
        )
    except (ValueError, FileNotFoundError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


@app.command()
def chat(
    user_id: str = typer.Argument(..., help="User identifier"),
    goal: str | None = typer.Option(None, "--goal", help="Name of the goal to use"),
    session: str | None = typer.Option(
        None, "--session", help="Existing conversation ID to resume"
    ),
    mode: str | None = typer.Option(
        None, "--mode", help="Deliberation mode: parallel or consolidated"
    ),
) -> None:
    """Start an interactive chat session."""
    if goal is None:
        typer.echo(
            "Error: --goal is required for chat. Use --goal <goal_name>.", err=True
        )
        raise typer.Exit(1)

    try:
        validate_id(user_id, "user_id")
    except ValueError as exc:
        typer.echo(f"Invalid user_id: {exc}", err=True)
        raise typer.Exit(1) from exc

    if session is not None and ".." in session:
        typer.echo("Error: Invalid --session value.", err=True)
        raise typer.Exit(1)

    config = _load_config_or_exit()
    resolved_mode: str = mode or config.deliberation_mode
    if mode is not None and mode not in {"parallel", "consolidated"}:
        typer.echo(
            f"Error: --mode must be 'parallel' or 'consolidated', got {mode!r}",
            err=True,
        )
        raise typer.Exit(1)
    store = FileStore(config.users_dir)
    llm = LLMClient(config)

    conversation_id: str = session if session is not None else str(uuid.uuid4())

    typer.echo(
        f"Welcome! Chatting as {user_id} with goal '{goal}'."
        " Type 'quit' or 'exit' to leave."
    )

    prompt_session: PromptSession[str] = PromptSession(history=InMemoryHistory())
    while True:
        try:
            message = prompt_session.prompt("> ")
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        if message in ("quit", "exit"):
            break
        if not message:
            continue
        try:
            resp, conversation_id = run_goal_chat(
                goal_name=goal,
                user_id=user_id,
                conversation_id=conversation_id,
                message=message,
                config=config,
                store=store,
                llm=llm,
                mode=resolved_mode,
            )
            typer.echo(resp)
        except KeyError as exc:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1) from exc


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to the corpus directory to ingest"),
) -> None:
    """Ingest corpus files from the given path."""
    config = _load_config_or_exit()
    result = ingest_corpus(config, corpus_dir=Path(path))
    typer.echo(
        f"Processed {result.files_processed} files,"
        f" created {result.chunks_created} chunks."
    )


@app.command()
def embed() -> None:
    """Embed all corpus chunks into the vector store."""
    config = _load_config_or_exit()
    result = embed_corpus(config)
    typer.echo(f"Created {result.vectors_created} vectors.")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
) -> None:
    """Start the corpus-council API server."""
    uvicorn.run(
        "corpus_council.api.app:app",
        host=host,
        port=port,
        reload=False,
    )


__all__ = ["app"]

if __name__ == "__main__":
    app()
