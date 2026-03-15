"""Entry point: global push-to-talk (Ctrl+Alt+Space) + ESC to exit (Windows)."""

import threading
from pynput import keyboard

from core.orchestrator import VoiceFlowOrchestrator

# If run_agent.bat already prints instructions, set this to False
SHOW_STARTUP_HELP = True
HOTKEY_LABEL = "CTRL + ALT + SPACE"

STARTUP_HELP = f"""\
Voice2Text Agent
Converts your voice into friendly, polished text and pastes it automatically.

Quick use:
1) Hold {HOTKEY_LABEL} to record (push-to-talk)
2) Release to stop and process
3) Paste happens automatically (Ctrl+V is sent for you)

Exit:
- Press ESC to quit
"""


class GlobalHotkeyController:
    """
    Push-to-talk semantics:
      - On first detection of Ctrl+Alt+Space being held -> start (toggle)
      - When any of Ctrl/Alt/Space is released while active -> stop/process (toggle)
    """

    def __init__(self, orchestrator: VoiceFlowOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._pressed = set()
        self._combo_down = False
        self._lock = threading.Lock()

    def _combo_pressed(self) -> bool:
        ctrl = (keyboard.Key.ctrl_l in self._pressed) or (keyboard.Key.ctrl_r in self._pressed)
        alt = (keyboard.Key.alt_l in self._pressed) or (keyboard.Key.alt_r in self._pressed)
        space = keyboard.Key.space in self._pressed
        return ctrl and alt and space

    def _start_async_toggle(self):
        # Avoid long work in the pynput callback thread
        threading.Thread(target=self.orchestrator.toggle, daemon=True).start()

    def on_press(self, key):
        # ESC to exit cleanly
        if key == keyboard.Key.esc:
            print("\n[EXIT] Closing Voice2Text Agent...")
            return False  # Stops listener (pynput convention)

        with self._lock:
            self._pressed.add(key)

            # Push-to-talk START: combo becomes true for the first time
            if self._combo_pressed() and not self._combo_down:
                self._combo_down = True
                self._start_async_toggle()

    def on_release(self, key):
        with self._lock:
            # Remove key first
            self._pressed.discard(key)

            # Push-to-talk STOP: if we were active and any combo key is released
            if self._combo_down and key in (
                keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
                keyboard.Key.alt_l, keyboard.Key.alt_r,
                keyboard.Key.space,
            ):
                self._combo_down = False
                self._start_async_toggle()


def main():
    if SHOW_STARTUP_HELP:
        print(STARTUP_HELP)

    orchestrator = VoiceFlowOrchestrator()
    controller = GlobalHotkeyController(orchestrator)

    # Keep this minimal to avoid conflicting instructions from the .bat
    print("Voice2Text Agent running (ESC to exit).")

    with keyboard.Listener(on_press=controller.on_press, on_release=controller.on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
