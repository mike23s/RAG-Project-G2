from openai import OpenAI

from rag_project_g2.config import get_settings

settings = get_settings()

client = OpenAI(
    api_key=settings.azure_openai_api_key.get_secret_value(),
    base_url=settings.openai_base_url,
)

with open("system_prompt.txt", "r") as f:
    SYSTEM_PROMPT = f.read()


def get_search_term(cv_text: str) -> str | None:
    # Fresh conversation per call so one user's CV never ends up in another's request
    messages: list = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Based on this CV, return ONLY a search term that can be used in Arbetsförmedlingens API as a query."
            "CV\n-----\n" + cv_text,
        },
    ]

    return str(
        client.chat.completions.create(
            model="gpt-5.4",
            messages=messages,
        )
        .choices[0]
        .message.content
    )
