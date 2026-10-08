from openai import OpenAI

from .config import get_settings
from .pdf import parse_pdf

settings = get_settings()

client = OpenAI(
    api_key=settings.azure_openai_api_key.get_secret_value(),
    base_url=settings.azure_openai_endpoint,  # TODO /openai/v1?
)

with open("system_prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()

messages: list = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


def get_search_term(cv_text: str):
    messages.append(
        {
            "role": "user",
            "content": "Based on this CV, return ONLY a search term that can be used in Arbetsförmedlingens API as a query."
            "CV\n-----\n" + cv_text,
        }
    )

    return (
        client.chat.completions.create(
            model="gpt-5.4",
            messages=messages,
        )
        .choices[0]
        .message
    )
