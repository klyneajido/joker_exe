import time
import os
import sys
import threading

def joker_virus():
    """Main virus logic with input handling"""
    os.system("cls" if os.name == "nt" else "clear")  # Cross-platform clear
    print("\033[92m" + "HA HA HA HA HA!" + "\033[0m")
    print("I'm the Joker, Robin! You fell for the leaked pic trick!")
    print("No pics here—just ME! Close me if you dare—I'll multiply!")
    print("\nRiddle #1: What's yellow and bends?")
    
    hearts = 3
    while hearts > 0:
        try:
            print("\033[95m" + "Still here, fool? Answer or lose a life!" + "\033[0m")
            time.sleep(3)
            
            clue_1 = input("\nEnter your answer (or the kill code later): ").upper().strip()
            
            if clue_1 == "WHYSOSERIOUS":
                print("\033[92mHA! Fine, you win! The Joker retreats!\033[0m")
                sys.exit(0)
            
            if clue_1 == "BANANA":
                print("Correct! Check www.jokerquest2.com for the next riddle!")
                break
            else:
                hearts -= 1
                print(f"Wrong! Lives left: {hearts}")
        
        except KeyboardInterrupt:
            print("\nInterruption detected. Exiting...")
            break
    
    if hearts == 0:
        print("\033[95mGame over, fool! I'm still here! HA HA!\033[0m")

if __name__ == "__main__":
    joker_virus()