#!/bin/bash
podman build -f Dockerfile -t podman-test --build-arg config=${1:-config.yaml}