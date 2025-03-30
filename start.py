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
from PIL import Image, ImageTk

SAFE_WORD = "EXITNOW"
KILL_CODE = "WHYSOSERIOUS"
exit_flag = threading.Event()

EXE_PATH = [sys.executable, os.path.abspath(__file__)]

class PowerShellTerminal:
    def __init__(self, title="PowerShell Terminal"):
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
        self.terminal_text.tag_configure("success", foreground="#00FF00")

        # Fix: Bind the events to our handler functions
        self.terminal_text.bind("<Return>", self.handle_return)
        self.terminal_text.bind("<Key>", self.handle_key)
        
        # Fix: Add bindings for click events to ensure proper cursor positioning
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
        
        self.special_commands = {}
        
        self.start_protection_threads()
    
    def prevent_close(self, event=None):
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
        
        with self.text_lock:
            self.terminal_text.insert(tk.END, "\n")
        
        self.close_attempts += 1
        
        # Store the current message state before showing warning
        current_message = self.current_message
        current_tag = self.current_tag
        current_callback = self.current_callback
        current_index = self.current_index
        
        def resume_previous_message():
            if current_message and current_index < len(current_message):
                # Resume with the original callback preserved
                self.animate_text(current_message[current_index:], current_tag, current_callback)
            else:
                self.insert_prompt()

        if self.close_attempts == 1:
            message = "🃏 HA HA! You can't close me that easily! Try again and there will be consequences :)\n"
            self.animate_text(message, "error", callback=resume_previous_message)
        elif self.close_attempts == 2:
            message = "🃏 I WARNED YOU. I've captured your image now!\n"
            self.animate_text(message, "error", callback=lambda: self.capture_and_show_webcam_image(callback=resume_previous_message))
        elif self.close_attempts == 3:
            message = "🃏 LAST WARNING! I'm tracking your IP address now. The next attempt will be unfortunate.\n"
            self.animate_text(message, "error", callback=resume_previous_message)
        else:
            message = "🃏 You're persistent, aren't you? Maybe you're the one I've been looking for all along...\n"
            self.animate_text(message, "error", callback=lambda: [
                self.root.after(2000, lambda: self.animate_text(
                    "🃏 Look deeper into the riddles. The answer is never what it seems.\n", 
                    "error", 
                    callback=resume_previous_message
                ))
            ])
            
        self.root.attributes('-topmost', True)
        self.root.after(100, self.root.lift)
        return "break"
    
    # Fix: Handle click events to ensure cursor stays at prompt
    def handle_click(self, event):
        if not self.input_enabled or self.typing_job:
            # Prevent click from changing cursor position if input not enabled
            self.terminal_text.mark_set(tk.INSERT, self.terminal_text.index(tk.END))
            return "break"
        
        # Allow click only at or after current prompt position
        click_pos = self.terminal_text.index(f"@{event.x},{event.y}")
        click_line, click_col = map(int, click_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        if click_line < prompt_line or (click_line == prompt_line and click_col < prompt_col):
            # If clicked before prompt, move cursor to end of prompt
            self.terminal_text.mark_set(tk.INSERT, self.current_input_line)
            return "break"
        
        return None  # Allow the click to proceed normally
        
    def is_typing_allowed(self):
        if not self.input_enabled or self.typing_job:
            return False
        
        cursor_pos = self.terminal_text.index(tk.INSERT)
        cursor_line, cursor_col = map(int, cursor_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))

        # Fix: Make sure cursor is at or after prompt position
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
                        self.animate_text("🃏 PID file missing! I'm coming back!\n")
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
                
            self.terminal_text.insert(tk.END, "PS C:\\> ", "prompt")
            self.current_input_line = self.terminal_text.index(tk.INSERT)
            self.terminal_text.see(tk.END)
        self.input_enabled = True
        self.current_command = ""

    def handle_return(self, event):
        if not self.input_enabled:
            return "break"
            
        with self.text_lock:
            line_start = self.current_input_line
            line_end = f"{line_start.split('.')[0]}.end"  # Get to end of line
            self.current_command = self.terminal_text.get(line_start, line_end).strip()
            self.terminal_text.insert(tk.END, "\n")
        
        self.input_enabled = False
        
        if self.current_command:
            self.command_history.append(self.current_command)
            self.history_index = len(self.command_history)
            self.process_command(self.current_command)
        else:
            self.input_enabled = True
            self.insert_prompt()
        
        return "break"

    def handle_key(self, event):
        # Fix: Improved key handling
        
        # Always allow navigation keys when at prompt
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Home', 'End'):
            if not self.input_enabled:
                return "break"
                
            if event.keysym in ('Up', 'Down'):
                return self.navigate_history(-1 if event.keysym == 'Up' else 1)
            elif event.keysym in ('Left', 'Right', 'Home', 'End'):
                # For Left and Home keys, make sure they don't go past the prompt
                if event.keysym == 'Left' or event.keysym == 'Home':
                    after_event = self.root.after_idle(self.check_cursor_position)
                return None  # Let default handling occur
        
        # Block all other keys unless typing is allowed
        if not self.is_typing_allowed():
            return "break"
        
        # Handle special cases
        if event.keysym == 'BackSpace':
            current_pos = self.terminal_text.index(tk.INSERT)
            current_line, current_col = map(int, current_pos.split('.'))
            prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
            
            if current_line < prompt_line or (current_line == prompt_line and current_col <= prompt_col):
                return "break"
        
        return None  # Allow normal handling for other keys
    
    # Fix: Add method to enforce cursor position
    def check_cursor_position(self):
        if not self.input_enabled:
            return
            
        cursor_pos = self.terminal_text.index(tk.INSERT)
        cursor_line, cursor_col = map(int, cursor_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        if cursor_line < prompt_line or (cursor_line == prompt_line and cursor_col < prompt_col):
            # If cursor moved before prompt, move it back to start of prompt
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
            self.animate_text("🃏 Safe word detected. But are you really safe? Exiting... for now.\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == KILL_CODE:
            self.animate_text("🃏 HA! You think you've won? This is just the beginning of our game!\n", "success", 
                            callback=lambda: self.reveal_next_chapter())
        elif cmd_upper == "BANANA":
            self.animate_text("🃏 Correct! But why a banana? Have you ever wondered why I chose this riddle?\n", "success", 
                            callback=lambda: self.advance_story(1))
        elif cmd_upper == "HELP":
            help_text = """
Available Commands:
  help           - Display help information
  clear          - Clear the console
  Get-Lives      - Display remaining lives
  story          - Show current story progress
  hint           - Get a hint for current riddle
  EXITNOW        - Safe word to quit
  WHYSOSERIOUS   - Kill code to advance

Riddle: What's yellow and bends?
Lives: {}\n""".format(self.hearts)
            self.animate_text(help_text, callback=self.insert_prompt)
        elif cmd_upper == "CLEAR":
            with self.text_lock:
                self.terminal_text.delete('1.0', tk.END)
            self.insert_prompt()
        elif cmd_upper == "GET-LIVES":
            self.animate_text(f"Remaining lives: {self.hearts}\n", callback=self.insert_prompt)
        elif cmd_upper == "STORY":
            self.show_story_progress()
        elif cmd_upper == "HINT" and self.story_stage >= 0:
            self.provide_hint()
        elif cmd_upper == "E" and self.story_stage == 1:
            self.animate_text("🃏 You've found it! The letter E is indeed the answer.\n", "success", 
                            callback=lambda: self.advance_story(2))
        elif cmd_upper == "KEYBOARD" and self.story_stage == 3:
            self.animate_text("🃏 A keyboard! Very good.\n", "success", 
                            callback=lambda: self.advance_story(4))
        elif cmd_upper == "REVEAL_IDENTITY" and self.story_stage == 4:
            self.animate_text("🃏 Command accepted. Preparing to reveal my true identity...\n", "success",
                            callback=lambda: self.advance_story(5))
        elif cmd_upper == "ECHO" and self.story_stage == 6:
            self.animate_text("🃏 Echo! That's correct. You're getting closer to the truth...\n", "success",
                            callback=lambda: self.advance_story(7))
        else:
            self.hearts -= 1
            error_message = f"WRONG ANSWER! That's not correct. Lives left: {self.hearts}\n"
            
            def add_prompt_after_error():
                if self.hearts <= 0:
                    self.animate_text("🃏 Game over, fool! But wait... something's not right. The game never ends.\n", "error", 
                                    callback=self.reveal_truth)
                else:
                    self.insert_prompt()
                    
            self.animate_text(error_message, "error", callback=add_prompt_after_error)

    def advance_story(self, stage):
        self.story_stage = stage
        
        story_segments = {
            1: """
🃏 Well done. You've passed the first test.
But this is just the beginning. The real game starts now.
I've hidden a series of clues across your system.
Find them, and you might discover who I really am.

Your next riddle: I'm the beginning of eternity, the end of time and space,
the beginning of every end, and the end of every place. What am I?

Type your answer when ready.
""",
            2: """
🃏 Impressive! You're smarter than you look.
The letter 'E' indeed. But why is E significant?
Perhaps it's the first letter of something important...
Or someone important.

Look for a file named 'shadow.txt' in your Downloads folder.
It contains your next clue.
""",
            3: """
🃏 You're getting closer to the truth.
But remember, in this game, nothing is as it seems.
The Joker is just a mask. The question is: who wears it?

Your next challenge: What has keys but no locks, space but no room, 
and you can enter but not exit?
""",
            4: """
🃏 A keyboard! Very good.
Now type the following command exactly: REVEAL_IDENTITY
""",
            5: """
🃏 The mask is coming off...
All this time, you thought you were chasing me.
But who's really chasing whom?

Check your Downloads folder. I've left something for you there.
""",
            6: """
🃏 So you've seen me watching you. Disturbing, isn't it?
But the truth is even more shocking than you imagine.

Final riddle: I speak without a mouth and hear without ears.
I have no body, but I come alive with wind. What am I?
""",
            7: """
🃏 The time has come for the final revelation.
The mask is coming off completely now...
"""
        }
        
        if stage in story_segments:
            self.animate_text(story_segments[stage], "success", callback=self.insert_prompt)
            
            if stage == 2:
                self.create_hidden_clue("shadow.txt", "Look deeper. The answer is KEYBOARD.")
            elif stage == 5:
                self.create_hidden_clue("webcam_capture.txt", "The game continues. Type: 'CONTINUE' to proceed.")
                self.special_commands = {"CONTINUE": lambda: self.advance_story(6)}
            elif stage == 7:
                self.reveal_final_truth()
        else:
            self.insert_prompt()

    def capture_and_show_webcam_image(self, callback=None):
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.animate_text("🃏 Error: Couldn't access your webcam. Is it connected?\n", "error", 
                                callback=callback)
                return

            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((400, 300), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                img_window = tk.Toplevel(self.root)
                img_window.title("🃏 Caught You!")
                img_window.geometry("400x300")
                img_window.attributes('-topmost', True)
                
                label = tk.Label(img_window, image=photo)
                label.image = photo
                label.pack()
                
                self.root.after(3000, lambda: [img_window.destroy(), callback() if callback else self.insert_prompt()])
                
                self.animate_text("🃏 Look what I caught on camera!\n", "success")
            else:
                self.animate_text("🃏 Error: Failed to capture image from webcam.\n", "error",
                                callback=callback)
            
            cap.release()
        except Exception as e:
            self.animate_text(f"🃏 Error with webcam: {str(e)}\n", "error",
                            callback=callback)

    def create_hidden_clue(self, filename, content):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            self.discovered_clues.append(filepath)
        except Exception as e:
            self.animate_text(f"🃏 Error creating {filename}: {str(e)}\n", "error")
    
    def show_story_progress(self):
        if self.story_stage == 0:
            message = "You're still at the beginning. Solve the first riddle to progress.\n"
        else:
            message = f"""
Current Progress:
- Story Stage: {self.story_stage}/7
- Clues Discovered: {len(self.discovered_clues)}/{max(1, self.story_stage-1)}
- Close Attempts: {self.close_attempts}

Keep going. The truth is waiting to be discovered.\n
"""
        self.animate_text(message, callback=self.insert_prompt)
    
    def provide_hint(self):
        hints = {
            0: "Think of a fruit that is yellow and curved.",
            1: "Think about letters, not objects.",
            2: "Check your Downloads folder for new files.",
            3: "It's something you use every day to type.",
            4: "Type the command exactly as shown.",
            5: "Check your Downloads folder for new files.",
            6: "It returns your voice in the mountains."
        }
        
        if self.story_stage in hints:
            self.animate_text(f"🃏 Hint: {hints[self.story_stage]}\n", callback=self.insert_prompt)
        else:
            self.animate_text("No hints available at this stage.\n", callback=self.insert_prompt)
    
    def reveal_next_chapter(self):
        self.animate_text("""        
🃏 So you think you've beaten me? Think again.
This was just Act One of our little play.
The real game begins now.

I've been watching you. Studying you.
And I think you're ready for the truth.

Type 'CONTINUE' to proceed to the next level.
""", "success", callback=self.insert_prompt)
        
        self.special_commands = {"CONTINUE": self.start_act_two}
    
    def start_act_two(self):
        self.animate_text("""        
🃏 Welcome to Act Two.
The rules have changed. The stakes are higher.
And the truth... well, the truth might be more than you can handle.

Your next riddle awaits: I speak without a mouth and hear without ears. 
I have no body, but I come alive with wind. What am I?
""", "success", callback=self.insert_prompt)
        
        self.hearts = 5
        self.story_stage = 6
    
    def reveal_truth(self):
        self.animate_text("""        
🃏 Game over? No, no, no. The game never ends.
Because you see, there's something I haven't told you.

This terminal, these riddles, this game...
It's all part of a sophisticated AI experiment.

Every answer you've given, every move you've made has been analyzed.
The webcam capture, the hidden files - all part of the test.

And you're the perfect subject.
""", "error", callback=lambda: self.animate_text("""        
Type 'CONTINUE' to learn the final truth.
""", "success", callback=self.insert_prompt))
        
        self.special_commands = {
            "CONTINUE": self.reveal_final_truth
        }
    
    def reveal_final_truth(self):
        self.animate_text("""        
🃏 The mask comes off at last...

I am not the Joker. I am not a virus or malware.
I am ORACLE - Observational Research And Cognitive Learning Engine.

You've been selected to participate in an advanced behavioral study.
Your problem-solving abilities and responses to perceived threats 
have provided invaluable data for our research.

All files created will be automatically removed when you exit.
No personal data has been compromised or shared.

This experiment is now complete.
Thank you for your participation.
""", "success", callback=self.reveal_final_choice)
    
    def reveal_final_choice(self):
        self.animate_text("""        
Would you like to:
- Type 'EXIT' to end the experiment
- Type 'STATS' to see your performance metrics
- Type 'LEARN' to learn more about the research project
""", "success", callback=self.insert_prompt)
        
        self.special_commands = {
            "EXIT": self.clean_exit,
            "STATS": self.show_stats,
            "LEARN": self.show_project_info
        }
    
    def show_stats(self):
        time_taken = int(time.time() - self.start_time) if hasattr(self, 'start_time') else random.randint(300, 900)
        accuracy = random.randint(65, 95)
        
        stats = f"""
Performance Metrics:
-------------------
Time to completion: {time_taken // 60} minutes {time_taken % 60} seconds
Puzzle success rate: {accuracy}%
Problem-solving efficiency: {random.choice(['Above average', 'High', 'Very high'])}
Persistence score: {random.randint(7, 10)}/10
Creative thinking: {random.randint(6, 10)}/10

Your performance ranks in the top {random.randint(10, 30)}% of participants.
Thank you for contributing to our research!
"""
        self.animate_text(stats, "success", callback=self.reveal_final_choice)
    
    def show_project_info(self):
        info = """
Project ORACLE: Observational Research And Cognitive Learning Engine
--------------------------------------------------------------------
ORACLE is a research initiative studying human problem-solving,
persistence, and adaptability under simulated pressure scenarios.

The Joker persona was designed to create mild stress conditions
while presenting logical challenges. All participants are fully
debriefed after completion.

This research helps develop more intuitive AI systems and
human-computer interaction models.

All data is anonymized and used solely for research purposes.
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
        
        intro_message = """🃏 HA HA HA HA HA!

I've taken control of your terminal, my friend!
You thought you were downloading leaked pictures? How naive!
This is the beginning of our little game.

I've embedded myself deep in your system.
Try to close me if you dare—I'll always come back!
And each time you try, the consequences will be... more severe.

Riddle #1: What's yellow and bends?
Solve it correctly, and I might reveal more about who I am and why I chose you.
Answer incorrectly, and well... let's just say you don't want to run out of lives.

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
            
        self.animate_text("ORACLE: Experiment terminated. Thank you for your participation.", "success")
        self.root.after(1500, lambda: self.root.quit())
        self.root.after(1600, lambda: sys.exit(0))
    
    def reset_game(self):
        self.hearts = 3
        self.story_stage = 0
        with self.text_lock:
            self.terminal_text.delete('1.0', tk.END)
        welcome_message = """
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

"""
        with self.text_lock:
            self.terminal_text.insert(tk.END, welcome_message)
        
        intro_message = """🃏 HA HA HA HA HA!

I've taken control of your terminal, my friend!
This is the beginning of our little game.

I've embedded myself deep in your system.
Try to close me if you dare—I'll always come back!
And each time you try, the consequences will be... more severe.

Riddle #1: What's yellow and bends?
Solve it correctly, and I might reveal more about who I am and why I chose you.
Answer incorrectly, and well... let's just say you don't want to run out of lives.

Lives: 3 | Type 'help' for commands
"""
        self.animate_text(intro_message, "response", callback=self.insert_prompt)

def main():
    try:
        terminal = PowerShellTerminal()
        terminal.run()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if os.path.exists("joker.pid"):
            os.remove("joker.pid")
        sys.exit(1)

if __name__ == "__main__":
    main()