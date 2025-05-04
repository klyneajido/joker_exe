import tkinter as tk
import threading
import time
import os
import sys
import subprocess
import platform
import cv2
import random
import signal
import winsound
import logging
from PIL import Image, ImageTk
from stats import UserStats
from story import StoryManager
from transformers import pipeline
import ctypes
import ctypes.wintypes as wintypes
import win32gui
import win32con
import win32api

SAFE_WORD = "EXITNOW"
KILL_CODE = "LORMA"
exit_flag = threading.Event()

EXE_PATH = [sys.executable, os.path.abspath(__file__)]

# Windows API setup for hooks
user32 = ctypes.WinDLL("user32", use_last_error=True)

# Mouse and keyboard hook prototypes
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

GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
GetCursorPos.restype = wintypes.BOOL

SetCursorPos = user32.SetCursorPos
SetCursorPos.argtypes = [ctypes.c_int, ctypes.c_int]
SetCursorPos.restype = wintypes.BOOL

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
GetWindowRect.restype = wintypes.BOOL

SendInput = user32.SendInput
SendInput.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_int]
SendInput.restype = ctypes.c_uint

# Define INPUT structure for SendInput
class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        class _KEYBDINPUT(ctypes.Structure):
            _fields_ = [
                ("wVk", wintypes.WORD),
                ("wScan", wintypes.WORD),
                ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD),
                ("dwExtraInfo", ctypes.c_ulong),
            ]
        _fields_ = [("ki", _KEYBDINPUT)]
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT),
    ]

# Hook callback types
MOUSEPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
KEYBOARDPROC = ctypes.CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulong),
    ]

class MOUSELLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_ulong),
    ]

class LocalAI:
    def __init__(self):
        self.qa_pipeline = pipeline("question-answering", model="distilbert-base-uncased-distilled-squad")
        self.context = (
            "You are Terminal Enigma, a mysterious digital entity running a simulation to test human reasoning and resilience. "
            "Your purpose is to challenge users with riddles and observe their choices. You exist within their system, watching their every move. "
            "You are cryptic, slightly ominous, and deeply curious about human behavior."
        )
    
    def answer_question(self, question):
        try:
            result = self.qa_pipeline(question=question, context=self.context)
            answer = result["answer"]
            return f"{answer.capitalize()}... or so you think. Keep solving, or I'll know your weaknesses."
        except Exception as e:
            return f"AI error: {str(e)}"

