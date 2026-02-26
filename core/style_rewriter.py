"""Local LLM style rewriting via Ollama.

Step 4 goals:
- Rewrite raw ASR text into a relaxed but grammatically correct style.
- Keep latency predictable with an explicit timeout.
- Provide clear recovery guidance when Ollama is unavailable.
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import ollama

DEFAULT_SYSTEM_PROMPT = (
    "You are a writing assistant. Rewrite the following text to be relaxed, "
    "conversational, but grammatically perfect. Do not add explanations, only "
    "return the corrected text."
)


class StyleRewriter:
    """Thin wrapper over Ollama chat API for transcript polishing."""

    def __init__(
        self,
        model_name: str = "llama3.2:1b",
        timeout_seconds: float = 10.0,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> None:
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.system_prompt = system_prompt

    def rewrite(self, text: str) -> str:
        """Rewrite text using local Ollama model.

        Raises:
            ValueError: If text is empty.
            ConnectionError: If Ollama service is unavailable.
            TimeoutError: If response exceeds configured timeout.
        """
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Input text is empty.")

        def _request() -> str:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": cleaned},
                ],
                options={"temperature": 0.2},
            )
            return response["message"]["content"].strip()

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_request)
            try:
                return future.result(timeout=self.timeout_seconds)
            except FutureTimeoutError as exc:
                future.cancel()
                raise TimeoutError(
                    f"Ollama rewrite timed out after {self.timeout_seconds:.1f}s"
                ) from exc
            except ConnectionError:
                raise
            except Exception as exc:
                message = str(exc).lower()
                if "connection" in message or "refused" in message:
                    raise ConnectionError(
                        "Unable to connect to Ollama service. Is `ollama serve` running?"
                    ) from exc
                raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Test style rewriting with Ollama")
    parser.add_argument(
        "--text",
        default="hola, i want to go to the park... uhm, maybe tomorrow?",
        help="Text to rewrite",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    rewriter = StyleRewriter(timeout_seconds=args.timeout)
    print(f"[style_rewriter] Model: {rewriter.model_name}")
    print(f"[style_rewriter] Input: {args.text}")

    t0 = time.perf_counter()
    try:
        output = rewriter.rewrite(args.text)
        elapsed = time.perf_counter() - t0
        print(f"[style_rewriter] Output: {output}")
        print(f"[style_rewriter] Request->Response time: {elapsed:.2f}s")
    except ConnectionError as exc:
        print(f"[style_rewriter] Connection error: {exc}")
        print("[style_rewriter] Repair tip: start Ollama with `ollama serve` and retry.")
    except TimeoutError as exc:
        print(f"[style_rewriter] Timeout: {exc}")
        print("[style_rewriter] Repair tip: increase timeout or reduce model/system load.")


if __name__ == "__main__":
    main()
