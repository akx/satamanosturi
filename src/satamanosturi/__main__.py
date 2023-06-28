from __future__ import annotations

import logging

import click

from satamanosturi.commands.copy_image import copy_image


@click.group
def main():
    logging.basicConfig(level=logging.INFO)


main.add_command(copy_image)

if __name__ == "__main__":
    main()
