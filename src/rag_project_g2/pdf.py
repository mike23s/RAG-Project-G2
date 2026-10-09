from azure.ai.contentunderstanding import ContentUnderstandingClient
from azure.ai.contentunderstanding.models import AnalysisResult
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import AzureError
from rag_project_g2.config import get_settings


def parse_pdf(pdf: str) -> str | None:
    """
    Takes a path to a PDF file, parses it, and returns the full text.
    """

    settings = get_settings()
    endpoint = settings.contentunderstanding_endpoint
    key = settings.contentunderstanding_key
    if not (endpoint and key):
        raise Exception("Environment variables missing")

    analyzer_id = settings.contentunderstanding_analyzer
    api_version = settings.contentunderstanding_api_version

    client = ContentUnderstandingClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(key.get_secret_value()),
        api_version=api_version,
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
