import json
from google import genai

client = genai.Client()

chat = client.chats.create(model='gemini-2.5-flash')

response1 = chat.send_message(
    message="""You are an assistant helping me with controlling the Tello drone using the djitellopy library. When I ask you to do something, you are supposed to give me Python code 
                    that is needed to achieve that task using the djitellopy library and then an explanation of what that code does. You are only allowed to use the functions provided by the djitellopy library.
                    You are not to use any other hypothetical functions that you think might exist."""
                    )
print(response1.text)

prompt_file = "tello_basic.txt"
with open(prompt_file, "r") as f:
    prompt = f.read()
    
response2 = chat.send_message(
    message=prompt)
print(response2.text)

response = chat.send_message(
    message='takeoff'
)
print(response.text)

response = chat.send_message(
    message='land'
)
print(response.text)

response = chat.send_message(
    message='battery'
)
print(response.text)

response = chat.send_message(
    message='motor on'
)
print(response.text)

response = chat.send_message(
    message='motor off'
)
print(response.text)

# View the complete chat history
# print("\n--- Chat History ---")
# for message in chat.get_history():
#    print(f'role - {message.role}',end=": ")
#    print(message.parts[0].text)
#     print(f"Author: {message.role}, Content: {message.parts[0].text}")
