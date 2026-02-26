"""Clipboard + paste automation for VoiceFlow Clone.

Step 5 goals:
- Copy rewritten text to clipboard.
- Wait briefly so Windows can register clipboard changes.
- Simulate Ctrl+V into the already-focused target app.
"""

from __future__ import annotations

import argparse
import time

import pyautogui
import pyperclip


class Paster:
    """Automates clipboard copy + Ctrl+V injection."""

    def __init__(self, paste_delay_seconds: float = 0.1) -> None:
        self.paste_delay_seconds = paste_delay_seconds
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True

    def paste_text(self, text: str) -> str:
        """Copy text to clipboard and paste into focused application.

        Flow:
            1) Receive text
            2) Copy to clipboard
            3) Wait 100ms
            4) Simulate Ctrl+V

        Returns:
            Clipboard text after copy (for verification).

        Raises:
            ValueError: If input text is empty.
            PermissionError: If keyboard injection is blocked by OS permissions.
        """
        payload = text.strip()
        if not payload:
            raise ValueError("Input text is empty.")

        pyperclip.copy(payload)
        time.sleep(self.paste_delay_seconds)

        try:
            pyautogui.hotkey("ctrl", "v")
        except Exception as exc:
            raise PermissionError(
                "Paste hotkey injection failed. On Windows, run terminal as Administrator "
                "if key events are not registering in target apps."
            ) from exc

        return pyperclip.paste()


def main() -> None:
    parser = argparse.ArgumentParser(description="Test clipboard + Ctrl+V automation")
    parser.add_argument(
        "--text",
        default="Hello from the Automation Agent!",
        help="Text to paste",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=5.0,
        help="Time to switch focus to target app before paste",
    )
    args = parser.parse_args()

    paster = Paster(paste_delay_seconds=0.1)

    print("[clipboard_paster] Focus your target app (Notepad/Slack/Word/etc.) now...")
    time.sleep(args.wait_seconds)

    try:
        clipboard_value = paster.paste_text(args.text)
        print(f"[clipboard_paster] Pasted text: {args.text}")
        print(f"[clipboard_paster] Clipboard now contains: {clipboard_value}")
    except ValueError as exc:
        print(f"[clipboard_paster] Input error: {exc}")
    except PermissionError as exc:
        print(f"[clipboard_paster] Permission error: {exc}")


if __name__ == "__main__":
    main()
