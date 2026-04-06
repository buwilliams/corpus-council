from __future__ import annotations

import dataclasses
import uuid
from pathlib import Path

import typer
import uvicorn
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory

from corpus_council.core.collection import respond_collection, start_collection
from corpus_council.core.config import AppConfig, load_config
from corpus_council.core.conversation import run_conversation
from corpus_council.core.corpus import ingest_corpus
from corpus_council.core.embeddings import embed_corpus
from corpus_council.core.llm import LLMClient
from corpus_council.core.store import FileStore
from corpus_council.core.validation import validate_id

app = typer.Typer(name="corpus-council", no_args_is_help=True)

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


@app.command()
def chat(
    user_id: str = typer.Argument(..., help="User identifier"),
) -> None:
    """Start an interactive chat session."""
    try:
        validate_id(user_id, "user_id")
    except ValueError as exc:
        typer.echo(f"Invalid user_id: {exc}", err=True)
        raise typer.Exit(1) from exc

    config = _load_config_or_exit()
    store = FileStore(config.data_dir)
    llm = LLMClient(config)

    typer.echo(f"Welcome! Chatting as {user_id}. Type 'quit' or 'exit' to leave.")

    session: PromptSession[str] = PromptSession(history=InMemoryHistory())
    while True:
        try:
            message = session.prompt("> ")
        except KeyboardInterrupt:
            break
        except EOFError:
            break
        if message in ("quit", "exit"):
            break
        if not message:
            continue
        result = run_conversation(user_id, message, config, store, llm)
        typer.echo(f"> {result.response}")


@app.command()
def query(
    user_id: str = typer.Argument(..., help="User identifier"),
    message: str = typer.Argument(..., help="Message to send"),
) -> None:
    """Send a single message and print the response, then exit."""
    try:
        validate_id(user_id, "user_id")
    except ValueError as exc:
        typer.echo(f"Invalid user_id: {exc}", err=True)
        raise typer.Exit(1) from exc

    config = _load_config_or_exit()
    store = FileStore(config.data_dir)
    llm = LLMClient(config)
    result = run_conversation(user_id, message, config, store, llm)
    typer.echo(result.response)


@app.command()
def collect(
    user_id: str = typer.Argument(..., help="User identifier"),
    session: str | None = typer.Option(None, "--session", help="Existing session ID"),
    plan: str | None = typer.Option(
        None, "--plan", help="Plan ID (required when no session given)"
    ),
) -> None:
    """Run an interactive data-collection session."""
    try:
        validate_id(user_id, "user_id")
    except ValueError as exc:
        typer.echo(f"Invalid user_id: {exc}", err=True)
        raise typer.Exit(1) from exc

    if session is not None:
        try:
            validate_id(session, "session_id")
        except ValueError as exc:
            typer.echo(f"Invalid session_id: {exc}", err=True)
            raise typer.Exit(1) from exc

    if session is None and plan is None:
        typer.echo(
            "Error: --plan is required when --session is not provided.", err=True
        )
        raise typer.Exit(1)

    config = _load_config_or_exit()
    store = FileStore(config.data_dir)
    llm = LLMClient(config)

    collect_session: PromptSession[str] = PromptSession(history=InMemoryHistory())

    if session is None:
        session_id = str(uuid.uuid4())
        collection_session = start_collection(
            user_id=user_id,
            plan_id=plan,  # type: ignore[arg-type]
            session_id=session_id,
            config=config,
            store=store,
            llm=llm,
        )
    else:
        session_id = session
        try:
            first_response = collect_session.prompt("> ")
        except (KeyboardInterrupt, EOFError):
            return
        collection_session = respond_collection(
            user_id=user_id,
            session_id=session_id,
            message=first_response,
            config=config,
            store=store,
            llm=llm,
        )

    while collection_session.status != "complete":
        if collection_session.next_prompt:
            typer.echo(collection_session.next_prompt)
        try:
            response = collect_session.prompt("> ")
        except (KeyboardInterrupt, EOFError):
            break
        collection_session = respond_collection(
            user_id=user_id,
            session_id=session_id,
            message=response,
            config=config,
            store=store,
            llm=llm,
        )

    typer.echo("Collection complete.")


@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to the corpus directory to ingest"),
) -> None:
    """Ingest corpus files from the given path."""
    config = _load_config_or_exit()
    modified_config = dataclasses.replace(config, corpus_dir=Path(path))
    result = ingest_corpus(modified_config)
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
