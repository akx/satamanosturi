from __future__ import annotations

import json

import click

from satamanosturi.docker import get_docker_client, pull_image, push_image
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
@click.option(
    "--confirm/--no-confirm",
    default=False,
    help="Confirm interactively before pushing",
)
@click.option(
    "--receipt-file",
    type=click.File("w"),
    help="Write a receipt JSON file with the details of the copied image",
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
    confirm: bool = False,
    receipt_file=None,
):
    try:
        dkr = get_docker_client()
    except Exception as e:
        raise click.ClickException(f"Failed to connect to Docker: {e}") from e
    source_repo = get_repo(source_repo_spec)
    dest_repo = get_repo(dest_repo_spec)
    source_repo.login(dkr)
    images = source_repo.get_images()
    source_image = find_latest_image_with_tag(images, tag=source_tag)
    if not source_image:
        raise click.ClickException(f"No image found with tag {source_tag} from {images!r}")

    dest_tags = set(additional_dest_tags)
    if copy_tags:
        dest_tags.update(source_image["imageTags"])
    for tag_to_remove in remove_dest_tags:
        dest_tags.discard(tag_to_remove)

    if not dest_tags:
        raise click.ClickException("No destination tags specified.")

    source_digest = source_image["imageDigest"]
    image = pull_image(dkr, source_repo, source_tag)
    print(f"Source digest: {source_digest}")
    print(f"Image ID:      {image.id}")
    print(f"Image tags:    {image.tags}")
    print(f"Labels:        {image.labels}")

    if confirm and not click.confirm("Continue?"):
        raise click.ClickException("Aborted.")

    dest_repo.login(dkr)

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

    if receipt_file:
        receipt_data = {
            "source": {
                "repository": source_repo.uri,
                "tag": source_tag,
                "digest": source_digest,
            },
            "destination": {
                "repository": dest_repo.uri,
                "tags": list(dest_tags),
            },
            "image": {
                "id": image.id,
                "tags": image.tags,
                "labels": image.labels,
            }
        }
        json.dump(receipt_data, receipt_file, ensure_ascii=False, indent=2, sort_keys=True)
