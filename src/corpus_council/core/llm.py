from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import jinja2

from corpus_council.core.config import AppConfig

_TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class LLMClient:
    def __init__(self, config: AppConfig) -> None:
        self._config = config

    def render_template(self, template_name: str, context: dict[str, Any]) -> str:
        if not Path(template_name).suffix:
            template_name = template_name + ".md"
        template_path = _TEMPLATES_DIR / template_name
        if not template_path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=False,
        )
        template = env.get_template(template_name)
        return template.render(**context)

    def call(
        self,
        template_name: str,
        context: dict[str, Any],
        system_prompt: str | None = None,
    ) -> str:
        rendered_prompt = self.render_template(template_name, context)
        provider = self._config.llm_provider
        if provider == "anthropic":
            return self._call_anthropic(rendered_prompt, system_prompt=system_prompt)
        raise ValueError(f"Unknown LLM provider: {provider}")

    def _call_anthropic(
        self,
        rendered_prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        import anthropic as anthropic_sdk

        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY environment variable is not set")
        client = anthropic_sdk.Anthropic(api_key=key)
        if system_prompt is not None:
            response = client.messages.create(
                model=self._config.llm_model,
                max_tokens=2048,
                system=system_prompt,
                messages=[{"role": "user", "content": rendered_prompt}],
            )
        else:
            response = client.messages.create(
                model=self._config.llm_model,
                max_tokens=2048,
                messages=[{"role": "user", "content": rendered_prompt}],
            )
        block = response.content[0]
        if not isinstance(block, anthropic_sdk.types.TextBlock):
            raise RuntimeError(f"Unexpected response content block type: {type(block)}")
        return block.text


__all__ = ["LLMClient"]
