from openai import OpenAI
import os
from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

itentions_dict = {
    "action": ["turn on", "turn off"],
    "item": ["living room light", "air conditioning", "bedroom light"],
}


def llm_inference(user_message, intentions_dict):
    """
    This function analyzes recession fear sentiment of articles for a given date using an LLM.
    The LLM is prompt to classify articles with a value between 1 and -1 (where 1 = high fear, -1 = no fear)

    Args:
    article_dict (dictionary): A dictionary with a list of dictionaries. Structured as {Date:[{id:,content:}]}
    max_attemps (int): A positive integer that sets how many retries the function will make in case the llm quota is exceded - API calls are free but rate limited

    Returns:
    list: A list of dictionaries with sentiment analysis and the most related sector results per article.
    """

    prompt = f"""
    
    Analyze the following message from the user and identify if there's any intention present in the list of itentions below (even if they are related). 
    The intention is combination of action and item, present in their respective lists.
    
    **User message:**
    {user_message}
    
    **Dictionary of intentions:**
    {intentions_dict}
    
    **Output format:**
    Respond **only** with a JSON dictionary, structured as follows:  
    ```json
    [{{"message": <your message> which should have should be short and concise except when told otherwise, 
      "action": <action that is implicit in the user message, and present in the Dictionary of itentions, a pair of the key "action">, 
      "item": <the item related that is implicit in the user message, and present in the Dictionary of itentions, a pair of the key "item">}}]
    
    """

    # call to OpenRouter LLM
    llm_response = client.chat.completions.create(
        model="mistralai/mistral-7b-instruct:free",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful home assistant, named Jarvis. You have a positive atitude.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    return llm_response


print(
    llm_inference(
        "Please turn on the lights in the living room", itentions_dict
    )
)
