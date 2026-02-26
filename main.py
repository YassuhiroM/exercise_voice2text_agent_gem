import os
from typing import Set
from pynput import keyboard
from core.orchestrator import VoiceFlowOrchestrator

class GlobalHotkeyController:
    def __init__(self, orchestrator: VoiceFlowOrchestrator) -> None:
        self.orchestrator = orchestrator
        self._pressed: Set[object] = set()
        self._combo_down = False

    @staticmethod
    def _normalize_key(key: object) -> object:
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r): return keyboard.Key.ctrl
        if key in (keyboard.Key.alt_l, keyboard.Key.alt_r): return keyboard.Key.alt
        return key

    def _combo_active(self) -> bool:
        return {keyboard.Key.ctrl, keyboard.Key.alt, keyboard.Key.space}.issubset(self._pressed)

    def on_press(self, key: object) -> None:
        # --- NEW: ESC TO EXIT ---
        if key == keyboard.Key.esc:
            print("\n🛑 ESC detected. Shutting down...")
            os._exit(0) # Forcefully kill the process

        normalized = self._normalize_key(key)
        self._pressed.add(normalized)

        if self._combo_active() and not self._combo_down:
            self._combo_down = True
            print("\n🎙️ Hotkey detected! Toggling recording...")
            self.orchestrator.toggle()

    def on_release(self, key: object) -> None:
        normalized = self._normalize_key(key)
        self._pressed.discard(normalized)
        if not self._combo_active():
            self._combo_down = False

def main() -> None:
    orchestrator = VoiceFlowOrchestrator()
    controller = GlobalHotkeyController(orchestrator)

    print("--- VoiceFlow Agent Active ---")
    print("1. Press CTRL+ALT+SPACE to Start/Stop.")
    print("2. Or stop talking for 10s to Auto-Stop.")
    print("3. Press ESC to close the app.")
    
    with keyboard.Listener(on_press=controller.on_press, on_release=controller.on_release) as listener:
        listener.join()

if __name__ == "__main__":
    main()
