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
| **Cost & Billing Analysis** | S3 (CUR), BCM Data Exports (CUR 2.0 / FOCUS), Cost Explorer, Billing, Pricing, Billing Conductor, Budgets, Invoicing, Payments, Purchase Orders, MAP Credits, Free Tier, Tax, Sustainability | Analyze AWS spending and generate cost intelligence reports | Cost and Usage Report data, billing details, budgets and forecasts, invoices, pricing and scenario estimates, carbon footprint summary |
| **Compute Optimization** | Compute Optimizer, Reserved Instances (EC2, RDS, DynamoDB, ElastiCache, Redshift, OpenSearch), Savings Plans | Identify rightsizing opportunities, reserved capacity, and savings plan recommendations | Instance types, utilization metrics, reservation coverage, savings plan utilization |
| **Container Cost Tracking** | CloudWatch Logs (Container Insights), ECS/EKS metrics | Attribute costs to containers, pods, and Kubernetes services | Container metrics, pod-level resource usage, cluster information |
| **Resource Discovery** | Organizations, Resource Groups, Resource Explorer, Tagging API | Map resources to teams, applications, and cost centers | Resource tags, account structure, organizational hierarchy |
| **Activity Monitoring** | CloudTrail, Health API, CloudWatch Metrics, Auto Scaling | Track resource lifecycle, usage patterns, and scaling behavior | API activity logs, health events, metric data, scaling configurations |
| **Infrastructure Configuration** | CloudFormation, Service Quotas | Understand resource relationships and service limits | Stack information, resource dependencies, quota usage |
| **Optimization Recommendations** | AWS Cost Optimization Hub, Trusted Advisor, AWS Health | Surface AWS-native cost and performance recommendations | Optimization suggestions, Trusted Advisor checks, service health events |

### Data Access Scope

CloudZero's access is bounded to your cost and usage surface. The majority of what CloudZero analyzes is derived from your AWS Cost and Usage Report (CUR), which contains the authoritative record of what AWS charged you, for what resources, under what tags and cost categories.

**No permission granted to CloudZero reads the contents of your resources.** CloudZero cannot read S3 object bodies (other than the CUR files you explicitly share), database records, application logs, secrets, EC2 instance disks, or any customer workload data. All granted actions return configuration metadata, usage metrics, billing data, or AWS-generated recommendations.

Where permissions reach beyond what's in the CUR, each one exists for a specific cost-intelligence reason:

