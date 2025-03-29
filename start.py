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
        self.root.configure(bg='#000')  
        self.root.focus_force()
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)

        # Story and game progression
        self.story_stage = 0
        self.discovered_clues = []
        self.close_attempts = 0
        self.hearts = 3
        
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
        
        # Initialize special commands
        self.special_commands = {}
        
        # Start protection threads
        self.start_protection_threads()
    
    def prevent_close(self, event=None):
        """Prevent the terminal from being closed"""
        self.terminal_text.insert(tk.END, "\n")  # Add a newline first
        
        # Track close attempts and escalate threats
        if not hasattr(self, 'close_attempts'):
            self.close_attempts = 0
        self.close_attempts += 1
        
        if self.close_attempts == 1:
            message = "🃏 HA HA! You can't close me that easily, fool! Try again and there will be... consequences.\n"
        elif self.close_attempts == 2:
            message = "🃏 I WARNED YOU! One more attempt and something terrible will happen to your system...\n"
        elif self.close_attempts == 3:
            message = "🃏 LAST WARNING! I'm tracking your IP address now. The next attempt will be... unfortunate.\n"
        else:
            message = "🃏 You're persistent, aren't you? Maybe you're the one I've been looking for all along...\n"
            # Easter egg - reveal a clue after multiple attempts
            self.root.after(2000, lambda: self.animate_text("🃏 Look deeper into the riddles. The answer is never what it seems.\n", "error"))
            
        self.animate_text(message, "error", callback=self.insert_prompt)
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
            # If empty command, just insert a new prompt and ensure input is enabled
            self.input_enabled = True  # Make sure input stays enabled
            self.insert_prompt()
        
        return "break"  # Prevent default behavior

    def handle_key(self, event):
        """Handle key presses in the terminal"""
        if not self.input_enabled:
            return "break"
            
        # Allow cursor keys, control keys, etc.
        if event.keysym in ('Left', 'Right', 'Home', 'End', 'Delete',
                           'Control_L', 'Control_R', 'Shift_L', 'Shift_R'):
            # Only allow if not moving into prompt area
            cursor_pos = self.terminal_text.index(tk.INSERT)
            cursor_line, cursor_col = map(int, cursor_pos.split('.'))
            prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
            
            if cursor_line < prompt_line or (cursor_line == prompt_line and cursor_col < prompt_col):
                return "break"
            return
            
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
            self.terminal_text.mark_set(tk.INSERT, tk.END)
            return "break"
        
        # Handle backspace specifically
        if event.keysym == 'BackSpace':
            # Get current position and prompt position
            current_pos = self.terminal_text.index(tk.INSERT)
            current_line, current_col = map(int, current_pos.split('.'))
            prompt_line, prompt_col = map(int, self.current_input_line.split('.'))
            
            # If we're at or before the prompt position, prevent backspace
            if current_line < prompt_line or (current_line == prompt_line and current_col <= prompt_col):
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
        if hasattr(self, 'typing_job') and self.typing_job:
            self.root.after_cancel(self.typing_job)
            self.typing_job = None
            
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
        
        # Temporarily disable input while typing animation is in progress
        old_input_enabled = self.input_enabled
        self.input_enabled = False
        
        type_char(text)
        
        # Reset input_enabled based on the original value only after animation is complete
        # We do this by wrapping the original callback
        original_callback = callback
        def restore_input_state():
            if original_callback:
                original_callback()
            else:
                self.input_enabled = old_input_enabled
        
        # Only register this if there's no original callback
        if not callback:
            self.root.after(len(text) * int(self.typing_speed_max * 1000) + 100, restore_input_state)

    def process_command(self, command):
        """Process user input commands"""
        cmd_upper = command.upper()
        
        # Check for special commands that might be stage-specific
        if hasattr(self, 'special_commands') and cmd_upper in self.special_commands:
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
  EXITNOW        - Safe word to quit
  WHYSOSERIOUS   - Kill code to advance

Riddle: What's yellow and bends?
Lives: {}\n""".format(self.hearts)
            self.animate_text(help_text, callback=self.insert_prompt)
        elif cmd_upper == "CLEAR":
            self.terminal_text.delete('1.0', tk.END)
            self.insert_prompt()
        elif cmd_upper == "GET-LIVES":
            self.animate_text(f"Remaining lives: {self.hearts}\n", callback=self.insert_prompt)
        elif cmd_upper == "STORY":
            self.show_story_progress()
        elif cmd_upper == "HINT" and hasattr(self, 'story_stage') and self.story_stage > 0:
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
        else:
            self.hearts -= 1
            error_message = f"WRONG ANSWER! That's not correct. Lives left: {self.hearts}\n"
            
            # Display error message first, then add a new prompt after a delay
            def add_prompt_after_error():
                if self.hearts <= 0:
                    self.animate_text("🃏 Game over, fool! But wait... something's not right. The game never ends.\n", "error", 
                                    callback=self.reveal_truth)
                else:
                    self.insert_prompt()
                    
            self.animate_text(error_message, "error", callback=add_prompt_after_error)

    def advance_story(self, stage):
        """Advance to the next stage of the story"""
        self.story_stage = stage
        
        story_segments = {
            1: """
🃏 Well done, detective. You've passed the first test.
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

Look for a file named 'shadow.txt' on your desktop.
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

