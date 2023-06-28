from __future__ import annotations


def find_latest_image_with_tag(images: list[dict], *, tag: str) -> dict | None:
    return next((image for image in images if tag in image["imageTags"]), None)
