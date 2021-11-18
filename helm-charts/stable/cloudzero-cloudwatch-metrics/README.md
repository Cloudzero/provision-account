# aws-cloudwatch-metrics

A helm chart for CloudWatch Agent to Collect Cluster Metrics

## Installing the Chart

Add the EKS repository to Helm:

```sh
helm repo add cloudzero https://cloudzero.github.io/provision-account
```

Install or upgrading aws-cloudwatch-metrics chart with default configuration:
Note: below is a helv3 command that creates a namespace for this deployment or
      use an exsisting namespace.

```sh
helm upgrade --install cloudzero-cloudwatch-metrics \
   --namespace cloudzero-metrics --create-namespace \
   cloudzero/cloudzero-cloudwatch-metrics           \
   --set clusterName=<Your Cluster>
```

## Configuration

| Parameter | Description | Default | Required |
| - | - | - | -
| `image.repository` | Image to deploy | `cloudzero/cloudwatch-agent` | ✔
| `image.tag` | Image tag to deploy | `1.0.0`
| `image.pullPolicy` | Pull policy for the image | `IfNotPresent` | ✔
| `clusterName` | Name of your cluster | `cluster_name` | ✔
| `serviceAccount.create` | Whether a new service account should be created | `true` | 
| `serviceAccount.name` | Service account to be used | | 
| `hostNetwork` | Allow to use the network namespace and network resources of the node | `false` | 
