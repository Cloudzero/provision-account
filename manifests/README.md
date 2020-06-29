# Kubernetes Manifests
## AWS Log Proxy
Proxies connections to the CloudWatch Logs API and removes the `X-Amzn-Logs-Format` header to prevent generation of EMF metrics
### Installation
```
kubectl apply -f https://raw.githubusercontent.com/Cloudzero/provision-account/master/manifests/aws-logs-proxy.yaml
```

### CloudWatch Agent Configuration
While this may be used for any connection to CloudWatch Logs, the typical use case is to proxy connections from the
CloudWatch Agent to prevent cost Container Insights metrics, but keep the `performance` log stream.

#### Install the Agent
If you haven't already done so, follow the AWS instructions to [install the CloudWatch Agent for Container Insights.](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-metrics.html)

#### Find the AWS Log Proxy Service Endpoint
```
$ kubectl get service aws-logs-proxy-service
NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
aws-logs-proxy-service   ClusterIP   10.100.151.128   <none>        6000/TCP   23h
```
Copy the `CLUSTER-IP` from the output, it'll be used for the `<service-ip>` below.

#### Edit the CloudWatch Agent ConfigMap
Edit the `cwagent-configmap.yaml` that was downloaded in Step 3 of the [agent install instructions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Container-Insights-setup-metrics.html).  Add an `endpoint_override` parameter:
```
"endpoint_override": "http://<service-ip>:6000/<aws_region>"
```
The complete agent ConfigMap should now look something like this:
```
{
    "agent": {
        "region": "us-east-1"
    },
    "logs": {
        "metrics_collected": {
            "kubernetes": {
                "cluster_name": "MyCluster",
                "metrics_collection_interval": 60
            }
        },
        "force_flush_interval": 5,
        "endpoint_override": "http://10.100.151.128:6000/us-east-1"
    }
}
```

#### Restart the CloudWatch Agent
Editing an existing ConfigMap may require the CloudWatch Agent to be restarted.  Either delete and reapply the DaemonSet
manifest or follow the [instructions for updating the agent.](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights-update-image.html)

### Additional Notes
#### AWS SigV4 Proxy
This deployment is dependent on the [AWS SigV4 Proxy](https://github.com/awslabs/aws-sigv4-proxy) which has been prebuilt and uploaded to the [CloudZero DockerHub](https://hub.docker.com/repository/docker/cloudzero/aws-sigv4-proxy)

