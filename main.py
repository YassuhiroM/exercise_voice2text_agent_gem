"""Entry point for VoiceFlow Clone hotkey-driven pipeline.

Hotkey:
- CTRL+ALT+SPACE to toggle start/stop recording.
"""

from __future__ import annotations

from typing import Set

from pynput import keyboard

from core.orchestrator import VoiceFlowOrchestrator


class GlobalHotkeyController:
    """Non-blocking global hotkey handler for CTRL+ALT+SPACE."""

    def __init__(self, orchestrator: VoiceFlowOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._pressed: Set[object] = set()
        self._combo_down = False

    @staticmethod
    def _normalize_key(key: object) -> object:
        if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl
        if key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            return keyboard.Key.alt
        return key

    def _combo_active(self) -> bool:
        required = {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.space}
        return required.issubset(self._pressed)

    def on_press(self, key: object) -> None:
        normalized = self._normalize_key(key)
        self._pressed.add(normalized)

        if self._combo_active() and not self._combo_down:
            self._combo_down = True
            self.orchestrator.toggle()

    def on_release(self, key: object) -> None:
        normalized = self._normalize_key(key)
        self._pressed.discard(normalized)
        if not self._combo_active():
            self._combo_down = False


def main() -> None:
    orchestrator = VoiceFlowOrchestrator()
    controller = GlobalHotkeyController(orchestrator)

    print("VoiceFlow running. Press CTRL+ALT+SPACE to start/stop recording. Press CTRL+C to exit.")
    listener = keyboard.Listener(on_press=controller.on_press, on_release=controller.on_release)
    listener.start()
    listener.join()


if __name__ == "__main__":
    main()
