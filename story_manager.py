import os
from resource_helper import resource_path, play_sound

class StoryManager:
    """Manages the story progression, riddles, and clues"""
    
    def __init__(self, terminal):
        self.terminal = terminal
        self.story_stage = 0
        self.discovered_clues = []
        self.hearts = 3
        
        self.riddles = {
            0: {
                "riddle": "If you drop me I'm sure to crack, but give me a smile and I'll always smile back. What am I?",
                "answer": "MIRROR",
                "hint": "You look into me to fix your hair, but I show everything backward."
            },
            1: {
                "riddle": "I’m what you’re called but not what you’re taught, something you have, but can’t be bought. What am I?",
                "answer": "NAME",
                "hint": "I'm how people communicated before voices could travel through wires."
            },
            2: {
                "riddle": "I hide your face but not your eyes, worn in sickness, fun, or lies—what am I?",
                "answer": "MASK",
                "hint": "I'm wore on your face to hide your identity."
            },
            3: {
                "riddle": "I’m not a photo, yet I stay; you carry me from yesterday—what am I??",
                "answer": "MEMORY",
                "hint": "I'm something you have, but can't be bought."
            },
            4: {
                "riddle": "I’m yours to make but not to keep; once decided, I’m buried deep—what am I?",
                "answer": "CHOICE",
                "hint": "Ladies ______ Mayonnaise"
            },
            5: {
                "riddle": "I follow you but never speak, I vanish when the sun is weak—what am I?",
                "answer": "SHADOW",
                "hint": "Noob Saibot"
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
            elif self.hearts == 1:
                # Play scream sound when only 1 life remains
                play_sound("scream.mp3")
                self.terminal.insert_prompt()
            else:
                self.terminal.insert_prompt()
                
        self.terminal.animate_text(error_message, "error", callback=add_prompt_after_error)
    
    def advance_story(self, stage):
        """Advance the story to a specific stage"""
        # Log stage completion
        self.terminal.user_stats.log_stage_complete(stage)
        
        # Explicitly update the story stage based on the current stage
        self.story_stage = stage + 1
        
        story_segments = {
            0: f"""
Good job. I thought you’d be hopeless.  
That mirror’s not just for checking your face, buddy. It’s showing you more than you think.  

Next riddle: {self.riddles[1]['riddle']}
""",
            1: f"""
Congrats. Big win there.  
Your name isn’t just a label, though. It's the first thing the world slaps on you, whether you like it or not. Like the humiliation that I'm going to give you if you fail to solve the next one.  

Now, for a clue, check your Downloads folder for a file called 'cipher.txt'.

Next riddle: {self.riddles[2]['riddle']}
""",
            2: f"""
Masks, huh? Everyone wears one. Whether it's for fun, lying, or just being miserable.  
Hmm... wondering what mask would you wear, after I leak those photos and videos of you LOL.

Next riddle: {self.riddles[3]['riddle']}
""",
            3: f"""
Memory is a joke. But I'll make sure won't forget this one ha ha ha.

I've left another file in your Downloads folder. Find 'shadow.bin'.
It contains a binary message that will lead you further.

Next riddle: {self.riddles[4]['riddle']}
""",
            4: f"""
Choices, huh? Should've thought of them before opening sketchy links. 

Next riddle: {self.riddles[5]['riddle']}
""",
            5: f"""
Shadow. Follows you around all day, then ghosts you at night.  
Kinda like the files you just downloaded—harmless, until they’re not XD
            
"""
        }
        
        if stage in story_segments:
            self.terminal.animate_text(story_segments[stage], "success", callback=self.terminal.insert_prompt)
            
            if stage == 0:
                self.story_stage = 1
            elif stage == 1:
                morse_message = self.text_to_morse("The next answer is MASK")
                self.create_hidden_clue("cipher.txt", f"MORSE CODE CIPHER:\n\n{morse_message}\n\nDecode to proceed.")
                self.story_stage = 2
            elif stage == 2:
                self.story_stage = 3
            elif stage == 3:
                binary_message = self.text_to_binary("The final answer is CHOICE")
                self.create_hidden_clue("shadow.bin", f"BINARY MESSAGE:\n\n{binary_message}\n\nDecode to proceed.")
                self.story_stage = 4
            elif stage == 4:
                self.story_stage = 5
            elif stage == 5:
                self.story_stage = 6
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
            self.terminal.animate_text(f"Hint: {hint}\n", callback=self.terminal.insert_prompt)
        else:
            self.terminal.animate_text("No hints at this point.\n", callback=self.terminal.insert_prompt)