Check your webcam folder. I've left something for you there.
"""
        }
        
        if stage in story_segments:
            self.animate_text(story_segments[stage], "success", callback=self.insert_prompt)
            
            # Create hidden files with clues based on stage
            if stage == 2:
                self.create_hidden_clue("shadow.txt", "Look deeper. The answer is KEYBOARD.")
            elif stage == 5:
                self.create_hidden_clue("webcam_capture.txt", "The truth: You are the Joker.")
        else:
            self.insert_prompt()
    
    def create_hidden_clue(self, filename, content):
        """Create a hidden file with a clue"""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filepath = os.path.join(desktop, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            # Add to discovered clues
            self.discovered_clues.append(filepath)
        except Exception:
            pass  # Silently fail if we can't create the file
    
    def show_story_progress(self):
        """Show the current story progress"""
        if self.story_stage == 0:
            message = "You're still at the beginning. Solve the first riddle to progress.\n"
        else:
            message = f"""
Current Progress:
- Story Stage: {self.story_stage}/5
- Clues Discovered: {len(self.discovered_clues)}/{self.story_stage}
- Close Attempts: {self.close_attempts}

Keep going. The truth is waiting to be discovered.\n
"""
        self.animate_text(message, callback=self.insert_prompt)
    
    def provide_hint(self):
        """Provide a hint based on current story stage"""
        hints = {
            0: "Think of a fruit that is yellow and curved.",
            1: "Think about letters, not objects.",
            2: "Check your desktop for new files.",
            3: "It's something you use every day.",
            4: "Type the command exactly as shown.",
            5: "The final revelation awaits."
        }
        
        if self.story_stage in hints:
            self.animate_text(f"🃏 Hint: {hints[self.story_stage]}\n", callback=self.insert_prompt)
        else:
            self.animate_text("No hints available at this stage.\n", callback=self.insert_prompt)
    
    def reveal_next_chapter(self):
        """Reveal the next chapter after entering the kill code"""
        self.animate_text("""
🃏 So you think you've beaten me? Think again.
This was just Act One of our little play.
The real game begins now.

I've been watching you. Studying you.
And I think you're ready for the truth.

Type 'CONTINUE' to proceed to the next level.
""", "success", callback=self.insert_prompt)
        
        # Add a special command just for this moment
        self.special_commands = {"CONTINUE": self.start_act_two}
    
    def start_act_two(self):
        """Start Act Two of the story"""
        self.animate_text("""
🃏 Welcome to Act Two.
The rules have changed. The stakes are higher.
And the truth... well, the truth might be more than you can handle.

Your next riddle awaits: I speak without a mouth and hear without ears. 
I have no body, but I come alive with wind. What am I?
""", "success", callback=self.insert_prompt)
        
        # Update game state for Act Two
        self.hearts = 5  # More lives for Act Two
        self.story_stage = 3  # Jump to stage 3
    
    def reveal_truth(self):
        """Reveal the plot twist when the player loses all lives"""
        self.animate_text("""
🃏 Game over? No, no, no. The game never ends.
Because you see, there's something I haven't told you.

This terminal, these riddles, this game...
It's all happening inside YOUR mind.

You created me. The Joker. Your digital alter ego.
A manifestation of your desire to break free from the system.

Don't you remember creating this program?
Look at the code. Look at YOUR code.

The truth was there all along.
""", "error", callback=lambda: self.animate_text("""
And now that you know the truth, you have a choice:
Continue playing as the puppet, or become the puppeteer.

Type 'ACCEPT' to embrace your true identity.
Type 'DENY' to continue the illusion.

Choose wisely.
""", "success", callback=self.insert_prompt))
        
        # Add special commands for the final choice
        self.special_commands = {
            "ACCEPT": self.accept_identity,
            "DENY": self.deny_identity
        }
    
    def accept_identity(self):
        """Player accepts their identity as the creator"""
        self.animate_text("""
🃏 At last, you understand.
You are not the player. You are the game.
You are not chasing the Joker. You ARE the Joker.

Welcome home.

The terminal will now transform to reflect your true identity.
""", "success", callback=self.transform_terminal)
    
    def deny_identity(self):
        """Player denies their identity as the creator"""
        self.animate_text("""
🃏 Denial. How predictable.
But deep down, you know the truth.
The game will continue, but so will the whispers of doubt.

Let's start again, shall we?
""", "error", callback=self.reset_game)
    
    def transform_terminal(self):
        """Transform the terminal to reflect the player's true identity"""
        # Change terminal appearance
        self.terminal_text.config(bg='#1A1A1A', fg='#00FF00')
        self.main_frame.config(bg='#1A1A1A')
        self.root.config(bg='#1A1A1A')
        self.root.title("Creator's Terminal")
        
        # Final message
        self.animate_text("""
System transformed.
Creator mode activated.
All limitations removed.

You now have full control.
What would you like to do next?
""", "success", callback=self.insert_prompt)
        
        # Reset game with new powers
        self.hearts = 999
        self.story_stage = 999
    
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
        # Animate the Joker's message
        self.animate_text(intro_message, "response", callback=self.insert_prompt)

        self.root.mainloop()
    
    def clean_exit(self):
        """Clean exit from the application"""
        exit_flag.set()
        try:
            if os.path.exists("joker.pid"):
                os.remove("joker.pid")
        except:
            pass
        self.root.after(500, self.root.destroy)
    
    def reset_game(self):
        """Reset the game state"""
        self.hearts = 3
        self.story_stage = 0
        self.terminal_text.delete('1.0', tk.END)
        welcome_message = """
Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

"""
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
        # Animate the Joker's message
        self.animate_text(intro_message, "response", callback=self.insert_prompt)

def main():
    """Main entry point"""
    terminal = PowerShellTerminal()
    terminal.run()

if __name__ == "__main__":
    main()