import re
import os
import json
from djitellopy import Tello
from google import genai
import speech_recognition as sr

print("\nInitializing Gemini Pro AI...")

client = genai.Client()

chat = client.chats.create(model='gemini-2.0-flash-lite')

def init():
    # Send a message and get a response
    
    response1 = chat.send_message(
    message="""You are an assistant helping me with controlling the Tello drone using the djitellopy library. When I ask you to do something, you are supposed to give me Python code 
                    that is needed to achieve that task using the djitellopy library and then an explanation of what that code does. You are only allowed to use the functions provided by the djitellopy library.
                    You are not to use any other hypothetical functions that you think might exist."""
                    )
    print(f"\nModel Instructions 1: {response1.text}")
    
    prompt_file = "tello_basic.txt"
    with open(prompt_file, "r") as f:
        prompt = f.read()
        
    response2 = chat.send_message(message=prompt)
    print(f"\nModel Instructions 2: {response2.text}")

def ask(prompt):
    response = chat.send_message(message=prompt)
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

recognizer = sr.Recognizer()
microphone = sr.Microphone()

with microphone as source:
    print("Adjusting for ambient noise...")
    recognizer.adjust_for_ambient_noise(source) # Adjust for ambient noise
    print("Speak something to check mic!")
    audio = recognizer.listen(source)

try:
    test = recognizer.recognize_google(audio)
    print(f"\nYou said: {test}\n")
except recognizer.UnknownValueError:
    print("Could not understand audio")
except recognizer.RequestError as e:
    print(f"Could not request results from Google Speech Recognition service; {e}")

print(f"\nInitializing drone...")

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

print(f"\nDrone Init Done.")

print("\nWelcome to the Tello drone chatbot! I am ready to help you with your Tello questions and commands.")

# Main loop for user input via voice
while True:
    print(colors.YELLOW + "Tello Drone> " + colors.ENDC + "Listening for your command...")

    with microphone as source:
#        recognizer.adjust_for_ambient_noise(source)
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
