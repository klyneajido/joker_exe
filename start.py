import tkinter as tk
import threading
import time
import os
import sys
import subprocess
import psutil
import signal
import random

# Safe word and kill code
SAFE_WORD = "EXITNOW"
KILL_CODE = "WHYSOSERIOUS"
exit_flag = threading.Event()

# Command to relaunch
EXE_PATH = [sys.executable, os.path.abspath(__file__)]

class PowerShellTerminal:
    def __init__(self, title="PowerShell Terminal"):
        # Main window setup
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x600")
        self.root.configure(bg='#012456')  # PowerShell dark blue background
        self.root.focus_force()

        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)
        self.root.bind("<Alt-F4>", lambda e: self.prevent_close())
        self.root.bind("<Control-q>", lambda e: self.prevent_close())

        # Create main frame for terminal
        self.main_frame = tk.Frame(self.root, bg='#012456')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create terminal output area with scrollbar
        self.scrollbar = tk.Scrollbar(self.main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.terminal_text = tk.Text(
            self.main_frame,
            bg='#012456',
            fg='#FFFFFF',  # White text
            insertbackground='#FFFFFF',
            font=('Consolas', 12),  # PowerShell uses Consolas
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.terminal_text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.terminal_text.yview)
        
        # Configure tags for styling
        self.terminal_text.tag_configure("prompt", foreground="#FFFF00")  # Yellow prompt
        self.terminal_text.tag_configure("response", foreground="#FFFFFF")  # White response
        self.terminal_text.tag_configure("error", foreground="#FF0000")    # Red errors
        self.terminal_text.tag_configure("success", foreground="#00FF00")  # Green success

        # Bind key events for command input
        self.terminal_text.bind("<Return>", self.handle_return)
        self.terminal_text.bind("<Key>", self.handle_key)
        
        # Keep track of current command input
        self.current_command = ""
        self.input_enabled = False
        self.current_input_line = "1.0"
        self.command_history = []
        self.history_index = -1
        
        # For typing animation
        self.typing_job = None
        self.typing_speed_min = 0.01
        self.typing_speed_max = 0.05
        
        # Initialize game state
        self.hearts = 3

        # Start protection threads
        self.start_protection_threads()

    def prevent_close(self, event=None):
        """Prevent the terminal from being closed"""
        self.terminal_text.insert(tk.END, "\n")  # Add a newline first
        self.animate_text("🃏 HA HA! You can't close me that easily, fool!\n", "error", 
                         callback=self.insert_prompt)  # Use error tag for red text
        self.root.attributes('-topmost', True)
        self.root.after(100, self.root.lift)  # Small delay to ensure window stays on top
        return "break"  # Prevent default close behavior

    def start_protection_threads(self):
        """Start threads for protection"""
        def process_protection():
            pid_file = "joker.pid"
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))

            while not exit_flag.is_set():
                try:
                    if not os.path.exists(pid_file):
                        self.animate_text("🃏 PID file missing! I'm coming back!\n")
                        subprocess.Popen(EXE_PATH, creationflags=subprocess.DETACHED_PROCESS)
                        sys.exit(0)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)

        protection_thread = threading.Thread(target=process_protection, daemon=True)
        protection_thread.start()

    def insert_prompt(self):
        """Insert a PowerShell-style prompt"""
        # Add a newline before the prompt if we're not at the beginning of the file
        current_pos = self.terminal_text.index(tk.END)
        line, col = map(int, current_pos.split('.'))
        if line > 1 and col > 0:  # Not at the beginning of the file
            self.terminal_text.insert(tk.END, "\n")
            
        self.terminal_text.insert(tk.END, "PS C:\\> ", "prompt")
        self.current_input_line = self.terminal_text.index(tk.INSERT)
        self.terminal_text.see(tk.END)  # Ensure the prompt is visible
        self.input_enabled = True
        self.current_command = ""

    def handle_return(self, event):
        """Handle Return key press to process commands"""
        if not self.input_enabled:
            return "break"
            
        # Get the command from the input line
        line_start = self.current_input_line
        line_end = self.terminal_text.index(tk.INSERT)
        self.current_command = self.terminal_text.get(line_start, line_end).strip()
        
        # Add a newline after the command
        self.terminal_text.insert(tk.END, "\n")
        
        # Process the command
        if self.current_command:
            # Add to history
            self.command_history.append(self.current_command)
            self.history_index = len(self.command_history)
            
            # Execute command
            self.process_command(self.current_command)
        else:
            # If empty command, just insert a new prompt
            self.insert_prompt()
        
        # Disable input temporarily during animation
        self.input_enabled = False
        self.terminal_text.see(tk.END)  # Make sure we see the end of text
        
        return "break"  # Prevent default behavior

    def handle_key(self, event):
        """Handle key presses in the terminal"""
        if not self.input_enabled:
            return "break"
            
        # Allow cursor keys, control keys, etc.
        if event.keysym in ('Left', 'Right', 'Home', 'End', 'BackSpace', 'Delete',
                            'Control_L', 'Control_R', 'Shift_L', 'Shift_R'):
            return  # Let these through
            
        # Handle Up/Down for command history
        if event.keysym == 'Up':
            self.navigate_history(-1)
            return "break"
        elif event.keysym == 'Down':
            self.navigate_history(1)
            return "break"
            
        # Ensure typing only happens at the current line or after
        cursor_pos = self.terminal_text.index(tk.INSERT)
        cursor_line, cursor_col = map(int, cursor_pos.split('.'))
        prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
        
        # If cursor is before the prompt line, move it to the end
        if cursor_line < prompt_line or (cursor_line == prompt_line and cursor_col < prompt_col):
            self.terminal_text.mark_set(tk.INSERT, f"{prompt_line}.end")
        
        # Don't allow backspacing into the prompt
        if event.keysym == 'BackSpace' and cursor_line == prompt_line and cursor_col <= prompt_col:
            return "break"
            
        return  # Allow regular typing

    def navigate_history(self, direction):
        """Navigate through command history"""
        if not self.command_history:
            return
            
        new_index = self.history_index + direction
        
        if 0 <= new_index < len(self.command_history):
            self.history_index = new_index
            
            # Clear current line
            line_start = self.current_input_line
            self.terminal_text.delete(line_start, f"{line_start.split('.')[0]}.end")
            
            # Insert history command
            self.terminal_text.insert(tk.END, self.command_history[self.history_index])

    def animate_text(self, text, tag="response", callback=None):
        """Add text with typing animation"""
        if self.typing_job:
            self.root.after_cancel(self.typing_job)
            
        # Add a newline before text if it doesn't start with one and we're not at the beginning
        if not text.startswith("\n") and self.terminal_text.get("1.0", tk.END).strip():
            text = "\n" + text
            
        def type_char(remaining, index=0):
            if index < len(remaining):
                self.terminal_text.insert(tk.END, remaining[index], tag)
                self.terminal_text.see(tk.END)
                delay = random.uniform(self.typing_speed_min, self.typing_speed_max)
                self.typing_job = self.root.after(int(delay * 1000), type_char, remaining, index + 1)
            else:
                self.typing_job = None
                if callback:
                    self.root.after(100, callback)  # Small delay before callback
        
        type_char(text)

    def process_command(self, command):
        """Process user input commands"""
        cmd_upper = command.upper()
        
        if cmd_upper == SAFE_WORD:
            self.animate_text("🃏 Safe word detected. Exiting gracefully...\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == KILL_CODE:
            self.animate_text("🃏 HA! Fine, you win! The Joker retreats!\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == "BANANA":
            self.animate_text("🃏 Correct! Check www.jokerquest2.com for the next riddle!\n", "success", 
                            callback=self.clean_exit)
        elif cmd_upper == "HELP":
            help_text = """
Available Commands:
  help           - Display help information
  clear          - Clear the console
  Get-Lives      - Display remaining lives
  EXITNOW        - Safe word to quit
  WHYSOSERIOUS   - Kill code to win

Riddle: What's yellow and bends?
Lives: {}\n""".format(self.hearts)
            self.animate_text(help_text, callback=self.insert_prompt)
        elif cmd_upper == "CLEAR":
            self.terminal_text.delete('1.0', tk.END)
            self.insert_prompt()
        elif cmd_upper == "GET-LIVES":
            self.animate_text(f"Remaining lives: {self.hearts}\n", callback=self.insert_prompt)
        else:
            self.hearts -= 1
            error_message = f"WRONG ANSWER! That's not correct. Lives left: {self.hearts}\n"
            
            # Display error message first, then add a new prompt after a delay
            def add_prompt_after_error():
                if self.hearts <= 0:
                    self.animate_text("🃏 Game over, fool! I'm still here! HA HA!\n", "error", 
                                    callback=self.reset_game)
                else:
                    self.insert_prompt()
                    
            self.animate_text(error_message, "error", callback=add_prompt_after_error)

    def reset_game(self):
        """Reset game after losing all lives"""
        self.hearts = 3
        self.insert_prompt()

    def clean_exit(self):
        """Gracefully exit the application"""
        exit_flag.set()
        pid_file = "joker.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        self.root.quit()
        os._exit(0)

    def run(self):
        """Run the terminal"""
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        welcome_message = """
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

"""
        self.terminal_text.insert(tk.END, welcome_message)
        
        intro_message = """🃏 HA HA HA HA HA!
I'm the Joker, Robin! You fell for the leaked pic trick!
No pics here—just ME! Close me if you dare—I'll come back!
Riddle #1: What's yellow and bends?
Lives: 3 | Type 'help' for commands
"""
        # Animate the Joker's message
        self.animate_text(intro_message, "response", callback=self.insert_prompt)

        print("Starting Tkinter event loop...")
        self.root.mainloop()

def main():
    pid_file = "joker.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            old_pid = int(f.read().strip())
        if psutil.pid_exists(old_pid):
            print("Application is already running!")
            sys.exit(1)
        else:
            os.remove(pid_file)

    terminal = PowerShellTerminal()
    terminal.run()

if __name__ == "__main__":
    main()