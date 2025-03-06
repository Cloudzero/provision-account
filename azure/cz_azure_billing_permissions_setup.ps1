# -*- coding: utf-8 -*-
# Copyright (c) 2016-present, CloudZero, Inc. All rights reserved.
# Licensed under the Apache 2.0 license. See LICENSE file in the project root for full license information.

[CmdletBinding()]
param (
    [Parameter(Mandatory=$true)]
    [string]
    $BillingAccountId,
    # For internal use only
    [Parameter()]
    [switch]
    $DevEnv
)

$resultObject = @{}

$ErrorActionPreference = 'Stop' # Stop if we get any errors

######################################################################################################
# Setup and validate important information
######################################################################################################
$currentUser = Get-AzContext

Write-Debug "AzContext: $(ConvertTo-Json -InputObject $currentUser)"

$currentTenantId = $currentUser.Tenant.Id

$resultObject.TenantId = $currentUser.Tenant.Id

$cloudZeroServicePrincipalName = if ($DevEnv) {"CloudZeroPlatformDev"} else {"CloudZeroPlatform"}
$cloudZeroServicePrincipal = Get-AzADServicePrincipal -DisplayName $cloudZeroServicePrincipalName

if (!$cloudZeroServicePrincipal) {
    throw "Cannot find the Service Principal '$($cloudZeroServicePrincipalName). You must first complete the consent process. See the CloudZero application."
}

Write-Debug "CloudZero SPN: $(ConvertTo-Json -InputObject $cloudZeroServicePrincipal)"
$resultObject.CloudZeroSpnId = $cloudZeroServicePrincipal.Id

$microsoftCustomerAgreement = "MicrosoftCustomerAgreement"
$enterpriseAgreement = "EnterpriseAgreement"
$validAgreementTypes = @($microsoftCustomerAgreement, $enterpriseAgreement)


######################################################################################################
# Get the billing account information and validate it
#
# The CloudZeroPlatform must know what type of agreement is in use as there are differences in how
# cost data is presented in the different agreement types.
######################################################################################################
$billingAccountInfo = if ($BillingAccountId) { (Get-AzBillingAccount -Name $BillingAccountId) } else { (Get-AzBillingAccount) }

Write-Debug "Billing Account: $(ConvertTo-Json -InputObject $billingAccountInfo)"

if ($billingAccountInfo.Length -gt 1) {
    Write-Error $billingAccountInfo
    throw "There are multiple billing accounts. You must select the billing account you are going to monitor on the CloudZero platform."
}

if (!($billingAccountInfo.AgreementType -in $validAgreementTypes)) {
    Write-Error $billingAccountInfo
    throw "Agreement type '$($billingAccountInfo.AgreementType)' is not supported. Supported agreement types: $($validAgreementTypes -join ", "))"
}

$resultObject.BillingAccountName = $billingAccountInfo.DisplayName
$resultObject.BillingAccountId = $billingAccountInfo.Name
$resultObject.AgreementType = $billingAccountInfo.AgreementType


######################################################################################################
# Set read only permissions on the billing account for the CloudZeroPlatform Service Principal
#
# There are some aspects cost data that are not present in the exported data. This includes items like
# taxes and fees. To get these costs, the CloudZeroPlatform Service Principal must have read access
# to the Billing Account (Microsoft Customer Agreement) or the Enrollment Account (Enterprise Agreemeent).
# This read access gives the CloudZero platform access to invoices.
######################################################################################################

$getBillingRoleAssignmentPath = "/providers/Microsoft.Billing/billingAccounts/$($billingAccountInfo.Name)/billingRoleAssignments?api-version=2019-10-01-preview"
$billingReaderRoleId = if ($billingAccountInfo.AgreementType -eq $enterpriseAgreement) {"24f8edb6-1668-4659-b5e2-40bb5f3a7d7e"} else {"50000000-aaaa-bbbb-cccc-100000000002"}
$billingReaderRoleDefinitionId = "/providers/Microsoft.Billing/billingAccounts/$($billingAccountInfo.Name)/billingRoleDefinitions/$($billingReaderRoleId)"

$billingRoleAssignmentsResult = Invoke-AzRestMethod -Path $getBillingRoleAssignmentPath -Method GET

$addBillingReaderRole = $true

# First check to see if the service principal has already been assigned the reader role
if ($billingRoleAssignmentsResult) {
    $billingRoleAssignments = ConvertFrom-Json -InputObject $billingRoleAssignmentsResult.Content
    Write-Debug "Checking Billing Role Assigment: $(ConvertTo-Json -InputObject $billingRoleAssignments.value)"
    foreach ($billingRoleAssignment in $billingRoleAssignments.value) {
        if ($billingRoleAssignment.properties.principalId -eq $cloudZeroServicePrincipal.Id `
            -and $billingRoleAssignment.properties.principalTenantId -eq $currentTenantId `
            -and $billingRoleAssignment.properties.roleDefinitionId -eq $billingReaderRoleDefinitionId) {
            $addBillingReaderRole = $false
            Write-Host "Billing reader role is already assigned to $($cloudZeroServicePrincipal.DisplayName) service principal."
        }
    }
}

# If we have not found the correct role assignment, then assign the role. The API to assign the role is different for EA and MCA accounts
if ($addBillingReaderRole) {
    if ($billingAccountInfo.AgreementType -eq $enterpriseAgreement) {
        $billingRoleAssignmentId = (New-Guid).Guid
        $putBillingRoleAssignmentPath = "/providers/Microsoft.Billing/billingAccounts/$($billingAccountInfo.Name)/billingRoleAssignments/$($billingRoleAssignmentId)?api-version=2019-10-01-preview"

        $props = @{
            properties = @{
                principalId = $cloudZeroServicePrincipal.Id
                principalTenantId = $currentTenantId
                roleDefinitionId = $billingReaderRoleDefinitionId
            }
        }
    
        $result = Invoke-AzRestMethod -Path $putBillingRoleAssignmentPath -Method PUT -Payload (ConvertTo-Json -InputObject $props)

        if (!($result.StatusCode -lt 300)) {
            Write-Error $result
            throw "A failure occurred assigning billing reader access to CloudZero service principal."
        }

    } else {
        $postBillingRoleAssignmentPath = "/providers/Microsoft.Billing/billingAccounts/$($billingAccountInfo.Name)/createBillingRoleAssignment?api-version=2019-10-01-preview"

        $props = @{
            properties = @{
                principalId = $cloudZeroServicePrincipal.Id
                roleDefinitionId = $billingReaderRoleDefinitionId
            }
        }

        $result = Invoke-AzRestMethod -Path $postBillingRoleAssignmentPath -Method POST -Payload (ConvertTo-Json -InputObject $props)

        if (!($result.StatusCode -lt 300)) {
            Write-Error $result
            throw "A failure occurred assigning billing reader access to $($cloudZeroServicePrincipal.DisplayName) service principal."
        }
        else {
            Write-Host "Added read only permissions for the billing account to $($cloudZeroServicePrincipal.DisplayName) service principal."
        }
    }
}

$resultObject.BillingReaderRoleAdded = $true

Write-Output $resultObject