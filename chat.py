import json
import google.generativeai as genai

with open("config.json", "r") as f:
    config = json.load(f)

print("Initializing Gemini Pro AI...")
genai.api_key = config["GEMINI_API_KEY"]

# Initialize the model
model = genai.GenerativeModel("gemini-1.5-flash") 

# Start a new chat session
chat = model.start_chat()

# Send a message and get a response
response1 = chat.send_message("""You are an assistant helping me with controlling the Tello drone using the djitellopy library. When I ask you to do something, you are supposed to give me Python code 
                    that is needed to achieve that task using the djitellopy library and then an explanation of what that code does. You are only allowed to use the functions provided by the djitellopy library.
                    You are not to use any other hypothetical functions that you think might exist.""")
print(f"Model response 1: {response1.text}")

prompt_file = "tello_basic.txt"
with open(prompt_file, "r") as f:
    prompt = f.read()
    
response2 = chat.send_message(prompt)
print(f"Model response 2: {response2.text}")

response3 = chat.send_message("takeoff")
print(f"Model response 3: {response3.text}")

response4 = chat.send_message("land")
print(f"Model response 4: {response4.text}")

# View the complete chat history
print("\n--- Chat History ---")
for message in chat.history:
    print(f"Author: {message.role}, Content: {message.parts[0].text}")
