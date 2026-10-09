# import os

# from dotenv import load_dotenv
from openai import OpenAI
from azure.cosmos import CosmosClient

from rag_project_g2.config import get_settings


settings = get_settings()

azure_openai_endpoint = settings.azure_openai_endpoint
azure_openai_key = settings.azure_openai_api_key
embedding_model = settings.embedding_deployment

cosmos_endpoint = settings.cosmos_endpoint
cosmos_key = settings.cosmos_key
database_name = settings.cosmos_database
container_name = settings.cosmos_ads_container
# if not (endpoint and key):
#     raise Exception("Environment variables missing")


# load_dotenv()
#
#
# azure_openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
# azure_openai_key = os.environ["AZURE_OPENAI_API_KEY"]
# embedding_model = os.environ["AZURE_OPENAI_EMBEDDING_MODEL"]
#
# cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
# cosmos_key = os.environ["COSMOS_KEY"]
# database_name = os.environ["COSMOS_DATABASE"]
# container_name = os.environ["COSMOS_CONTAINER"]


openai_client = OpenAI(
    api_key=azure_openai_key.get_secret_value(),
    base_url=settings.openai_base_url,
)


cosmos_client = CosmosClient(cosmos_endpoint, credential=cosmos_key.get_secret_value())

database = cosmos_client.get_database_client(database_name)

container = database.get_container_client(container_name)


def create_embedding(text):
    response = openai_client.embeddings.create(model=embedding_model, input=text)

    return response.data[0].embedding


def vector_search(candidate_text, top_k=20, region=None, remote_only=False):
    query_embedding = create_embedding(candidate_text)

    parameters = [{"name": "@embedding", "value": query_embedding}]

    # Filter inside Cosmos so TOP k is taken among matching ads only
    conditions = []
    if region:
        conditions.append("CONTAINS(c.region, @region, true)")
        parameters.append({"name": "@region", "value": region})
    if remote_only:
        conditions.append("c.remote = true")
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
    SELECT TOP {top_k}
        c.id,
        c.title,
        c.employer,
        c.description,
        c.municipality,
        c.region,
        c.occupation,
        c.remote,
        c.url,
        VectorDistance(
            c.embedding,
            @embedding
        ) AS score
    FROM c
    {where}
    ORDER BY VectorDistance(
        c.embedding,
        @embedding
    )
    """

    results = list(
        container.query_items(
            query=query, parameters=parameters, enable_cross_partition_query=True
        )
    )

    return results

