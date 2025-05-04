import os

class StoryManager:
    """Manages the story progression, riddles, and clues"""
    
    def __init__(self, terminal):
        self.terminal = terminal
        self.story_stage = 0
        self.discovered_clues = []
        self.hearts = 3
        
        self.riddles = {
            0: {
                "riddle": "I show you yourself, but I'm not you. What am I?",
                "answer": "MIRROR",
                "hint": "I reflect your digital identity."
            },
            1: {
                "riddle": "I'm the language of dots and dashes, older than computers. What am I?",
                "answer": "MORSE",
                "hint": "I'm how people communicated before voices could travel through wires."
            },
            2: {
                "riddle": "I flow through circuits, never seen but always felt. Without me, your device is just an empty shell. What am I?",
                "answer": "POWER",
                "hint": "I'm measured in watts and volts."
            },
            3: {
                "riddle": "I'm the guardian between you and chaos, filtering the good from the bad. What am I?",
                "answer": "FIREWALL",
                "hint": "I protect your system from unwanted visitors."
            },
            4: {
                "riddle": "I'm the absence of signal, yet my presence can be detected. What am I?",
                "answer": "SILENCE",
                "hint": "When data stops flowing, I'm what remains."
            }
        }
    
    def handle_wrong_answer(self):
        """Handle incorrect answers to riddles"""
        if self.hearts > 0:
            self.hearts -= 1
        
        self.terminal.user_stats.log_wrong_answer()
        
        error_message = f"Wrong! Damn it, that's not it. Lives left: {self.hearts}\n"
        
        def add_prompt_after_error():
            if self.hearts <= 0:
                self.story_stage = -1
                self.terminal.animate_text("You're out of lives. But this isn't the end—something's off.\n", "error", 
                                callback=self.terminal.reveal_truth)
            else:
                self.terminal.insert_prompt()
                
        self.terminal.animate_text(error_message, "error", callback=add_prompt_after_error)
    
    def advance_story(self, stage):
        """Advance the story to a specific stage"""
        self.terminal.user_stats.log_stage_complete(self.story_stage)
        self.story_stage = stage
        
        story_segments = {
            0: f"""
Good. You've solved the first puzzle.
The mirror reflects more than just your face - it reflects your digital presence.
I've planted clues for you to find. Each one brings you closer to the truth.

Next riddle: {self.riddles[1]['riddle']}
""",
            1: f"""
Check your Downloads folder for a file called 'cipher.txt'.
The file contains an encrypted message. Decrypt it to proceed.

Next riddle: {self.riddles[2]['riddle']}
""",
            2: f"""
You're proving yourself worthy of the next challenge.
Now enter this command exactly: DECRYPT_FIREWALL
""",
            3: f"""
I've left another file in your Downloads folder. Find 'shadow.bin'.
It contains a binary message that will lead you further.

Next riddle: {self.riddles[4]['riddle']}
""",
            4: f"""
Silence - the absence of signal. You've reached the final barrier.
Prepare for the truth to be unveiled...
"""
        }
        
        if stage in story_segments:
            self.terminal.animate_text(story_segments[stage], "success", callback=self.terminal.insert_prompt)
            
            if stage == 0:
                self.story_stage = 1
            elif stage == 1:
                morse_message = self.text_to_morse("The next answer is POWER")
                self.create_hidden_clue("cipher.txt", f"MORSE CODE CIPHER:\n\n{morse_message}\n\nDecode to proceed.")
                self.story_stage = 2
            elif stage == 2:
                self.story_stage = 3
            elif stage == 3:
                binary_message = self.text_to_binary("The final answer is SILENCE")
                self.create_hidden_clue("shadow.bin", f"BINARY MESSAGE:\n\n{binary_message}\n\nDecode to proceed.")
                self.story_stage = 4
            elif stage == 4:
                self.story_stage = 5
                self.terminal.reveal_final_truth()
        else:
            self.terminal.insert_prompt()
    
    def text_to_morse(self, text):
        """Convert text to Morse code"""
        morse_dict = {
            'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 
            'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 
            'M': '--', 'N': '-.', 'O': '---', 'P': '.--.', 'Q': '--.-', 'R': '.-.', 
            'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', 
            '3': '...--', '4': '....-', '5': '.....', '6': '-....', '7': '--...', 
            '8': '---..', '9': '----.', ' ': '/'
        }
        return ' '.join(morse_dict.get(c.upper(), '') for c in text)
    
    def text_to_binary(self, text):
        """Convert text to binary"""
        return ' '.join(format(ord(c), '08b') for c in text)
    
    def create_hidden_clue(self, filename, content):
        """Create a hidden clue file in the Downloads folder"""
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        filepath = os.path.join(downloads, filename)
        
        try:
            with open(filepath, "w") as f:
                f.write(content)
            self.discovered_clues.append(filepath)
            self.terminal.discovered_clues.append(filepath)
        except Exception as e:
            self.terminal.animate_text(f"Error creating {filename}: {str(e)}\n", "error")
    
    def show_story_progress(self):
        """Display the current story progress"""
        if self.story_stage == 0:
            message = "You're at the beginning. Solve the first riddle to move forward.\n"
        else:
            message = f"""
Current Progress:
- Story Stage: {self.story_stage}/5
- Clues Found: {len(self.terminal.discovered_clues)}/{max(1, self.story_stage-1)}
- Close Attempts: {self.terminal.close_attempts}

Keep pushing. The truth is near.\n
"""
        self.terminal.animate_text(message, callback=self.terminal.insert_prompt)
    
    def provide_hint(self):
        """Provide a hint for the current riddle"""
        self.terminal.user_stats.hints_requested += 1
        
        if 0 <= self.story_stage < len(self.riddles):
            hint = self.riddles[self.story_stage]['hint']
            self.terminal.animate_text(f"🔮 Hint: {hint}\n", callback=self.terminal.insert_prompt)
        else:
            self.terminal.animate_text("No hints at this point.\n", callback=self.terminal.insert_prompt)
