from __future__ import annotations

import typer
import uvicorn

app = typer.Typer(no_args_is_help=True)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
) -> None:
    uvicorn.run(
        "corpus_council.api.app:app",
        host=host,
        port=port,
        reload=False,
    )


@app.command()
def version() -> None:
    """Print the corpus-council version."""
    typer.echo("corpus-council 0.1.0")


__all__ = ["app"]
