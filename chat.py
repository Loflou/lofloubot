import os
from dotenv import load_dotenv
import openai
import requests
import json
import logging
import yaml  # New import

# Load environment variables
load_dotenv()
# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
# Set the Google Search API key
google_api_key = os.getenv("GOOGLE_API_KEY")
google_cx = os.getenv("GOOGLE_CX")

# Set up logging
logging.basicConfig(filename='chatbot.log', level=logging.INFO)

print("ChatGPT: Hi, I'm ChatGPT. I'm a helpful assistant")
messages = [
  {"role": "system", "content": "You are a helpful assistant."},
]

def save_to_yaml(data, filename):  # New function
    with open(filename, 'w') as file:
        yaml.dump(data, file)

def google_search(query):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': google_api_key,
        'cx': google_cx,
        'q': query,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # ensure we notice bad responses
    return response.json()['items']

google_search_function = [
    {
        "name": "search_web",
        "description": "Perform a Google search",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                }
            },
            "required": ["query"]
        }
    }
]

# Function to call OpenAI API
def call_openai_api(functions=None):
    try:
        chat_completion = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=messages,
            functions=functions,
        )
        print(f"Chat completion: {chat_completion}")  # Print statement added here
        return chat_completion
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("An error occurred. Please check the log for more details.")
        return None

while True:
    message = input("👤: ")
    if message == "exit":
        break
    if message == "clear":
        print("\033[H\033[J")
        print("ChatGPT: Hi, I'm ChatGPT. I'm a helpful assistant")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
        ]
                
        continue

    if message:
        messages.append(
            {"role": "user", "content": message},
        )

        # Save the chat history after a new message
        save_to_yaml(messages, 'chat_history.yaml')

        # Call OpenAI API
        chat_completion = call_openai_api(google_search_function)

        if chat_completion is None:
            print("Error: The API call didn't return a response.")
        else:
            try:
                reply = chat_completion["choices"][0]["message"]["content"]

                # Check if function_call is related to a web search
                if "function_call" in chat_completion["choices"][0]["message"]:
                    function_call = chat_completion["choices"][0]["message"]["function_call"]
                    if function_call["name"] == "search_web":
                        arguments = json.loads(function_call["arguments"])  # parse the arguments into a dictionary
                        query = arguments["query"]
                        print(f"Search query: {query}")  # Print statement added here
                        search_results = google_search(query)
                        print(f"Search results: {search_results}")  # Print statement added here

                        # Send results back to OpenAI API
                        messages.append(
                            {"role": "function", "name": "search_web", "content": json.dumps(search_results)},
                        )
                        # Save the chat history after a new message
                        save_to_yaml(messages, 'chat_history.yaml')
                        
                        chat_completion = call_openai_api(google_search_function)
                        if chat_completion is None:
                            print("Error: The API call didn't return a response.")
                        else:
                            try:
                                reply = chat_completion["choices"][0]["message"]["content"]
                            except KeyError:
                                print("Error: The API response didn't contain the expected data.")

            except KeyError:
                print("Error: The API response didn't contain the expected data.")

        print(f"🤖: {reply}")
