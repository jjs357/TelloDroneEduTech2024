import re
import os
import json
from djitellopy import Tello
import google.generativeai as genai
import speech_recognition as sr

# Load configuration and initialize Gemini Pro AI. Ensure config.json is in the same directory as this file and contains the API Key
with open("config.json", "r") as f:
    config = json.load(f)

print("Initializing Gemini Pro AI...")

genai.api_key = config["GEMINI_API_KEY"]

# Initialize the model
# model = genai.GenerativeModel("gemini-1.5-flash") 
model = genai.GenerativeModel("gemini-2.5-flash") 


# Start a new chat session
chat = model.start_chat()

def init():
    # Send a message and get a response
    response1 = chat.send_message("""You are an assistant helping me with the DroneBlocks simulator for the Tello drone. When I ask you to do something, you are supposed to give me Python code 
                    that is needed to achieve that task using the DroneBlocks simulator and then an explanation of what that code does. You are only allowed to use the functions I have
                    defined for you. You are not to use any other hypothetical functions that you think might exist.""")
    print(f"Model Instructions 1: {response1.text}")
    
    prompt_file = "tello_basic.txt"
    with open(prompt_file, "r") as f:
        prompt = f.read()
        
    response2 = chat.send_message(prompt)
    print(f"Model Instructions 2: {response2.text}")

def ask(prompt):
    response = chat.send_message(prompt)
    return response.text

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

print(f"Done.")

init()

print(f"Initializing drone...")

drone = Tello()

try:
	drone.connect()
except Exception as e:
    if str(e) == "Did not receive a state packet from the Tello":
        # Handle the specific exception based on the message
        print("Caught missing Tello state: ignoring")
    else:
        # exit if the exception doesn't match the expected message
        print(f"Error connecting to Tello: {e}")
        exit()
    
#drone.get_battery()
#drone.streamon()
drone.query_battery()
drone.query_temperature()

print(f"Drone Init Done.")

print("Welcome to the Tello drone chatbot! I am ready to help you with your Tello questions and commands.")

# Main loop for user input via voice
recognizer = sr.Recognizer()
microphone = sr.Microphone()

while True:
    print(colors.YELLOW + "Tello Drone> " + colors.ENDC + "Listening for your command...")

    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    try:
        question = recognizer.recognize_google(audio)
        print(colors.YELLOW + "You said: " + colors.ENDC + question)

        if question.lower() in ["quit", "exit"]:
            break

        if question.lower() == "clear":
            os.system("cls" if os.name == 'nt' else 'clear')
            continue

        response = ask(question)

        print(f"\n{response}\n")

        code = extract_python_code(response)
        if code is not None:
            print("Please wait while I run the code with the Tello drone...")
            exec(code, globals(), {"drone": drone})
            print("Done!\n")

    except sr.UnknownValueError:
        print(colors.RED + "Sorry, I did not understand that." + colors.ENDC)
    except sr.RequestError as e:
        print(colors.RED + f"Could not request results; {e}" + colors.ENDC)

drone.end()
