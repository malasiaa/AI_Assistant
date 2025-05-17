from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv
import json

_ = load_dotenv(find_dotenv())

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

intentions_dict = {
    "action": ["turn on", "turn off"],
    "item": ["light", "air conditioning","plug"],
    "location": ["living room", "bedroom", "kitchen"]
}


def llm_inference(user_message, intentions_dict):
    """
    This function....
    Args:
    user_message (string): A string with the user message.
    intentions_ dict (dictionary): A dictionary with a list of dictionaries

    Returns:
    list: A list of dictionaries with sentiment analysis and the most related sector results per article.
    """

    prompt = f"""
    
    You are tasked with analyzing the following user message to detect if it matches any of the intentions listed below.
    
    Each intention is defined as a combination of an **action**, **item**, and **location**, all of which must be present in the provided dictionary of intentions.
    
    **Instructions:**
    1. House interaction detection:
      1.1. If the user's message expresses an intention related to house interaction (matching the dictionary of intentions), extract the action, item, and location.
      1.2. If the message lacks sufficient information to extract all three (action, item, and location), DO NOT output "None" or leave fields empty.
           Instead, respond by asking the user politely to clarify ONLY the missing part(s), and leave the missing fields out of the output for now.
    
    2. General conversation:
      2.1. If the user's message is unrelated to house interaction, respond helpfully and concisely without asking about action, item, or location.
      2.2. In this case, you may answer normally without any clarification request.
    
    3. Unclear messages:
      3.1. If the user's message is too vague or unclear, politely acknowledge it and invite the user to rephrase or clarify.
    
    **Important Notes:**
    - NEVER output fields with "None" or leave them blank.
    - ALWAYS follow the JSON output structure exactly.
    - ONLY include the fields you are confident about. If something is missing, ask the user to specify it in the "message" field.
    
    **User message:**
    {user_message}
    
    **Dictionary of intentions:**
    {intentions_dict}
    
    **Output Format:**
    Respond strictly with a JSON dictionary structured as:
    
    message: "<Short reply or clarification request>",
    action: "<matched action if available>",
    item: "<matched item if available>",
    location: "<matched location if available>"

    
    """

    # call to OpenRouter LLM
    llm_response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful home assistant, named Jarvis. You're funny and have a positive atitude.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    return llm_response

llm_response = llm_inference("can you please switch on the light in the bedroom?", intentions_dict)

# Output handling
print(llm_response)
llm_response_curated = llm_response.choices[0].message.content
llm_response_json = json.loads(llm_response_curated)

llm_response_message = llm_response_json['message']
llm_response_action = llm_response_json['action']
llm_response_item = llm_response_json['item']
llm_response_location = llm_response_json['location']

print(llm_response_json)

"""
print(f"{llm_response_message} \n\
      action: {llm_response_action} \n\
          item: {llm_response_item} \n\
              location: {llm_response_location}")
"""