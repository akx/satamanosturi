from __future__ import annotations

import click
from docker import DockerClient

from satamanosturi.docker import pull_image, push_image
from satamanosturi.images import find_latest_image_with_tag
from satamanosturi.repos import get_repo


@click.command()
@click.option(
    "--source-repo",
    "source_repo_spec",
    required=True,
)
@click.option(
    "--dest-repo",
    "dest_repo_spec",
    required=True,
)
@click.option(
    "--source-tag",
    "source_tag",
    required=True,
)
@click.option(
    "--copy-tags/--no-copy-tags",
    help="Copy all tags from the source image",
)
@click.option(
    "--skip-tag",
    "remove_dest_tags",
    multiple=True,
    help="Skip these source tags in the destination",
)
@click.option(
    "--add-tag",
    "additional_dest_tags",
    multiple=True,
    help="Tag the image with these tags in the destination",
)
@click.option(
    "--dry-run/--no-dry-run",
    default=False,
    help="Don't actually push the tagged images",
)
def copy_image(
    *,
    source_repo_spec: str,
    dest_repo_spec: str,
    source_tag: str,
    copy_tags: bool = False,
    remove_dest_tags: list[str] = (),
    additional_dest_tags: list[str] = (),
    dry_run: bool = False,
):
    dkr = DockerClient.from_env()
    dkr.ping()
    source_repo = get_repo(source_repo_spec)
    dest_repo = get_repo(dest_repo_spec)
    images = source_repo.get_images()
    source_image = find_latest_image_with_tag(images, tag=source_tag)

    dest_tags = set(additional_dest_tags)
    if copy_tags:
        dest_tags.update(source_image["imageTags"])
    for tag_to_remove in remove_dest_tags:
        dest_tags.discard(tag_to_remove)

    if not dest_tags:
        raise click.ClickException("No destination tags specified.")

    source_digest = source_image["imageDigest"]
    image = pull_image(dkr, source_repo, source_tag)

    for tag in dest_tags:
        dest_spec = f"{dest_repo.uri}:{tag}"
        print(f"Tagging as {dest_spec}")
        image.tag(dest_repo.uri, tag)
        if dry_run:
            print(f"Would push {dest_spec}")
            continue
        print(f"Pushing {dest_spec}")
        push_image(dkr, dest_repo, tag)
        print(f"Verifying {dest_spec}")
        dest_image = dest_repo.get_image(tag)
        if dest_image["imageDigest"] != source_digest:
            raise RuntimeError(f"Digest mismatch for {tag}: {dest_image['imageDigest']} != {source_digest}")
