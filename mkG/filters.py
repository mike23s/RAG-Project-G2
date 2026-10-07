def filter_jobs(jobs, region=None, remote_only=False):
    """
    Filter jobs by region and remote preference.

    jobs:
        A list of job dictionaries.

    region:
        Region to filter by.
        Example: "Stockholm"

    remote_only:
        If True, only return remote jobs.
    """

    filtered_jobs = jobs

    # Filter by region
    if region:
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get("region") == region
        ]

    # Filter by remote jobs
    if remote_only:
        filtered_jobs = [
            job for job in filtered_jobs
            if job.get("remote") is True
        ]

    return filtered_jobs


# Temporary mock job data
jobs = [
    {
        "id": "job-1",
        "title": "Python Developer",
        "company": "Tech AB",
        "region": "Stockholm",
        "remote": True,
        "score": 0.88
    },
    {
        "id": "job-2",
        "title": "Data Analyst",
        "company": "Data AB",
        "region": "Malmö",
        "remote": False,
        "score": 0.61
    },
    {
        "id": "job-3",
        "title": "Cloud Developer",
        "company": "Cloud AB",
        "region": "Stockholm",
        "remote": False,
        "score": 0.81
    },
    {
        "id": "job-4",
        "title": "Frontend Developer",
        "company": "Web AB",
        "region": "Göteborg",
        "remote": True,
        "score": 0.55
    }
]


# Test region filter
stockholm_jobs = filter_jobs(
    jobs,
    region="Stockholm"
)

print("Jobs in Stockholm:")

for job in stockholm_jobs:
    print(
        job["title"],
        "-",
        job["region"],
        "- Remote:",
        job["remote"]
    )


# Test region and remote filter
remote_stockholm_jobs = filter_jobs(
    jobs,
    region="Stockholm",
    remote_only=True
)

print("\nRemote jobs in Stockholm:")

for job in remote_stockholm_jobs:
    print(
        job["title"],
        "-",
        job["region"],
        "- Remote:",
        job["remote"]
    )