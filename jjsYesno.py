import asyncio
import platform
import subprocess
import speech_recognition as sr
import aiohttp
import os
import google.generativeai as genai
import time
from djitellopy import Tello

def get_gemini_response(question):
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    model = genai.GenerativeModel("gemini-1.5-flash")
    chat = model.start_chat()

    user_input = input(question)
    if user_input.lower() in ['exit', 'quit', 'bye']:
        return

    response = chat.send_message("Answer either 'yes' or 'no'. Do not use any other words." + user_input)
    model_output = response.text.strip().lower() 

        # Process the model's output to fit the required format
    if "yes" in model_output:
        final_response = "yes"
    elif "no" in model_output:
        final_response = "no"
    else:
        final_response = "i don't understand"

    print("Gemini:", final_response)
    return final_response

# Tello drone control
def control_tello(response):
    drone = Tello()
#    drone.connect()
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
    drone.takeoff()
    drone.query_battery()
    
    if response.lower() == "yes":
        for x in range(2):#say yes
            drone.send_rc_control(0, -80, 0, 0)  # Pitch up twice for a nod
            time.sleep(0.5)
            drone.send_rc_control(0, 80, 0, 0)   # Stop movement
            time.sleep(0.5)
        drone.send_rc_control(0, 0, 0, 0)
        
    elif response.lower() == "no":
        for y in range(2):#say no
            drone.send_rc_control(0, 0, 0, -80)  # Yaw left and right for a head shake
            time.sleep(0.5)
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.2)
            drone.send_rc_control(0, 0, 0, 80)
            time.sleep(0.5)
            drone.send_rc_control(0, 0, 0, 0)
            time.sleep(0.2)
    drone.send_rc_control(0, 0, 0, 0)
    drone.land()

# Function to capture verbal questions
def get_verbal_question():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        question = recognizer.recognize_google(audio)
        print(f"You said: {question}")
        
        return question
    except sr.UnknownValueError:
        print("Sorry, could not understand audio")
        return ""
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return ""
# Main program loop
def mains():
    
    #drone.wait_for_connection(60.0)

    question = get_verbal_question()
        #if question.lower() == 'exit' or question.lower() == 'quit' or question.lower() == 'stop' or question.lower() == 'land':
        #    break

    response = get_gemini_response(question)
    print(f"Gemini AI response: {response}")
    control_tello(response)
    
    

# Check platform and adjust library loading if necessary
#if platform.system() == 'Windows':
#    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

mains()
