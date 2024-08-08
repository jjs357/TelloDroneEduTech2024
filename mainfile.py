import re
import argparse
import os
import json
%pip install djitellopy
from djitellopy import Tello
import google.generativeai as palm

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", type=str, default="tello_basic.txt")
args = parser.parse_args()

with open("config.json", "r") as f:
    config = json.load(f)

print("Initializing Gemini Pro AI...")
palm.api_key = config["GEMINI_API_KEY"]

chat_history = [
    {
        "author": "system",
        "content": """You are an assistant helping me with controlling the Tello drone using the djitellopy library. When I ask you to do something, you are supposed to give me Python code 
                    that is needed to achieve that task using the djitellopy library and then an explanation of what that code does. You are only allowed to use the functions provided by the djitellopy library.
                    You are not to use any other hypothetical functions that you think might exist.""",
    }
]

def ask(prompt):
    chat_history.append(
        {
            "author": "user",
            "content": prompt,
        }
    )
    response = palm.generate_text(
        model="models/chat-bison-001",
        prompt="\n".join([f"{msg['author']}: {msg['content']}" for msg in chat_history]),
        temperature=0.7,
    )
    chat_history.append(
        {
            "author": "assistant",
            "content": response.result,
        }
    )
    return chat_history[-1]["content"]

print(f"Done.")

code_block_regex = re.compile(r"```(.*?)```", re.DOTALL)

def extract_python_code(content):
    code_blocks = code_block_regex.findall(content)
    if code_blocks:
        full_code = "\n".join(code_blocks)

        if full_code.startswith("python"):
            full_code = full_code[7:]

        return full_code
    else:
        return None

class colors:  # You may need to change color settings
    RED = "\033[31m"
    ENDC = "\033[m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"

print(f"Initializing drone...")

drone = Tello()
drone.connect()
drone.streamon()

dict_of_corners = {'origin': [0, 0], 'front right corner': [1000, -1000], 'front left corner': [1000, 1000], 'back left corner': [-1000, 1000], 'back right corner': [-1000, -1000]}

print(f"Done.")

with open(args.prompt, "r") as f:
    prompt = f.read()

ask(prompt)

print("Welcome to the Tello drone chatbot! I am ready to help you with your Tello questions and commands.")

while True:
    question = input(colors.YELLOW + "Tello Drone> " + colors.ENDC)

    if question == "!quit" or question == "!exit":
        break

    if question == "!clear":
        os.system("cls" if os.name == 'nt' else 'clear')
        continue

    response = ask(question)

    print(f"\n{response}\n")

    code = extract_python_code(response)
    if code is not None:
        print("Please wait while I run the code with the Tello drone...")
        exec(code, globals(), {"drone": drone})
        print("Done!\n")

drone.end()
