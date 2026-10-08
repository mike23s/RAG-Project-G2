import asyncio

from ingestion.jobsearch import JobTechClient


async def main():
    client = JobTechClient()

    jobs = await client.search_jobs("Machine learning")

    for job in jobs:
        for field_name in job.model_fields:
            value = getattr(job, field_name)
            print(f"{field_name}: {value}")
        print("---")


if __name__ == "__main__":
    asyncio.run(main())
