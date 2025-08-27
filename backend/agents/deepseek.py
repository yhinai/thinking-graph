from openai import OpenAI
import os
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client with standard OpenAI API
try:
    # Create httpx client without proxy settings
    http_client = httpx.Client()
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        http_client=http_client
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    # Fallback initialization
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY")
    )

def get_reasoning_response(user_input: str) -> tuple[str, str]:
    """
    Get reasoning response from DeepSeek model via OpenRouter.
    Returns a tuple of (thoughts, response) where thoughts are the model's reasoning process
    and response is the final answer.
    """
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Using OpenAI GPT-3.5 model
        messages=[
            {
                "role": "system",
                "content": """You are a reasoning agent that thinks step by step.
                Format your response as follows:
                <think>
                [Your step-by-step reasoning process here]
                </think>
                [Your final answer here]"""
            },
            {
                "role": "user",
                "content": user_input
            }
        ]
    )

    response_text = completion.choices[0].message.content
    
    # Check if the response uses the expected <think></think> format
    if "<think>" in response_text and "</think>" in response_text:
        split_text = response_text.split("</think>")
        thoughts = split_text[0].replace("<think>", "").strip()
        response = split_text[1].strip() if len(split_text) > 1 else ""
    else:
        # Fallback: if model doesn't use expected format, treat the entire response as the answer
        # and create a simple reasoning note
        thoughts = f"Processing user query: {user_input}"
        response = response_text.strip()

    return thoughts, response

if __name__ == "__main__":
    # Test the implementation
    user_input = input("Enter your question: ")
    thoughts, response = get_reasoning_response(user_input)
    print("\nThoughts:\n", thoughts)
    print("\nResponse:\n", response)