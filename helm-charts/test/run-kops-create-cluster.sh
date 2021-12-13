#!/usr/bin/env bash

# Run e2e tests

set -o errexit


kops create cluster --name=k8s-cluster.k8s.local \
  --state=s3://cz-kops-base \
  --cloud=aws \
  --vpc=vpc-d4b483af \
  --zones="us-east-1a,us-east-1b,us-east-1c" \
  --subnets="subnet-05d6d6c02cacf4474,subnet-0c1a3896519b2dcf0,subnet-046596eb985492dfb" \
  --master-count=3 \
  --master-size=c5.2xlarge \
  --node-count=4 \
  --node-size=c5.xlarge \
  --container-runtime=containerd \
  --kubernetes-version="1.20.9" \
  --authorization=RBAC \
  --networking=amazonvpc \
  --dry-run \
  -oyaml > erase.yaml

