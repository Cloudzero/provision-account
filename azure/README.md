# CloudZero Azure Billing API Access Script

The [cz_azure_billing_permissions_setup.ps1](./cz_azure_billing_permissions_setup.ps1) PowerShell script grants CloudZero the necessary **read-only** permissions to connect to your Azure Enterprise Agreement (EA) or Microsoft Customer Agreement (MCA) account.

It automates "Step 4: Grant Access to the Azure Billing API" in the CloudZero [EA](https://docs.cloudzero.com/docs/connections-azure-ea#step-4-grant-access-to-the-azure-billing-api) and [MCA](https://docs.cloudzero.com/docs/connections-azure-mca#step-4-grant-access-to-the-azure-billing-api) documentation by:

1. Validating your billing account ID.
2. Determining your Azure agreement type (EA or MCA).
3. Setting up read-only [EnrollmentReader](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/assign-roles-azure-service-principals#permissions-that-can-be-assigned-to-the-service-principal) permissions for the CloudZero service principal.

## Prerequisites

- [Azure PowerShell](https://learn.microsoft.com/en-us/powershell/azure/what-is-azure-powershell) installed:
  - Locally on any platform
  - Via [Azure Cloud Shell](https://shell.azure.com/)
  - Using a [Docker container](https://learn.microsoft.com/en-us/powershell/azure/azureps-in-docker)
- Azure user with permissions to assign the `EnrollmentReader` role at the billing account scope
- Your Azure [billing account ID (8-digit number)](#finding-your-billing-account-id)
- Completed Steps 1-3 of the CloudZero connection process:
  - [EA accounts documentation](https://docs.cloudzero.com/docs/connections-azure-ea)
  - [MCA accounts documentation](https://docs.cloudzero.com/docs/connections-azure-mca)

### Finding Your Billing Account ID

1. Go to [Cost Management + Billing](https://portal.azure.com/#view/Microsoft_Azure_GTM/ModernBillingMenuBlade/~/BillingAccounts) in the Azure Portal.
2. Select your billing account.
3. Navigate to **Settings > Properties**.
4. Copy the 8-digit **Billing Account ID**.

## Usage Instructions

1. Log in to Azure PowerShell:

   ```powershell
   Connect-AzAccount
   ```

2. Navigate to the directory containing the script.

3. Run the script with your billing account ID:

   ```powershell
   ./cz_azure_billing_permissions_setup.ps1 -billingaccountId <billing_account_id>
   ```

> **Important**: Execute the script as a whole file. Do not copy and paste individual lines.

## Verification

Check your new Azure connection in CloudZero's [Billing Connections table](https://app.cloudzero.com/organization/connections). The connection status will change from **Pending Data** to **Healthy** after the first data ingest (may take several hours).

## Documentation Links

- [EA Connection Documentation](https://docs.cloudzero.com/docs/connections-azure-ea)
- [MCA Connection Documentation](https://docs.cloudzero.com/docs/connections-azure-mca)
- [Azure Service Principal Permissions](https://learn.microsoft.com/en-us/azure/cost-management-billing/manage/assign-roles-azure-service-principals#permissions-that-can-be-assigned-to-the-service-principal)
