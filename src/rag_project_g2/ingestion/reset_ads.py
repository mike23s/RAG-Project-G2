"""Drop and recreate the Cosmos `ads` container (deletes every stored ad!).

Recreating (instead of deleting items) lets us set things that can't be changed later:
a vector index on /embedding and TTL support so ads expire at their deadline.

    PYTHONPATH=src python -m rag_project_g2.ingestion.reset_ads
"""

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError

from rag_project_g2.config import get_settings


def reset_ads_container() -> None:
    settings = get_settings()
    settings.require("cosmos_endpoint", "cosmos_key")
    client = CosmosClient(
        settings.cosmos_endpoint, credential=settings.cosmos_key.get_secret_value()
    )
    database = client.create_database_if_not_exists(settings.cosmos_database)

    try:
        database.delete_container(settings.cosmos_ads_container)
        print(f"Deleted container {settings.cosmos_ads_container!r}")
    except CosmosResourceNotFoundError:
        pass

    common = {
        "id": settings.cosmos_ads_container,
        "partition_key": PartitionKey(path="/region_id"),
        "default_ttl": -1,  # TTL on, but only items with their own `ttl` expire
    }
    vector_policy = {
        "vectorEmbeddings": [
            {
                "path": "/embedding",
                "dataType": "float32",
                "distanceFunction": "cosine",
                "dimensions": settings.embedding_dimensions,
            }
        ]
    }
    indexing_policy = {
        "indexingMode": "consistent",
        "includedPaths": [{"path": "/*"}],
        "excludedPaths": [{"path": '/"_etag"/?'}, {"path": "/embedding/*"}],
        "vectorIndexes": [{"path": "/embedding", "type": "quantizedFlat"}],
    }

    try:
        database.create_container(
            **common,
            vector_embedding_policy=vector_policy,
            indexing_policy=indexing_policy,
        )
        print("Created container with vector index")
    except CosmosHttpResponseError as err:
        # Accounts without the vector search capability reject the policy;
        # VectorDistance still works there, just as a full scan.
        print(f"Vector index not supported ({err.message.splitlines()[0]}); creating plain container")
        database.create_container(**common)


if __name__ == "__main__":
    reset_ads_container()
