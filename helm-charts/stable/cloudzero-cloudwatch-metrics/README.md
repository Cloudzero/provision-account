# CloudZero Container Metrics

---

A helm chart for collecting performance metrics down to the pod level.  CloudZero uses this data to calculate container cost to the pod, label, namespace, or Cluster level.  See our documentation [here](https://docs.cloudzero.com/docs/container-cost-track).

## Chart Installation

---

Add the CloudZero repository to Helm:

```sh
helm repo add cloudzero https://cloudzero.github.io/provision-account
```

### Prerequisite

---

The agent must have permission to create and write to a CloudWatch LogGroup and LogStream. Adding the AWS Managed policy `arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy` to the cluster nodes allows this. Review how you manage your node to see how to attach this managed policy before installation.

### Considerations Before Installing

---

The agent consumes cpu and memory in relation to your cluster density when initializing but then reduces cpu and memory usage after initialization. The density is defined by counting resources like number of nodes, pods, endpoints, and ReplicaSets.  The values in this chart are tuned for a cluster density of 300 nodes, 5000 pods, and 70,000 ReplicaSets. Even though the limits are high the agent will back off those limits but these values help the initial start-up.

The chart performs a rolling update on a DaemonSet as documented at [kubernetes.io](https://kubernetes.io/docs/tasks/manage-daemon/update-daemon-set/). The rolling update helps large/dense cluster by spreading out the start-up load.

One caveat of the rolling update is the initial release of the agent is a mass install and only the second update is a rolling update. Most cases, it is fine to install the latest the initial install and having the next update a rolling on the next upgrade. For those large dense cluster it is best to follow this two step strategy.  For less dense cluster just proceed to step 2.

#### Step 1

Install version 0.0.0 of the chart.

```sh
helm upgrade --install cloudzero-cloudwatch-metrics           \
             cloudzero/cloudzero-cloudwatch-metrics           \
             --namespace cloudzero-metrics --create-namespace \
             --set clusterName=<Your Cluster>                 \
             --version 0.0.0 
```

#### Step 2

Install the latest version

```sh
helm upgrade --install cloudzero-cloudwatch-metrics           \
             cloudzero/cloudzero-cloudwatch-metrics           \
             --namespace cloudzero-metrics --create-namespace \
             --set clusterName=<Your Cluster>
```

> Note: these are helm3 commands that creates a namespace for this deployment or you can use an existing namespace.

## Configuration

---

| Parameter | Description | Default | Required |
| - | - | - | -
| `image.repository` | Image to deploy | `cloudzero/cloudwatch-agent` | ✔
| `image.tag` | Image tag to deploy | `1.247349.0`
| `image.pullPolicy` | Pull policy for the image | `IfNotPresent` | ✔
| `clusterName` | Name of your cluster | `cluster_name` | ✔
| `serviceAccount.create` | Whether a new service account should be created | `true` |
| `serviceAccount.name` | Service account to be used | |
| `hostNetwork` | Allow to use the network namespace and network resources of the node | `true` |
