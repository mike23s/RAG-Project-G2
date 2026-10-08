def filter_by_score(jobs, min_score=0.35):
    """
    Keep only jobs with a score equal to
    or higher than the minimum score.
    """

    filtered_jobs = [
        job for job in jobs
        if job.get("score", 0) >= min_score
    ]

    return filtered_jobs


def get_match_level(score):
    """
    Convert the similarity score into
    an easy-to-understand match level.
    """

    if score >= 0.60:
        return "Strong match"

    elif score >= 0.50:
        return "Good match"

    elif score >= 0.35:
        return "Weak match"

    else:
        return "Very weak match"


