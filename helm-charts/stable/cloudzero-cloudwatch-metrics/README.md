# cloudzero-cloudwatch-metrics

A helm chart for CloudWatch Agent to Collect Cluster Metrics

## Installing the Chart

Add the Cloudzero repository to Helm:

```sh
helm repo add cloudzero https://cloudzero.github.io/provision-account
```

Install or upgrading cloudzero-cloudwatch-metrics chart with default configuration:

Note: below is a helv3 command that creates a namespace for this deployment or
      use an exsisting namespace.

```sh
helm upgrade --install cloudzero-cloudwatch-metrics           \
             cloudzero/cloudzero-cloudwatch-metrics           \
             --namespace cloudzero-metrics --create-namespace \
             --set clusterName=<Your Cluster>
```

## Configuration

| Parameter | Description | Default | Required |
| - | - | - | -
| `image.repository` | Image to deploy | `cloudzero/cloudwatch-agent` | ✔
| `image.tag` | Image tag to deploy | `1.247349.0`
| `image.pullPolicy` | Pull policy for the image | `IfNotPresent` | ✔
| `clusterName` | Name of your cluster | `cluster_name` | ✔
| `serviceAccount.create` | Whether a new service account should be created | `true` | 
| `serviceAccount.name` | Service account to be used | | 
| `hostNetwork` | Allow to use the network namespace and network resources of the node | `false` | 

## Kubernetes runtime changes and EKS

In Kubernetes version 1.20, Kubernetes deprecated Dockershim, which allows Kubernetes to use Docker as a container runtime. Docker is still fully functional, but users will need to migrate to a different container runtime before support is removed in a future Kubernetes release.

CloudZero Helm Chart for Cloudzero-Agent version 0.0.3 will support the containerd runtime when used with Kebernetes 1.21 and containerd is turn on.

Customers using Kebernetes version 1.20 and older or version 1.21 without turning on containerd must install chart version 0.0.2.

```sh
helm upgrade --install cloudzero-cloudwatch-metrics           \
             cloudzero/cloudzero-cloudwatch-metrics           \
             --namespace cloudzero-metrics --create-namespace \
             --set clusterName=<Your Cluster>                 \
             --version 0.0.2
```
