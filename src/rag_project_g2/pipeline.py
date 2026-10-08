import asyncio

from ingestion.jobsearch import JobTechClient
import pdf
import llm


async def retrieve_jobs(search_phrase: str):
    client = JobTechClient()

    jobs = await client.search_jobs(search_phrase)

    for job in jobs:
        for field_name in job.model_fields:
            value = getattr(job, field_name)
            print(f"{field_name}: {value}")
        print("---")


if __name__ == "__main__":
    cv_text = pdf.parse_pdf("src/rag_project_g2/cv.pdf")
    search_term = llm.get_search_term(cv_text)
    asyncio.run(retrieve_jobs(search_phrase=search_term))