| Area | Data accessed (beyond CUR) | Why CloudZero needs it |
|---|---|---|
| **Billing account metadata** (`account`, `billing`, `consolidatedbilling`, `freetier`, `invoicing`, `payments`, `tax`) | Your account contact info, billing preferences, invoice records, payment methods, tax registrations, free-tier status | Invoices include EDP credits and other adjustments the raw CUR does not reflect. Free-tier status and payment/tax settings are your own billing configuration — read so CloudZero can reconcile invoiced cost with CUR line items. |
| **Alternative CUR delivery** (`bcm-data-exports:Get*/List*`) | Data export configurations for CUR 2.0 and FOCUS-format exports | AWS is moving customers from the classic CUR to BCM Data Exports (CUR 2.0, FOCUS). Read access here lets CloudZero discover and ingest whichever export format a customer is on. |
| **Purchase orders, MAP credits, carbon footprint** (`purchase-orders`, `mapcredits`, `sustainability:Get*`) | Your enterprise purchase orders, Migration Acceleration Program credit balances, monthly carbon footprint summary | Purchase orders align invoices with customer procurement processes. MAP credits show up as CUR adjustments — the describe APIs show the underlying program enrollment. Carbon footprint is AWS's account-level sustainability summary, used for ESG reporting alongside cost. |
| **Budgets** (`budgets:Describe*/View*`) | Budgets you've configured in AWS and their alert thresholds | Lets CloudZero surface your existing AWS Budgets alongside its own cost analysis. Read-only — CloudZero cannot create, modify, or delete your budgets. |
| **Reserved Instance & Savings Plan details** (`*:DescribeReserved*`, `savingsplans:*`) | Terms, expirations, and configuration of RIs and Savings Plans you own | CUR shows applied RI/SP coverage per line item. The describe APIs surface upcoming expirations and commitment details needed for renewal planning and coverage analysis. All data is about financial instruments your account already owns. |
| **Pricing catalog and scenario modeling** (`pricing:*`, `bcm-pricing-calculator:Get*/List*`) | Public AWS list prices; the customer's saved AWS Pricing Calculator workload estimates | Pricing data is publicly published by AWS. Calculator estimates are what-if scenarios you've already saved in your own account. Together they let CloudZero model cost changes that the realized prices in your CUR cannot answer on their own. |
| **Billing Conductor** (`billingconductor:Get*/List*`) | Your configured pro-forma billing groups, pricing plans, and rules | For enterprise customers using AWS Billing Conductor for internal chargeback, these APIs expose the billing-group structure needed to mirror the same showback/chargeback view inside CloudZero. Read-only — cannot alter your billing groups. |
| **Organizations & live tagging** (`organizations`, `tag`, `resource-groups`, `resource-explorer`, `account:ListRegions`) | Your organization hierarchy (OUs, accounts, service control policies), live resource tags, custom resource groups, enabled regions | CUR records account IDs and tags at the time of billing. The live APIs add real-time organizational hierarchy and up-to-the-minute tag state for timely showback and chargeback. Metadata only — no resource contents. |
| **AWS-generated recommendations** (`compute-optimizer`, `cost-optimization-hub`, `support:DescribeTrustedAdvisor*`, `health:Describe*`) | Rightsizing recommendations, optimization hub recommendations, Trusted Advisor checks, service health events affecting your account | These AWS services exist specifically to analyze your account and produce cost, performance, and availability recommendations. CloudZero surfaces those recommendations alongside its own CUR-derived analysis so you have a consolidated view. |
| **CloudWatch utilization metrics** (`cloudwatch`, `autoscaling:Describe*`) | Utilization metrics (CPU, memory, network, scaling events) | CUR records what you were charged for (e.g., instance-hours); it does not record how hard the resource was being used. Rightsizing and anomaly detection require utilization signal. Metric data only — no log contents. |
| **Container Insights logs** (`logs:*` scoped to `/aws/containerinsights/*`, plus log-group discovery and query-result retrieval) | Pod- and container-level usage metrics emitted by the Container Insights agent | CUR attributes cost to an EKS/ECS cluster; Kubernetes cost allocation requires pod-level granularity, which this log-group provides. Access is scoped to Container Insights log groups only. |
| **CloudTrail** (`cloudtrail:Describe/Get/List/LookupEvents`) | Read-only API activity events (who made which API call, when) | When a cost shifts unexpectedly, CloudTrail answers "what changed and who changed it." Metadata about API calls — not the data those calls returned. |
| **Service Quotas** (`servicequotas`) | Current service limits and applied-quota values | Approaching a quota can change cost shape (e.g., scaling behavior). Account configuration metadata. |
| **CloudFormation** (`cloudformation:Describe/Get/List`) | Stack composition and which resources belong to which stack | Enables stack-level cost rollups and dependency mapping; CUR records per-resource cost but not stack grouping. |
| **IAM self-inspection** (`iam:GetRole`, `iam:GetRolePolicy`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`, `iam:ListRoleTags`, `iam:SimulatePrincipalPolicy` scoped to `role/cloudzero/*`; `iam:GetPolicy`, `iam:GetPolicyVersion` scoped to the four AWS managed policies CloudZero attaches) | CloudZero's own cross-account role and the policy documents attached to it | Transparency: CloudZero can show you exactly what access has been granted, which managed policies are attached, and the contents of those specific policies. Useful during audits and permission reviews. Role actions are scoped to `role/cloudzero/*`; `iam:GetPolicy`/`GetPolicyVersion` is scoped to exactly `AWSBillingReadOnlyAccess`, `CloudWatchReadOnlyAccess`, `ComputeOptimizerReadOnlyAccess`, and `ViewOnlyAccess` — no access to any other policy documents in your account. |

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

**Important**: CloudZero requires an HOURLY Cost and Usage Report. Daily reports are not supported.

#### Resource Owner Account
Member accounts in your AWS Organization that own and run resources. These accounts provide:
- Resource-level cost attribution
- Container and Kubernetes cost tracking
- Activity monitoring and optimization recommendations
- Tagging and resource grouping data

### Security & Privacy

- **Read-Only Access**: All permissions are strictly read-only. CloudZero cannot create, modify, or delete any AWS resources
- **Cross-Account IAM Roles**: Uses AWS best practice cross-account roles with external ID for secure, auditable access
- **Transparent Self-Inspection**: CloudZero reads its own role and attached policies so you can see exactly what access has been granted — useful during audits and permission reviews
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
