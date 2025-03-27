import tkinter as tk
import threading
import time
import os
import sys
import subprocess
import psutil
import signal
from PIL import Image, ImageTk  # For WebP support

# Safe word and kill code
SAFE_WORD = "EXITNOW"
KILL_CODE = "WHYSOSERIOUS"
exit_flag = threading.Event()

# Command to relaunch
EXE_PATH = [sys.executable, os.path.abspath(__file__)]

class JokerTerminal:
    def __init__(self, title="Joker's Lair"):
        # Main window setup
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("800x600")
        self.root.configure(bg='black')
        self.root.focus_force()  # Force focus on the window

        # Prevent closing
        self.root.protocol("WM_DELETE_WINDOW", self.prevent_close)
        self.root.bind("<Alt-F4>", lambda e: self.prevent_close())
        self.root.bind("<Control-q>", lambda e: self.prevent_close())

        # Create image frame
        self.image_frame = tk.Frame(self.root, bg='black')
        self.image_frame.pack(fill=tk.X, padx=10, pady=5)

        # Load and display WebP image
        try:
            img = Image.open("Hologram.webp")
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.image_label = tk.Label(self.image_frame, image=self.photo, bg='black')
            self.image_label.pack()
        except FileNotFoundError:
            print("WebP image 'Hologram.webp' not found. Skipping image display.")
        except Exception as e:
            print(f"Error loading WebP image: {e}")

        # Create main frame for terminal
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create terminal output area with scrollbar
        self.scrollbar = tk.Scrollbar(self.main_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = tk.Text(
            self.main_frame,
            bg='black',
            fg='#00FF00',
            insertbackground='#00FF00',
            font=('Courier New', 12),
            wrap=tk.WORD,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.output_text.yview)
        self.output_text.config(state=tk.DISABLED)

        # Create input area
        self.input_frame = tk.Frame(self.root, bg='black')
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.prompt_label = tk.Label(
            self.input_frame,
            text="joker@chaos:~$ ",
            bg='black',
            fg='#00FF00',
            font=('Courier New', 12)
        )
        self.prompt_label.pack(side=tk.LEFT)

        self.input_entry = tk.Entry(
            self.input_frame,
            bg='black',
            fg='#00FF00',
            insertbackground='#00FF00',
            font=('Courier New', 12),
            borderwidth=1,
            relief=tk.FLAT
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', self.process_command)
        self.input_entry.focus_set()  # Set initial focus
        self.root.update()  # Force update to ensure widget is rendered
        self.input_entry.focus_force()  # Force focus on entry

        # Initialize game state
        self.hearts = 3

        # Start protection threads
        self.start_protection_threads()

    def prevent_close(self, event=None):
        """Prevent the terminal from being closed"""
        self.log_message("🃏 HA HA! You can’t close me that easily, fool!")
        self.root.attributes('-topmost', True)
        self.root.lift()

    def start_protection_threads(self):
        """Start threads for protection"""
        def process_protection():
            pid_file = "joker.pid"
            with open(pid_file, "w") as f:
                f.write(str(os.getpid()))

            while not exit_flag.is_set():
                try:
                    if not os.path.exists(pid_file):
                        self.log_message("🃏 PID file missing! I’m coming back!")
                        subprocess.Popen(EXE_PATH, creationflags=subprocess.DETACHED_PROCESS)
                        sys.exit(0)
                    time.sleep(2)
                except Exception:
                    time.sleep(1)

        protection_thread = threading.Thread(target=process_protection, daemon=True)
        protection_thread.start()

    def log_message(self, message):
        """Log a message to the terminal"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, f"{message}\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def process_command(self, event):
        """Process user input commands"""
        command = self.input_entry.get().strip()
        if not command:
            self.input_entry.focus_set()
            return

        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, f"joker@chaos:~$ {command}\n")

        cmd_upper = command.upper()
        if cmd_upper == SAFE_WORD:
            self.log_message("🃏 Safe word detected. Exiting gracefully...")
            self.clean_exit()
        elif cmd_upper == KILL_CODE:
            self.log_message("🃏 HA! Fine, you win! The Joker retreats!")
            self.clean_exit()
        elif cmd_upper == "BANANA":
            self.log_message("🃏 Correct! Check www.jokerquest2.com for the next riddle!")
            self.clean_exit()
        elif cmd_upper == "HELP":
            help_text = """
Joker's Commands:
  help    - Show this help message
  clear   - Clear the screen
  EXITNOW - Safe word to quit
  WHYSOSERIOUS - Kill code to win
Riddle: What's yellow and bends?
Lives: {}
""".format(self.hearts)
            self.log_message(help_text)
        elif cmd_upper == "CLEAR":
            self.output_text.config(state=tk.NORMAL)
            self.output_text.delete('1.0', tk.END)
            self.output_text.config(state=tk.DISABLED)
        else:
            self.hearts -= 1
            self.log_message(f"🃏 Wrong! Lives left: {self.hearts}")
            if self.hearts <= 0:
                self.log_message("🃏 Game over, fool! I’m still here! HA HA!")
                self.hearts = 3

        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        self.input_entry.delete(0, tk.END)
        self.input_entry.focus_force()  # Ensure focus returns to input

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

        self.output_text.config(state=tk.NORMAL)
        welcome_message = """
╔══════════════════════════════════════╗
║      WELCOME TO JOKER'S LAIR         ║
╚══════════════════════════════════════╝
🃏 HA HA HA HA HA!
I'm the Joker, Robin! You fell for the leaked pic trick!
No pics here—just ME! Close me if you dare—I’ll come back!
Riddle #1: What's yellow and bends?
Lives: 3 | Type 'help' for commands
"""
        self.output_text.insert(tk.END, welcome_message)
        self.output_text.config(state=tk.DISABLED)

        print("Starting Tkinter event loop...")  # Debug to confirm loop start
        self.root.mainloop()

def main():
    pid_file = "joker.pid"
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            old_pid = int(f.read().strip())
        if psutil.pid_exists(old_pid):
            print("Joker is already running!")
            sys.exit(1)
        else:
            os.remove(pid_file)

    terminal = JokerTerminal()
    terminal.run()

if __name__ == "__main__":
    main()