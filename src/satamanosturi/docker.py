from __future__ import annotations

from docker import DockerClient
from docker.models.images import Image

from satamanosturi.models import Repo


def pull_image(dkr: DockerClient, source_repo: Repo, tag: str) -> Image:
    image_uri = f"{source_repo.uri}:{tag}"
    print(f"Pulling {image_uri}")
    for _entry in dkr.api.pull(
        repository=source_repo.uri,
        tag=tag,
        stream=True,
    ):
        print(".", end="", flush=True)
    print()
    return dkr.images.get(image_uri)


def push_image(dkr: DockerClient, repo: Repo, tag: str) -> None:
    for _entry in dkr.api.push(
        repository=repo.uri,
        tag=tag,
        stream=True,
    ):
        print(".", end="", flush=True)
    print()
