import time
import os
import sys

hearts = 3
def start_game():
    global hearts
    clue_1 = input("Enter your Answer: ")
    
    if clue_1 != "BANANA":
        hearts -= 1
        print("That is wrong! You now only have", hearts, "lives")
        start_game()
        if hearts==0:
            input("\nPress Enter to exit...")
            return 
    
    input("\nPress Enter to exit...")  # Prevents auto-closing

start_game()
