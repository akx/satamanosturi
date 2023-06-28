import dataclasses
from functools import cached_property

from mypy_boto3_ecr import ECRClient


class Repo:
    uri: str

    def get_images(self) -> list[dict]:
        ...

    def get_image(self, tag: str) -> dict:
        ...


@dataclasses.dataclass(frozen=True)
class ECRRepo(Repo):
    ecr: ECRClient
    name: str

    @cached_property
    def uri(self) -> str:
        return self.info["repositoryUri"]

    @cached_property
    def info(self) -> dict:
        return self.ecr.describe_repositories(
            repositoryNames=[self.name],
        )[
            "repositories"
        ][0]

    def get_images(self) -> list[dict]:
        return sorted(
            self.ecr.describe_images(
                repositoryName=self.name,
                maxResults=100,
            )["imageDetails"],
            key=lambda image: image["imagePushedAt"],
            reverse=True,
        )

    def get_image(self, tag: str):
        return self.ecr.describe_images(
            repositoryName=self.name,
            imageIds=[{"imageTag": tag}],
        )[
            "imageDetails"
        ][0]