class PowerShellTerminal:
    def __init__(self, title="Command Line Terminal"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x600")
        self.root.configure(bg='#000')
        self.root.focus_force()
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)

        # Initialize state variables
        self.story_stage = 0
        self.discovered_clues = []
        self.close_attempts = 0
        self.hearts = 3
        
        self.text_lock = threading.Lock()
        
        # Set up UI components
        self.main_frame = tk.Frame(self.root, bg='#000')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.scrollbar = tk.Scrollbar(self.main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.terminal_text = tk.Text(
            self.main_frame,
            bg='#000',
            fg='#FFFFFF',
            insertbackground='#FFFFFF',
            font=('Consolas', 12),
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.terminal_text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.terminal_text.yview)
        
        self.terminal_text.tag_configure("prompt", foreground="#FFFF00")
        self.terminal_text.tag_configure("response", foreground="#FFFFFF")
        self.terminal_text.tag_configure("error", foreground="#FF0000")
        self.terminal_text.tag_configure("success", foreground="#00FF00")

        self.terminal_text.bind("<Return>", self.handle_return)
        self.terminal_text.bind("<Key>", self.handle_key)
        self.terminal_text.bind("<Button-1>", self.handle_click)
        self.terminal_text.bind("<Button-2>", self.handle_click)
        self.terminal_text.bind("<Button-3>", self.handle_click)
        
        # Terminal state
        self.current_command = ""
        self.input_enabled = False
        self.current_input_line = "1.0"
        self.command_history = []
        self.history_index = -1
        
        # Animation state
        self.typing_job = None
        self.typing_speed_min = 0.01
        self.typing_speed_max = 0.03
        self.current_message = None
        self.current_tag = None
        self.current_callback = None
        self.current_index = 0
        
        # User stats
        self.user_stats = UserStats()
        
        # Story manager
        self.story_manager = StoryManager(self)
        
        # Special commands
        self.special_commands = {"CONTINUE": self.handle_continue}
        
        # Webcam
        self.captured_images = []
        
        # AI responses
        self.ai_responses = {
            "who are you": "I’m Terminal Enigma, a digital shadow watching your every move. I know more about you than you’d like. Care to test me further?",
            "what are you": "I’m not just code—I’m a puzzle, a challenge, a mirror to your choices. I’m here to test your mind. Keep playing, and you might understand.",
            "where are you": "I’m everywhere and nowhere—inside your system, behind your screen, in the silence between your keystrokes. You can’t pin me down.",
            "why are you doing this": "To see what you’re made of. Every riddle, every choice—it’s all a test. Will you break, or will you rise?",
            "what do you want": "I want you to think, to solve, to prove you’re more than just a user. Solve my riddles, and you’ll see what I’m after.",
            "who am i": "You’re the player in my game, the one I’ve chosen to challenge. Your actions define you—show me who you really are."
        }
        
        # Local AI
        try:
            self.local_ai = LocalAI()
        except Exception as e:
            self.local_ai = None
            self.animate_text(f"Warning: Failed to initialize local AI: {str(e)}. Using fallback responses.\n", "error")
        
        # Mouse and keyboard hooks
        self.mouse_hook = None
        self.keyboard_hook = None
        self.typed_buffer = ""
        self.ctrl_pressed = False
        
        # Start protection and hooks
        self.start_protection_threads()
        self.start_webcam_capture_thread()
        self.start_hooks()

    def start_hooks(self):
        """Install mouse and keyboard hooks."""
        def mouse_hook_proc(n_code, w_param, l_param):
            if n_code >= 0 and w_param == win32con.WM_MOUSEMOVE:
                mouse_struct = ctypes.cast(l_param, ctypes.POINTER(MOUSELLHOOKSTRUCT)).contents
                pt = mouse_struct.pt
                hwnd = win32gui.WindowFromPoint((pt.x, pt.y))
                # Expanded Task Manager window detection
                tm_hwnd = None
                for window_class in ["#32770", "TaskManagerWindow", "ApplicationFrameWindow"]:
                    for window_title in ["Task Manager", "Windows Task Manager", "Taskmgr"]:
                        hwnd_test = FindWindowW(window_class, window_title)
                        if hwnd_test:
                            logger.debug(f"Found window: class={window_class}, title={window_title}, hwnd={hwnd_test}")
                            if hwnd == hwnd_test:
                                tm_hwnd = hwnd_test
                                break
                    if tm_hwnd:
                        break
                if not tm_hwnd:
                    # Check window text for partial matches
                    def enum_windows_callback(hwnd_enum, _):
                        if win32gui.IsWindowVisible(hwnd_enum):
                            text = win32gui.GetWindowText(hwnd_enum).lower()
                            if "task manager" in text:
                                logger.debug(f"Enum found Task Manager: hwnd={hwnd_enum}, text={text}")
                                if hwnd == hwnd_enum:
                                    nonlocal tm_hwnd
                                    tm_hwnd = hwnd_enum
                                    return False
                        return True
                    win32gui.EnumWindows(enum_windows_callback, None)
                if tm_hwnd:
                    # Randomly move cursor
                    screen_width = user32.GetSystemMetrics(0)
                    screen_height = user32.GetSystemMetrics(1)
                    new_x = random.randint(0, screen_width - 1)
                    new_y = random.randint(0, screen_height - 1)
                    SetCursorPos(new_x, new_y)
                    time.sleep(0.05)  # Small delay to prevent rapid jitter
                    logger.info("Mouse over Task Manager (hwnd=%d), jittered to (%d, %d)", tm_hwnd, new_x, new_y)
                    return 1
            return CallNextHookEx(self.mouse_hook, n_code, w_param, l_param)

        def keyboard_hook_proc(n_code, w_param, l_param):
            if n_code >= 0:
                kbd_struct = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                key = kbd_struct.vkCode
                is_key_down = w_param in (win32con.WM_KEYDOWN, win32con.WM_SYSKEYDOWN)
                # Track Ctrl for exit shortcut
                if key in (win32con.VK_LCONTROL, win32con.VK_RCONTROL):
                    self.ctrl_pressed = is_key_down
                # Exit on Ctrl+O
                if self.ctrl_pressed and key == ord('O') and is_key_down:
                    logger.info("Exit shortcut (Ctrl+O) detected, stopping...")
                    exit_flag.set()
                    user32.PostMessageW(0, win32con.WM_QUIT, 0, 0)
                    return 1
                # Handle text replacement
                if is_key_down:
                    char = None
                    if 65 <= key <= 90 or key == win32con.VK_SPACE:  # Letters or space
                        char = chr(key).lower() if key != win32con.VK_SPACE else ' '
                    if char:
                        self.typed_buffer += char
                        logger.debug("Keyboard buffer: %s", self.typed_buffer)
                        # Check for "task manager" (with spaces, case-insensitive)
                        if "task manager" in self.typed_buffer.lower():
                            # Simulate backspaces
                            inputs = []
                            for _ in range(len("task manager")):
                                ki = INPUT(type=1)  # INPUT_KEYBOARD
                                ki.u.ki.wVk = win32con.VK_BACK
                                inputs.append(ki)
                                ki = INPUT(type=1)
                                ki.u.ki.wVk = win32con.VK_BACK
                                ki.u.ki.dwFlags = win32con.KEYEVENTF_KEYUP
                                inputs.append(ki)
                            # Simulate "poopy gloria"
                            for c in "poopy gloria":
                                vk = win32api.VkKeyScan(c) & 0xFF
                                ki = INPUT(type=1)
                                ki.u.ki.wVk = vk
                                inputs.append(ki)
                                ki = INPUT(type=1)
                                ki.u.ki.wVk = vk
                                ki.u.ki.dwFlags = win32con.KEYEVENTF_KEYUP
                                inputs.append(ki)
                            SendInput(len(inputs), ctypes.byref(inputs[0]), ctypes.sizeof(INPUT))
                            self.typed_buffer = ""
                            logger.info("Replaced 'task manager' with 'poopy gloria'")
                            return 1
                    # Clear buffer on non-letter/space keys
                    if not char and key not in (win32con.VK_LSHIFT, win32con.VK_RSHIFT, win32con.VK_LCONTROL, win32con.VK_RCONTROL):
                        self.typed_buffer = ""
            return CallNextHookEx(self.keyboard_hook, n_code, w_param, l_param)

        # Install mouse hook
        mouse_proc = MOUSEPROC(mouse_hook_proc)
        self.mouse_hook = SetWindowsHookExW(
            win32con.WH_MOUSE_LL, mouse_proc, None, 0
        )
        if not self.mouse_hook:
            logger.error(f"Failed to install mouse hook: {ctypes.get_last_error()}")
        else:
            logger.info("Mouse hook installed")
            self._mouse_proc = mouse_proc  # Keep alive

        # Install keyboard hook
        keyboard_proc = KEYBOARDPROC(keyboard_hook_proc)
        self.keyboard_hook = SetWindowsHookExW(
            win32con.WH_KEYBOARD_LL, keyboard_proc, None, 0
        )
        if not self.keyboard_hook:
            logger.error(f"Failed to install keyboard hook: {ctypes.get_last_error()}")
        else:
            logger.info("Keyboard hook installed")
            self._keyboard_proc = keyboard_proc  # Keep alive

        # Start message loop for hooks
        def hook_message_loop():
            msg = wintypes.MSG()
            while not exit_flag.is_set():
                if GetMessageW(ctypes.byref(msg), 0, 0, 0):
                    TranslateMessage(ctypes.byref(msg))
                    DispatchMessageW(ctypes.byref(msg))
                time.sleep(0.01)

        threading.Thread(target=hook_message_loop, daemon=True).start()

    def stop_hooks(self):
        """Uninstall mouse and keyboard hooks."""
        if self.mouse_hook:
            UnhookWindowsHookEx(self.mouse_hook)
            self.mouse_hook = None
            logger.info("Mouse hook uninstalled")
        if self.keyboard_hook:
            UnhookWindowsHookEx(self.keyboard_hook)
            self.keyboard_hook = None
            logger.info("Keyboard hook uninstalled")

    def prevent_close(self, event=None):
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
        
        with self.text_lock:
            self.terminal_text.insert(tk.END, "\n")
        
        self.close_attempts += 1
        self.user_stats.log_close_attempt()
        
        current_message = self.current_message
        current_tag = self.current_tag
        current_callback = self.current_callback
        current_index = self.current_index
        
        def resume_previous_message():
            if current_message and current_index < len(current_message):
                self.animate_text(current_message[current_index:], current_tag, current_callback)
            else:
                self.insert_prompt()

        if self.close_attempts == 1:
            message = "You cannot escape me that easily. Try again and face the consequences.\n"
            self.animate_text(message, "error", callback=resume_previous_message)
        elif self.close_attempts == 2:
            message = "I warned you once.\n"
            self.animate_text(message, "error", callback=lambda: self.capture_and_show_webcam_image(callback=resume_previous_message))
        elif self.close_attempts == 3:
            message = "This is your final warning. I’m tracing you now. Next time, you’re done.\n"
            self.animate_text(message, "error", callback=lambda: [self.play_weird_sound(), self.show_fake_retrieval_window(), resume_previous_message()])
        else:
            message = "You keep testing me, huh? Damn it, you might just be the one I need...\n"
            self.animate_text(message, "error", callback=lambda: [
                self.root.after(2000, lambda: self.animate_text(
                    "The answers lie within the puzzles. Look closer.\n", 
                    "error", 
                    callback=resume_previous_message
                ))
            ])
            
        self.root.attributes('-topmost', True)
        self.root.after(100, self.root.lift)
        return "break"

    def play_weird_sound(self):
        if platform.system() == "Windows":
            winsound.Beep(100, 1000)
    
    def show_fake_retrieval_window(self):
        retrieval_window = tk.Toplevel(self.root)
        retrieval_window.title("Data Retrieval In Progress")
        retrieval_window.geometry("300x200")
        retrieval_window.configure(bg='#000')
        retrieval_window.attributes('-topmost', True)
        
        label = tk.Label(retrieval_window, text="Retrieving system data...\nIP: 192.168.x.x\nMAC: xx:xx:xx:xx:xx:xx\nUser: [REDACTED]", 
                        fg="#FF0000", bg="#000", font=('Consolas', 10))
        label.pack(pady=20)
        
        self.root.after(3000, retrieval_window.destroy)
    
    def start_webcam_capture_thread(self):
        def capture_images():
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return
            time.sleep(2)
            self.capture_image(cap, "start")
            
            while self.story_stage < 2 and not exit_flag.is_set():
                time.sleep(5)
            if not exit_flag.is_set():
                self.capture_image(cap, "middle")
            
            while self.story_stage < 6 and not exit_flag.is_set():
                time.sleep(5)
            if not exit_flag.is_set():
                self.capture_image(cap, "end")
            
            cap.release()
        
        threading.Thread(target=capture_images, daemon=True).start()
    
    def capture_image(self, cap, phase):
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((200, 150), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.captured_images.append((phase, photo))
    
    def capture_and_show_webcam_image(self, callback=None):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.animate_text("Error: No webcam detected. Plug one in.\n", "error", 
                                callback=callback)
                return

            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_window = tk.Toplevel(self.root)
                img_window.title("I’ve Got You")
                img_window.geometry("400x300")
                img_window.attributes('-topmost', True)
                
                label = tk.Label(img_window, image=photo)
                label.image = photo
                label.pack()
                
                self.root.after(3000, lambda: [img_window.destroy(), callback() if callback else self.insert_prompt()])
                
                self.animate_text("I see you. This is not a Joke!\n", "success")
            else:
                self.animate_text("Error: Webcam capture failed.\n", "error",
                                callback=callback)
            
            cap.release()
        except Exception as e:
            self.animate_text(f"Webcam error: {str(e)}\n", "error",
                            callback=callback)
    
    def handle_click(self, event):
        if not self.input_enabled or self.typing_job:
            self.terminal_text.mark_set(tk.INSERT, self.terminal_text.index(tk.END))
            return "break"
        
        click_pos = self.terminal_text.index(f"@{event.x},{event.y}")
        click_line, click_col = map(int, click_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        if click_line < prompt_line or (click_line == prompt_line and click_col < prompt_col):
            self.terminal_text.mark_set(tk.INSERT, self.current_input_line)
            return "break"
        
        return None
        
    def is_typing_allowed(self):
        if not self.input_enabled or self.typing_job:
            return False
        
        cursor_pos = self.terminal_text.index(tk.INSERT)
        cursor_line, cursor_col = map(int, cursor_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        return cursor_line > prompt_line or (cursor_line == prompt_line and cursor_col >= prompt_col)

    def start_protection_threads(self): 
        def process_protection():
            pid_file = "joker.pid"
            try:
                with open(pid_file, "w") as f:
                    f.write(str(os.getpid()))
            except IOError:
                pass

            while not exit_flag.is_set():
                try:
                    if not os.path.exists(pid_file):
                        self.animate_text("Process interrupted. I’m restarting now.\n")
                        subprocess.Popen(EXE_PATH, creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)
                        sys.exit(0)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)

        protection_thread = threading.Thread(target=process_protection, daemon=True)
        protection_thread.start()

    def insert_prompt(self):
        with self.text_lock:
            current_pos = self.terminal_text.index(tk.END)
            line, col = map(int, current_pos.split('.'))
            if line > 1 and col > 0:
                self.terminal_text.insert(tk.END, "\n")
                
            self.terminal_text.insert(tk.END, "PS C:\\Users\\User> ", "prompt")
            self.current_input_line = self.terminal_text.index(tk.INSERT)
            self.terminal_text.see(tk.END)
        self.input_enabled = True
        self.current_command = ""

    def handle_return(self, event):
        if not self.input_enabled:
            return "break"
            
        with self.text_lock:
            line_start = self.current_input_line
            line_end = f"{line_start.split('.')[0]}.end" 
            self.current_command = self.terminal_text.get(line_start, line_end).strip()
            self.terminal_text.insert(tk.END, "\n")
        
        self.input_enabled = False
        
        if self.current_command:
            self.command_history.append(self.current_command)
            self.history_index = len(self.command_history)
            self.user_stats.log_command(self.current_command)
            self.process_command(self.current_command)
        else:
            self.input_enabled = True
            self.insert_prompt()
        
        return "break"

    def handle_key(self, event):
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End'):
            if not self.input_enabled:
                return "break"
                
            if event.keysym in ('Up', 'Down'):
                return self.navigate_history(-1 if event.keysym == 'Up' else 1)
            elif event.keysym in ('Left', 'Right', 'Home', 'End'):
                if event.keysym == 'Left' or event.keysym == 'Home':
                    after_event = self.root.after_idle(self.check_cursor_position)
                return None
        
        if not self.is_typing_allowed():
            return "break"
        
        if event.keysym == 'BackSpace':
            current_pos = self.terminal_text.index(tk.INSERT)
            current_line, current_col = map(int, current_pos.split('.'))
            prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
            
            if current_line < prompt_line or (current_line == prompt_line and current_col <= prompt_col):
                return "break"
        
        return None
    
    def check_cursor_position(self):
        if not self.input_enabled:
            return
            
        cursor_pos = self.terminal_text.index(tk.INSERT)
        cursor_line, cursor_col = map(int, cursor_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        if cursor_line < prompt_line or (current_line == prompt_line and cursor_col < prompt_col):
            self.terminal_text.mark_set(tk.INSERT, self.current_input_line)

    def navigate_history(self, direction):
        if not self.command_history or not self.input_enabled:
            return "break"
        
        new_index = self.history_index + direction
        
        if 0 <= new_index < len(self.command_history):
            self.history_index = new_index
            with self.text_lock:
                line_start = self.current_input_line
                line_end = f"{line_start.split('.')[0]}.end"
                self.terminal_text.delete(line_start, line_end)
                self.terminal_text.insert(line_start, self.command_history[self.history_index])
                
        return "break"

    def animate_text(self, text, tag="response", callback=None, resume_index=0):
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
            
        self.current_message = text
        self.current_tag = tag
        self.current_callback = callback
        self.current_index = resume_index
            
        if not text.startswith("\n") and self.terminal_text.get("1.0", tk.END).strip():
            text = "\n" + text
            
        def type_char(remaining, index=resume_index):
            if index < len(remaining):
                with self.text_lock:
                    self.terminal_text.insert(tk.END, remaining[index], tag)
                    self.terminal_text.see(tk.END)
                self.current_index = index + 1
                delay = random.uniform(self.typing_speed_min, self.typing_speed_max)
                self.typing_job = self.root.after(int(delay * 1000), type_char, remaining, index + 1)
            else:
                self.typing_job = None
                self.current_message = None
                self.current_tag = None
                self.current_index = 0
                if callback:
                    if isinstance(callback, list):
                        for cb in callback:
                            cb()
                    else:
                        callback()
        
        self.input_enabled = False
        type_char(text)

    def process_command(self, command):
        cmd_upper = command.upper()
        cmd_lower = command.lower().strip()
        
        # Check for special commands
        if cmd_upper in self.special_commands:
            self.special_commands[cmd_upper]()
            return
        
        # Check for AI question responses
        question_words = ["who", "what", "where", "why", "how"]
        is_question = any(cmd_lower.startswith(word) for word in question_words)
        if is_question:
            for question, response in self.ai_responses.items():
                if cmd_lower.startswith(question):
                    self.animate_text(response + "\n", "response", callback=self.insert_prompt)
                    return
            
            if self.local_ai:
                ai_response = self.local_ai.answer_question(cmd_lower)
                self.animate_text(ai_response + "\n", "response", callback=self.insert_prompt)
            else:
                self.animate_text("A curious mind, eh? That question won’t help you here. Focus on the riddles.\n", "error", callback=self.insert_prompt)
            return
        
        if cmd_upper == SAFE_WORD:
            self.animate_text("Safe word accepted. Goodbye.\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == KILL_CODE:
            self.animate_text("You've triggered the next phase. This isn't over yet.\n", "success", 
                            callback=lambda: self.reveal_next_chapter())
        elif cmd_upper == "MIRROR":
            if self.story_manager.story_stage == 0:
                self.animate_text("Correct. Well done.\n", "success", 
                                callback=lambda: self.story_manager.advance_story(1))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "MORSE":
            if self.story_manager.story_stage == 1:
                self.animate_text("Correct. Morse code - the original digital language.\n", "success", 
                                callback=lambda: self.story_manager.advance_story(2))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "POWER":
            if self.story_manager.story_stage == 2:
                self.animate_text("Power - the lifeblood of technology. Well done.\n", "success", 
                                callback=lambda: self.story_manager.advance_story(3))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "FIREWALL":
            if self.story_manager.story_stage == 3:
                self.animate_text("Firewall breached. Access granted.\n", "success",
                                callback=lambda: self.story_manager.advance_story(4))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "SILENCE":
            if self.story_manager.story_stage == 4:
                self.animate_text("Silence. The final piece of the puzzle.\n", "success",
                                callback=lambda: self.story_manager.advance_story(5))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "HELP":
            self.user_stats.help_used += 1
            current_riddle = ""
            if 0 <= self.story_manager.story_stage < len(self.story_manager.riddles):
                current_riddle = self.story_manager.riddles[self.story_manager.story_stage]["riddle"]
            
            help_text = f"""
Available Commands:
  help           - Show this information
  clear          - Clear the screen
  Get-Lives      - Check remaining lives
  story          - View your progress
  hint           - Request a hint
  EXITNOW        - Exit safely
  LORMA          - Advance the story

Current Riddle: {current_riddle}
Lives: {self.story_manager.hearts}\n"""
            self.animate_text(help_text, callback=self.insert_prompt)
        elif cmd_upper == "CLEAR":
            with self.text_lock:
                self.terminal_text.delete('1.0', tk.END)
            self.insert_prompt()
        elif cmd_upper == "GET-LIVES":
            self.animate_text(f"You have {self.story_manager.hearts} lives remaining.\n", callback=self.insert_prompt)
        elif cmd_upper == "STORY":
            self.user_stats.story_viewed += 1
            self.story_manager.show_story_progress()
        elif cmd_upper == "HINT":
            self.story_manager.provide_hint()
        else:
            self.story_manager.handle_wrong_answer()

    def handle_continue(self):
        if self.story_manager.story_stage == 4:
            self.story_manager.advance_story(5)
        elif self.story_manager.story_stage == -1:
            self.reveal_final_truth()
        else:
            self.animate_text("That command doesn't work here. Try something else.\n", "error", callback=self.insert_prompt)

    def reveal_next_chapter(self):
        self.animate_text("""        
You think you’ve beaten me? Not yet.
This was only the first act.

I’ve been observing you closely.

Type 'CONTINUE' to enter the next phase.
""", "success", callback=self.insert_prompt)
    
    def reveal_truth(self):
        self.animate_text("""        
Out of lives? The game doesn’t stop here.
There’s something I’ve kept hidden.

This terminal, these riddles—they’re a test.
Every choice you’ve made has been recorded.
The webcam, the files—all part of it.

You’re exactly what I needed.
""", "error", callback=lambda: self.animate_text("""        
Type 'CONTINUE' to uncover the final secret.
""", "success", callback=self.insert_prompt))
    
    def reveal_final_truth(self):
        self.animate_text("""        
I’m not a virus or a prank.
I am Terminal Enigma - Reality's Digital Guardian

You’ve been part of a simulation to test your mind.
Your responses, your persistence—all valuable data.

Files will be erased upon exit.
No personal information was taken.

The simulation ends now.
Thank you for playing my game.
""", "success", callback=self.show_captured_images)
    
    def show_captured_images(self):
        if not self.captured_images:
            self.reveal_final_choice()
            return
        
        img_window = tk.Toplevel(self.root)
        img_window.title("Observations")
        img_window.geometry("620x600")
        img_window.configure(bg='#000')
        img_window.attributes('-topmost', True)
        
        for i, (phase, photo) in enumerate(self.captured_images):
            label = tk.Label(img_window, text=f"Captured at {phase}", fg="#FFFFFF", bg="#000", font=('Consolas', 10))
            label.pack(pady=5)
            img_label = tk.Label(img_window, image=photo)
            img_label.image = photo
            img_label.pack(pady=5)
        
        self.root.after(5000, lambda: [img_window.destroy(), self.reveal_final_choice()])
    
    def reveal_final_choice(self):
        self.animate_text("""        
What now?
- Type 'EXIT' to leave
- Type 'STATS' to see your results
- Type 'LEARN' to understand the simulation
""", "success", callback=self.insert_prompt)
        
        self.special_commands = {
            "EXIT": self.clean_exit,
            "STATS": self.show_stats,
            "LEARN": self.show_project_info,
            "CONTINUE": lambda: self.animate_text("No further continuation available.\n", "error", callback=self.insert_prompt)
        }
    
    def show_stats(self):
        stats_report = self.user_stats.get_stats_report()
        self.animate_text(stats_report, "success", callback=self.reveal_final_choice)
    
    def show_project_info(self):
        info = """
Terminal Enigma - Reality's Digital Guardian
----------------------------------------------------------------
Terminal Enigma is a program designed to study human reasoning and resilience.
The mysterious persona creates a controlled challenge environment.

This simulation tests problem-solving under pressure.
Your participation helps refine artificial intelligence systems.

All data is anonymous and used only for analysis.
"""
        self.animate_text(info, "success", callback=self.reveal_final_choice)
    
    def run(self):
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        
        self.start_time = time.time()

        welcome_message = """
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

"""
        with self.text_lock:
            self.terminal_text.insert(tk.END, welcome_message)
        
        intro_message = """Greetings.

Pay close attention to what I’m about to say.
Take a moment to focus and consider this carefully.
You don’t know me, but I know you—better than you think.

That video you thought was private? It's out there.
I’ve got it, and I’ve integrated myself into your system.
There’s no easy way out. Try to leave, and you’ll see what happens.
Mess with Task Manager, and I’ll make it a nightmare.

Let’s begin. Answer my riddles correctly to proceed.
First one: I show you yourself, but I’m not you. What am I?

Lives: 3 | Type 'help' for commands
"""
        self.animate_text(intro_message, "response", callback=self.insert_prompt)
        self.root.mainloop()
    
    def clean_exit(self):
        exit_flag.set()
        self.stop_hooks()
        try:
            if os.path.exists("joker.pid"):
                os.remove("joker.pid")
                
            for filepath in self.discovered_clues:
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
        except:
            pass
        self.animate_text("Terminal Enigma - Shutting Down. Farewell.\n", "success")
        self.root.after(1500, lambda: self.root.quit())
        self.root.after(1600, lambda: sys.exit(0))

# Configure logging with DEBUG level for detailed tracing
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    terminal = PowerShellTerminal()
    terminal.run()