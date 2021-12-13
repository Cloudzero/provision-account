#!/usr/bin/env bash
set -euo pipefail

GIT_REPO_ROOT=$(git rev-parse --show-toplevel)
RS_DIR="${GIT_REPO_ROOT}/helm-charts/test/replica-sets"

echo $PWD
echo GIT_REPO_ROOT=${GIT_REPO_ROOT}
echo RS_DIR=${RS_DIR}

kubectl apply -f - <<EOF
apiVersion: v1 
kind: Namespace
metadata:
  name: misc-replica-sets 
  labels:
    name: misc-replica-sets
EOF


BATCH="1 2 3 4 5 6"
NUMRS=64000
i=49491
s=0
declare -a PIDS

# indent to supper yaml strick spacing requirement.
until [ $i -gt ${NUMRS} ]
do
for s in ${BATCH};
do
  n=$(printf "%05d" ${i})
  # Create a secret with several keys
   (kubectl apply --namespace misc-replica-sets -f - <<EOF
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: misc-replica-set-${n}
spec:
  replicas: 0
  selector:
    matchLabels:
      tier: misc-replica-set-${n}
  template:
    metadata:
      labels:
        tier: misc-replica-set-${n}
    spec:
      containers:
      - name: alpine
        image: alpine:latest
        resources:
          requests:
            cpu: "25m"
          limits:
            cpu: "50m"
        command: ["/bin/sh"]
        args:
        - -c
        - >-
            sleep \$(shuf -i 120-300 -n1) && echo "" 
EOF
) & > /dev/null
 PIDS[${s}]=$!
  ((i=i+1))
  done
  wait
  echo "Batch completed through " $n
done

