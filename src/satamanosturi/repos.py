import boto3

from satamanosturi.models import ECRRepo, Repo


def get_repo(repo_spec: str) -> Repo:
    if repo_spec.startswith("ecr:"):
        return ECRRepo(ecr=boto3.client("ecr"), name=repo_spec[4:])
    raise ValueError(f"Unknown repo spec: {repo_spec}")
