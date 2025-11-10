# CloudZero Account Provisioning Template for AWS

## About CloudZero
CloudZero provides Cloud Cost Intelligence for Engineering Teams and is designed to eliminate manual work, build cost optimized software, and optimize your AWS bill.

To learn more about CloudZero, visit [CloudZero.com](cloudzero.com) or start by creating an account at https://app.cloudzero.com and activating a free 30 day trial.

## About this template
This template provides full transparency into the permissions and process CloudZero recommends for connecting their AWS accounts. In addition to using this template to fully automate the process, CloudZero supports multiple manual methods for connecting accounts to the CloudZero platform. You can learn more about your options at [docs.cloudzero.com](https://docs.cloudzero.com/docs/getting-started)

## AWS Permissions Explained

CloudZero requires **read-only** access to your AWS account to provide cost intelligence and optimization recommendations. CloudZero **never** modifies your AWS resources, infrastructure, or configurations.

### Why CloudZero Needs AWS Access

CloudZero analyzes your AWS usage to:
- Break down costs by team, product, feature, or any dimension you choose
- Identify optimization opportunities (rightsizing, reserved capacity, unused resources)
- Track Kubernetes and container costs at the pod/service level
- Monitor cost anomalies and unusual spending patterns
- Provide unit cost metrics (cost per customer, per transaction, per deployment)

### Permission Categories

| Category | AWS Services | Purpose | What CloudZero Accesses |
|----------|--------------|---------|-------------------------|
| **Cost & Billing Analysis** | S3 (CUR), Cost Explorer, Billing, Pricing, Tax, Invoicing | Analyze AWS spending and generate cost intelligence reports | Cost and Usage Report data, billing details, pricing information |
| **Compute Optimization** | Compute Optimizer, Reserved Instances (EC2, RDS, DynamoDB, ElastiCache, Redshift, OpenSearch) | Identify rightsizing opportunities and reserved capacity recommendations | Instance types, utilization metrics, reservation coverage |
| **Container Cost Tracking** | CloudWatch Logs (Container Insights), ECS/EKS metrics | Attribute costs to containers, pods, and Kubernetes services | Container metrics, pod-level resource usage, cluster information |
| **Resource Discovery** | Organizations, Resource Groups, Resource Explorer, Tagging API | Map resources to teams, applications, and cost centers | Resource tags, account structure, organizational hierarchy |
| **Activity Monitoring** | CloudTrail, Health API, CloudWatch Metrics, Auto Scaling | Track resource lifecycle, usage patterns, and scaling behavior | API activity logs, health events, metric data, scaling configurations |
| **Infrastructure Configuration** | CloudFormation, Service Quotas | Understand resource relationships and service limits | Stack information, resource dependencies, quota usage |
| **Optimization Recommendations** | AWS Optimization Hub, Trusted Advisor | Surface AWS-native cost and performance recommendations | Optimization suggestions, trusted advisor checks, service health |

### AWS Managed Policies Used

CloudZero uses the following AWS-managed policies for broad read-only access:

- **ComputeOptimizerReadOnlyAccess**: Provides access to AWS Compute Optimizer recommendations for rightsizing EC2 instances, Auto Scaling groups, EBS volumes, and Lambda functions
- **ViewOnlyAccess**: AWS-managed policy providing read-only access to most AWS services for comprehensive resource discovery and monitoring
- **CloudWatchReadOnlyAccess**: Read access to CloudWatch metrics, logs, and alarms for performance monitoring and cost attribution
- **AWSBillingReadOnlyAccess**: Read access to billing, cost, and usage data for cost analysis and reporting

### Account Types

CloudZero supports two primary account connection types:

#### Master Payer Account
The AWS account that contains your Cost and Usage Report (CUR) and is the payer for your organization. This account provides:
- Access to detailed billing data via CUR in S3
- Organization-wide cost visibility
- Consolidated billing information
- Typically only one per AWS Organization

#### Resource Owner Account
Member accounts in your AWS Organization that own and run resources. These accounts provide:
- Resource-level cost attribution
- Container and Kubernetes cost tracking
- Activity monitoring and optimization recommendations
- Tagging and resource grouping data

### Security & Privacy

- **Read-Only Access**: All permissions are strictly read-only. CloudZero cannot create, modify, or delete any AWS resources
- **Cross-Account IAM Roles**: Uses AWS best practice cross-account roles with external ID for secure, auditable access
- **No Direct Access**: No SSH keys, API keys, or direct instance access required
- **Encryption**: All data is encrypted in transit (TLS) and at rest
- **Compliance**: CloudZero is SOC 2 Type II certified
- **Data Retention**: Cost data is retained according to your CloudZero subscription agreement

For more information about CloudZero's security practices, visit [cloudzero.com/security](https://www.cloudzero.com/security)

### Deployment Options

This repository provides two deployment methods:

1. **CloudFormation Templates** (Recommended): Located in `services/` directory
   - Automated deployment via AWS CloudFormation
   - Creates IAM roles and policies automatically
   - Supports nested stacks for different account types

2. **Terraform Modules**: Located in `terraform/` directory
   - Infrastructure-as-code deployment
   - Version-controlled IAM configuration
   - Suitable for organizations using Terraform

## Questions? We got answers!
If you have questions or want to report an issue with this template, feel free to open an issue or write to us at support@cloudzero.com
