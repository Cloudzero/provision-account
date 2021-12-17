# CloudZero Container Metrics

A helm chart for collecting performance metrics down to the pod level.  CloudZero uses this data to calculate container cost to the pod, label, namespace, or Cluster level.  See our documentation [here](https://docs.cloudzero.com/docs/container-cost-track).

## Chart Installation

Add the CloudZero repository to Helm:

```sh
helm repo add cloudzero https://cloudzero.github.io/provision-account
```

### Prerequisite

The agent must have permission to create and write to a CloudWatch LogGroup and LogStream. Adding the AWS Managed policy `arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy` to the cluster nodes allows this. Review how you manage your nodes to see how best to attach this managed policy to the node role before installation.

### Considerations Before Installing

The agent consumes cpu and memory in relation to your cluster density. The density is defined by counting resources like number of nodes, pods, endpoints, and replicasets.  The chart values defined for CPU and Memory Limits/requests are suitable for a cluster density of 300 nodes, 5000 pods, and 70,000 ReplicaSets.

Install the latest version

```sh
helm upgrade --install cloudzero-cloudwatch-metrics           \
             cloudzero/cloudzero-cloudwatch-metrics           \
             --namespace cloudzero-metrics --create-namespace \
             --set clusterName=<Your Cluster>
```

> Note: these are helm3 commands that creates a namespace for this deployment or you can use an existing namespace.

## Configuration

| Parameter | Description | Default | Required |
| - | - | - | -
| `image.repository` | Image to deploy | `cloudzero/cloudwatch-agent` | ✔
| `image.tag` | Image tag to deploy | `1.247349.0`
| `image.pullPolicy` | Pull policy for the image | `IfNotPresent` | ✔
| `clusterName` | Name of your cluster | `cluster_name` | ✔
| `serviceAccount.create` | Whether a new service account should be created | `true` |
| `serviceAccount.name` | Service account to be used | |
| `hostNetwork` | Allow to use the network namespace and network resources of the node | `true` |
