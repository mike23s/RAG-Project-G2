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
