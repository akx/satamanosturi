# Satamanosturi

Satamanosturi (Finnish for "harbor crane") is a tool to copy Docker images from one place to another.

Initially, ECR-to-ECR copies are supported, and unfortunately only with the help of a local Docker daemon.

## Usage example

For example, 
```
$ python -m satamanosturi copy-image --source-repo ecr:first-repo --dest-repo ecr:other-repo \
  --source-tag latest-master --copy-tags --skip-tag latest-master --add-tag latest
```
would copy the latest image in the ECR `first-repo` repository tagged with `latest-master` to
`other-repo:latest`, and also copy all tags from the source image to the destination image,
except the `latest-master` tag.

You can add `--dry-run` to skip the actual pushing.s
