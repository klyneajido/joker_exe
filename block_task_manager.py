import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import win32gui
import win32con
import win32api
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Windows API setup
user32 = ctypes.WinDLL("user32", use_last_error=True)

# Define Windows API function prototypes
SetWindowsHookExW = user32.SetWindowsHookExW
SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, wintypes.HINSTANCE, wintypes.DWORD]
SetWindowsHookExW.restype = wintypes.HHOOK

UnhookWindowsHookEx = user32.UnhookWindowsHookEx
UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
UnhookWindowsHookEx.restype = wintypes.BOOL

CallNextHookEx = user32.CallNextHookEx
CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
CallNextHookEx.restype = ctypes.c_long

GetMessageW = user32.GetMessageW
GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
GetMessageW.restype = wintypes.BOOL

TranslateMessage = user32.TranslateMessage
TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
TranslateMessage.restype = wintypes.BOOL

DispatchMessageW = user32.DispatchMessageW
DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
DispatchMessageW.restype = None

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

keybd_event = user32.keybd_event
keybd_event.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong]
keybd_event.restype = None

# Keyboard hook callback type
HOOKPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

class TaskManagerBlocker:
    def __init__(self):
        self.hook = None
        self.running = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.shift_pressed = False
        self.win_pressed = False

    def low_level_keyboard_hook(self, n_code, w_param, l_param):
        """Keyboard hook callback to block Task Manager shortcuts and handle exit shortcut."""
        if n_code >= 0:
            kbd_struct = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            key = kbd_struct.vkCode
            is_key_down = w_param == win32con.WM_KEYDOWN or w_param == win32con.WM_SYSKEYDOWN

            # Track modifier keys
            if key in (win32con.VK_LCONTROL, win32con.VK_RCONTROL):
                self.ctrl_pressed = is_key_down
            elif key in (win32con.VK_LMENU, win32con.VK_RMENU):  # Alt key
                self.alt_pressed = is_key_down
            elif key in (win32con.VK_LSHIFT, win32con.VK_RSHIFT):
                self.shift_pressed = is_key_down
            elif key in (win32con.VK_LWIN, win32con.VK_RWIN):
                self.win_pressed = is_key_down

            # Exit program on Ctrl+O
            if self.ctrl_pressed and key == ord('O') and is_key_down:
                logger.info("Exit shortcut (Ctrl+O) detected, stopping blocker...")
                self.running = False
                user32.PostMessageW(0, win32con.WM_QUIT, 0, 0)
                return 1  # Block the key

            # Block Ctrl+Shift+Esc
            if self.ctrl_pressed and self.shift_pressed and key == win32con.VK_ESCAPE and is_key_down:
                logger.info("Blocked Ctrl+Shift+Esc")
                return 1  # Block the key

            # Block Ctrl+Alt+Del Task Manager
            if self.ctrl_pressed and self.alt_pressed and key == win32con.VK_DELETE and is_key_down:
                logger.info("Blocked Ctrl+Alt+Del (Task Manager)")
                return 1  # Block the key

            # Block Win+X (Power User Menu, which can launch Task Manager)
            if self.win_pressed and key == ord('X') and is_key_down:
                logger.info("Blocked Win+X")
                return 1  # Block the key

        return CallNextHookEx(self.hook, n_code, w_param, l_param)

    def install_hook(self):
        """Install the low-level keyboard hook."""
        hook_proc = HOOKPROC(self.low_level_keyboard_hook)
        self.hook = SetWindowsHookExW(
            win32con.WH_KEYBOARD_LL,
            hook_proc,
            None,  # Current process
            0  # All threads
        )
        if not self.hook:
            logger.error(f"Failed to install keyboard hook: {ctypes.get_last_error()}")
            return False
        logger.info("Keyboard hook installed")
        self._hook_proc = hook_proc  # Keep hook procedure alive
        return True

    def uninstall_hook(self):
        """Uninstall the keyboard hook."""
        if self.hook:
            UnhookWindowsHookEx(self.hook)
            self.hook = None
            logger.info("Keyboard hook uninstalled")

    def simulate_alt_f4(self, hwnd):
        """Simulate Alt+F4 to close a window."""
        try:
            # Ensure the window is in focus
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.1)  # Small delay to ensure focus
            # Press Alt
            keybd_event(win32con.VK_MENU, 0, 0, 0)
            time.sleep(0.01)
            # Press F4
            keybd_event(win32con.VK_F4, 0, 0, 0)
            time.sleep(0.01)
            # Release F4
            keybd_event(win32con.VK_F4, 0, win32con.KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
            # Release Alt
            keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            logger.info(f"Simulated Alt+F4 on window {hwnd}")
        except Exception as e:
            logger.error(f"Failed to simulate Alt+F4: {e}")

    def poll_task_manager(self):
        """Poll for Task Manager windows and processes, close them via Alt+F4."""
        while self.running:
            try:
                # Check for Task Manager windows
                for window_class in ["#32770", "TaskManagerWindow", "ApplicationFrameWindow"]:
                    for window_title in ["Task Manager", "Windows Task Manager", "Taskmgr"]:
                        hwnd = FindWindowW(window_class, window_title)
                        if hwnd:
                            logger.info(f"Task Manager window detected ({window_class}/{window_title})")
                            self.simulate_alt_f4(hwnd)

                # Enumerate windows for additional detection
                def enum_windows_callback(hwnd, _):
                    if win32gui.IsWindowVisible(hwnd):
                        window_text = win32gui.GetWindowText(hwnd).lower()
                        if "task manager" in window_text:
                            logger.info(f"Found Task Manager window via enumeration: '{window_text}'")
                            self.simulate_alt_f4(hwnd)
                    return True

                win32gui.EnumWindows(enum_windows_callback, None)

                # Check for alternative tools (Process Explorer, etc.)
                for alt_title in ["Process Explorer", "Process Hacker", "System Explorer"]:
                    hwnd = FindWindowW(None, alt_title)
                    if hwnd:
                        logger.info(f"{alt_title} detected")
                        self.simulate_alt_f4(hwnd)

                # Check for taskmgr.exe process
                for proc in psutil.process_iter(['name']):
                    if proc.info['name'].lower() == 'taskmgr.exe':
                        logger.info("Task Manager process detected")
                        # Find associated window and close
                        hwnd = FindWindowW("TaskManagerWindow", None) or FindWindowW("#32770", "Task Manager")
                        if hwnd:
                            self.simulate_alt_f4(hwnd)

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

            time.sleep(0.2)  # Poll every 200ms

    def run(self):
        """Start the blocker."""
        if not self.install_hook():
            return

        self.running = True
        # Start polling thread
        polling_thread = threading.Thread(target=self.poll_task_manager, daemon=True)
        polling_thread.start()

        # Message loop for hook processing
        msg = wintypes.MSG()
        while self.running:
            if GetMessageW(ctypes.byref(msg), 0, 0, 0):
                TranslateMessage(ctypes.byref(msg))
                DispatchMessageW(ctypes.byref(msg))

    def stop(self):
        """Stop the blocker."""
        self.running = False
        self.uninstall_hook()
        logger.info("Task Manager blocker stopped")

# Define KBDLLHOOKSTRUCT for keyboard hook
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulong),
    ]

def main():
    blocker = TaskManagerBlocker()
    try:
        blocker.run()
    except KeyboardInterrupt:
        blocker.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        blocker.stop()

if __name__ == "__main__":
    main()