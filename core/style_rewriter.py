import ollama
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

DEFAULT_SYSTEM_PROMPT = (
    "You are a strict minimalist proofreader. "
    "Your ONLY task is to correct grammatical errors, spelling mistakes, and "
    "linguistic inconsistencies. "
    "STRICT RULES:\n"
    "1. Keep the original wording and structure as much as possible.\n"
    "2. Do NOT change the style, tone, or vocabulary unless it is incorrect.\n"
    "3. Do NOT answer questions or provide conversational responses.\n"
    "4. Output ONLY the corrected text, with no explanations or filler."
<<<<<<< Updated upstream
    #"5. Consider only these languages: English, Spanish, Portuguese."
=======
>>>>>>> Stashed changes
)

class StyleRewriter:
    def __init__(self, model_name="llama3.2:1b", timeout_seconds=10.0):
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def rewrite(self, text):
        """This is the method the Orchestrator is looking for."""
        def _request():
            response = ollama.generate(
                model=self.model_name,
                system=DEFAULT_SYSTEM_PROMPT,
                prompt=f"Polish this text: {text}"
            )
            return response['response'].strip()

        # Execute with a timeout to prevent the app from freezing
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_request)
            try:
                return future.result(timeout=self.timeout_seconds)
            except FutureTimeoutError:
                return f"[Timeout] Ollama is taking too long. Raw text: {text}"
            except Exception as e:
                return f"[Error] Style rewriter failed: {str(e)}"

def rewrite_text(text):
    """Fallback function for simple calls."""
    rewriter = StyleRewriter()
    return rewriter.rewrite(text)

if __name__ == "__main__":
    main()
