import base64
import dataclasses
from functools import cached_property

import tqdm
from docker import DockerClient
from mypy_boto3_ecr import ECRClient


class Repo:
    uri: str

    def get_images(self) -> list[dict]:
        ...

    def get_image(self, tag: str) -> dict:
        ...

    def login(self, dkr: DockerClient) -> None:
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
        kwargs = {
            "repositoryName": self.name,
            "maxResults": 1000,
            "filter": {"tagStatus": "TAGGED"},
        }
        images = []
        with tqdm.tqdm(desc=f"Fetching images for {self.name}", unit="image") as progress:
            while True:
                image_page = self.ecr.describe_images(**kwargs)
                page_images = image_page["imageDetails"]
                images.extend(page_images)
                progress.update(len(page_images))
                if "nextToken" not in image_page:
                    break
                kwargs["nextToken"] = image_page["nextToken"]
        return sorted(images, key=lambda image: image["imagePushedAt"], reverse=True)

    def get_image(self, tag: str):
        return self.ecr.describe_images(
            repositoryName=self.name,
            imageIds=[{"imageTag": tag}],
        )[
            "imageDetails"
        ][0]

    def login(self, dkr: DockerClient) -> None:
        resp = self.ecr.get_authorization_token()
        for token in resp["authorizationData"]:
            auth_token = base64.b64decode(token["authorizationToken"]).decode()
            username, _, password = auth_token.partition(":")
            registry = token["proxyEndpoint"].partition("://")[-1]
            dkr.api.login(
                username=username,
                password=password,
                registry=registry,
            )
            print(f"Logged in to {self.uri} ({registry})")
