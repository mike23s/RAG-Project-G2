import os

from dotenv import load_dotenv
from openai import OpenAI
from azure.cosmos import CosmosClient


load_dotenv()


azure_openai_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
azure_openai_key = os.environ["AZURE_OPENAI_API_KEY"]
embedding_model = os.environ["AZURE_OPENAI_EMBEDDING_MODEL"]

cosmos_endpoint = os.environ["COSMOS_ENDPOINT"]
cosmos_key = os.environ["COSMOS_KEY"]
database_name = os.environ["COSMOS_DATABASE"]
container_name = os.environ["COSMOS_CONTAINER"]


openai_client = OpenAI(
    api_key=azure_openai_key,
    base_url=f"{azure_openai_endpoint.rstrip('/')}/openai/v1/"
)


cosmos_client = CosmosClient(
    cosmos_endpoint,
    credential=cosmos_key
)

database = cosmos_client.get_database_client(
    database_name
)

container = database.get_container_client(
    container_name
)


def create_embedding(text):
    response = openai_client.embeddings.create(
        model=embedding_model,
        input=text
    )

    return response.data[0].embedding


def vector_search(candidate_text, top_k=20):
    query_embedding = create_embedding(
        candidate_text
    )

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
    ORDER BY VectorDistance(
        c.embedding,
        @embedding
    )
    """

    parameters = [
        {
            "name": "@embedding",
            "value": query_embedding
        }
    ]

    results = list(
        container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True
        )
    )

    return results