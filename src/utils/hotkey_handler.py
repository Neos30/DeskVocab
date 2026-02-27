from pynput import keyboard
import threading

class HotkeyHandler:
    """
    全局快捷键监听器
    """
    def __init__(self, toggle_callback):
        self.toggle_callback = toggle_callback
        self.listener = None

    def _on_press(self, key):
        # 示例：检测 Ctrl + Alt + S
        try:
            # 这里可以扩展更复杂的组合键逻辑
            pass
        except AttributeError:
            pass

    def _listen(self):
        # 使用 pynput 的 Global Hotkeys 功能
        with keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+s': self.toggle_callback
        }) as h:
            h.join()

    def start(self):
        """在后台线程启动监听"""
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()
        print("Hotkey listener started: Ctrl+Alt+S to toggle interaction.")
