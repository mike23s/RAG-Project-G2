from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from dotenv import dotenv_values


def parse_pdf(pdf: str) -> str | None:
    """
    Takes a path to a PDF file, parses it, and returns the full text.
    """

    config = dotenv_values(".env")
    endpoint = config["CONTENTUNDERSTANDING_ENDPOINT"]
    key = config["CONTENTUNDERSTANDING_KEY"]
    if not (endpoint and key):
        raise Exception("Environment variables missing")

    analyzer_id = "prebuilt-read"
    api_version = "2026-06-01-preview"

    client = ContentUnderstandingClient(
        endpoint=endpoint, credential=AzureKeyCredential(key), api_version=api_version
    )

    with open(pdf, "rb") as f:
        file_bytes = f.read()

    try:
        poller = client.begin_analyze_binary(
            analyzer_id=analyzer_id,
            binary_input=file_bytes,
            content_type="application/pdf",
        )
        result: AnalysisResult = poller.result()

    except AzureError as err:
        print(f"[Azure Error]: {err.message}")
        return

    return result.as_dict()["contents"][0]["markdown"]
