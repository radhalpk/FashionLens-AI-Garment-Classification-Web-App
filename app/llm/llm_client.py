# gemini_client.py
import os
from langchain_google_genai import ChatGoogleGenerativeAI

from dotenv import load_dotenv
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY2")

def make_llm(model: str = "gemini-2.5-flash-lite", temperature: float = 0.15):
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=GOOGLE_API_KEY,
        temperature=temperature,
    )

def make_vision_llm(model: str = "gemini-2.5-flash", temperature: float = 0.3):
    """LLM configured for multimodal / vision tasks."""
    return ChatGoogleGenerativeAI(
        model=model,
        api_key=GOOGLE_API_KEY,
        temperature=temperature,
    )


# GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY4")
# def make_llm(model: str = "gemini-2.5-pro", temperature: float = 0.15):
#     return ChatGoogleGenerativeAI(
#         model=model,
#         api_key=GOOGLE_API_KEY,
#         temperature=temperature,
#     )

if __name__ == "__main__":
    # Example usage:
    llm = make_llm()
    res = llm.invoke("Hi").content
    print(res)