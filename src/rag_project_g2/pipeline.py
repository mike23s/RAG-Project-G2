import asyncio

from ingestion.jobsearch import JobTechClient
import pdf


async def retrieve_jobs(search_phrase: str):
    client = JobTechClient()

    jobs = await client.search_jobs(search_phrase)

    for job in jobs:
        for field_name in job.model_fields:
            value = getattr(job, field_name)
            print(f"{field_name}: {value}")
        print("---")


if __name__ == "__main__":
    # print(pdf.parse_pdf("src/rag_project_g2/cv.pdf"))
    # extract phrase from cv to search_jobs
    #
    asyncio.run(retrieve_jobs("web utvecklare"))
