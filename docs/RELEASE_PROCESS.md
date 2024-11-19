# Release Process

This guide outlines the steps and best practices for managing releases in the repository. Following this process ensures consistency, quality, and clear communication with all stakeholders, including necessary external approvals.

## Overview

1. **Create Release Document**
2. **Submit Pull Request (PR)**
3. **Review and Merge**
4. **Trigger Manual Release Workflow**
5. **Obtain External Approvals**
6. **Publish Release**

---

## Step-by-Step Process

### 1. Create a New Release Document

- **Location:** [docs/releases](.)
- **Filename Format:** `X.X.X.md` (e.g., `1.2.3.md`)
- **Template:** Use the provided [Release Notes Template](#release-notes-template) below.

**Instructions:**

- Duplicate the release notes template.
- Replace placeholders with the appropriate version number and details.
- Save the file with the correct naming convention in the `docs/releases` folder.

### 2. Open a Pull Request (PR)

- **Target Branch:** `develop`
- **PR Title:** `Release X.X.X - [Brief Description]`
  
**Automations:**

- Opening a PR will automatically notify the stakeholder teams for review.

### 3. Review and Merge the PR

- **Stakeholders:** Not Found
- **Approval:** Obtain necessary approvals from the reviewers.
- **Merge:** Once approved, merge the release notes PR into the `develop` branch.

### 4. Trigger the Manual Release Workflow

- **Workflow Link:** [Release](https://github.com/provision-account/actions/workflows/release.yml)
  
**Purpose:**

- Ensures stakeholders review the functionality and public-facing documentation before publishing.
- **External Approvals Required:** Designated stakeholders must manually approve the release.

**Steps:**

1. Navigate to the **Actions** tab in your repository.
2. Select the **Manual Release** workflow.
3. Trigger the workflow and follow any on-screen instructions.
4. **Await Stakeholder Approval:** Stakeholders will receive a notification to review and approve the release.

### 5. (Optional) Obtain External Approvals

- **Stakeholders Involved:** PM Team, Documentation Team, and any other designated external parties.
- **Approval Process:**
  - Stakeholders review the functionality, documentation, and overall release readiness.
  - Upon satisfaction, stakeholders provide manual approval through the workflow interface.

### 6. Publish the Release

- Once the manual release workflow is approved and completed, the release will be published.
- Stakeholders will be notified upon successful publication.

---

## Creating Release Notes

Effective release notes provide clear and concise information about the changes in each release. Follow these guidelines to create comprehensive release notes.

### Pro-Tip

- **Review Changes:** Examine the GitHub diff between the previous and current release to identify all changes.
- **Commit Messages:** Use commit titles to outline the changes and categorize them appropriately. Include a link to the relevant commit where possible.

### Release Notes Structure

Use the following sections to organize your release notes:

1. **Upgrade Steps**
2. **Breaking Changes**
3. **New Features**
4. **Bug Fixes**
5. **Improvements**
6. **Other Changes**

#### Upgrade Steps

- **Purpose:** Detail any actions users must take to upgrade beyond updating dependencies.
- **Content:**
  - Step-by-step instructions for the upgrade.
  - Pseudocode or code snippets highlighting necessary changes.
  - Recommendations to upgrade due to known issues in older versions.
- **Note:** Ideally, no upgrade steps are required.

#### Breaking Changes

- **Purpose:** List all breaking changes that may affect users.
- **Content:**
  - Comprehensive list of changes that are not backward compatible.
  - Typically included in major version releases.
- **Note:** Aim to minimize breaking changes.

#### New Features

- **Purpose:** Describe new functionalities introduced in the release.
- **Content:**
  - Detailed descriptions of each new feature.
  - Usage scenarios and benefits.
  - Include screenshots or diagrams where applicable.
  - Mention any caveats, warnings, or if the feature is in beta.

#### Bug Fixes

- **Purpose:** Highlight fixes for existing issues.
- **Content:**
  - Description of the issues that have been resolved.
  - Reference to related features or functionalities.

#### Improvements

- **Purpose:** Outline enhancements made to existing features or workflows.
- **Content:**
  - Performance optimizations.
  - Improved logging or error messaging.
  - Enhancements to user experience.

#### Other Changes

- **Purpose:** Capture miscellaneous changes that do not fit into the above categories.
- **Content:**
  - Minor updates or maintenance tasks.
  - Documentation updates.
- **Note:** Aim to keep this section empty by categorizing changes appropriately.

---

### Release Notes Template

Copy and paste the following template to create your release notes. Replace placeholders with relevant information.

```markdown
## [X.X.X](https://github.com/provision-account/compare/Y.Y.Y...X.X.X) (YYYY-MM-DD)

> Brief description of the release.

### Upgrade Steps
* [ACTION REQUIRED]
* Detailed upgrade instructions or steps.

### Breaking Changes
* Description of breaking change 1.
* Description of breaking change 2.

### New Features
* **Feature Name:** Detailed description, usage scenarios, and any relevant notes or images.
* **Feature Name:** Detailed description, usage scenarios, and any relevant notes or images.

### Bug Fixes
* **Bug Fix Description:** Explanation of the issue and how it was resolved.
* **Bug Fix Description:** Explanation of the issue and how it was resolved.

### Improvements
* **Improvement Description:** Details about the enhancement.
* **Improvement Description:** Details about the enhancement.

### Other Changes
* **Change Description:** Brief explanation of the change.
* **Change Description:** Brief explanation of the change.
```

**Example:**

Examples can be found in the [docs/releases](https://github.com/provision-account/tree/main/docs/releases) folder.

---

## Best Practices

- **Consistency:** Maintain a consistent format and structure across all release notes.
- **Clarity:** Use clear and concise language to describe changes.
- **Categorization:** Properly categorize changes to make it easier for users to find relevant information.
- **Visual Aids:** Include screenshots or diagrams for new features to enhance understanding.
- **Review:** Ensure all sections are thoroughly reviewed by relevant teams before publishing.
- **Highlight External Approvals:** Clearly indicate when external approvals are required and obtained.

---

## Roles and Responsibilities

- **Developer:** Drafts the release notes using the provided template.
- **Product Management (PM) Team:** Reviews and approves the release notes for accuracy and completeness.
- **Documentation Team:** Ensures that the release notes are well-documented and user-friendly.
- **Stakeholders:** Review and provide external approval for the release through the Manual Release workflow.
- **Release Manager:** Oversees the release process, ensuring all steps, including external approvals, are completed.

---

## External Approvals

External approvals are a critical part of the release process to ensure that all stakeholders are aligned and that the release meets quality and functionality standards.

### Approval Workflow

1. **Initiate Approval:**
   - After triggering the Manual Release workflow, stakeholders receive a notification to review the release.

2. **Review Process:**
   - Stakeholders evaluate the functionality, documentation, and overall readiness of the release.
   - Any feedback or required changes are communicated back to the release manager or developer.

3. **Provide Approval:**
   - Once satisfied, stakeholders provide manual approval within the workflow interface.
   - The release process proceeds to publication upon receiving all necessary approvals.

4. **Handling Rejections:**
   - If a stakeholder rejects the release, the release manager must address the feedback and possibly iterate on the release notes or code before resubmitting for approval.

**Note:** The release cannot be published until all required external approvals are obtained.

---

## FAQs

**Q: What if there are no changes for a minor release?**
A: Even if there are no significant changes, create a release document indicating that it is a maintenance or patch release.

**Q: How often should releases be made?**
A: Follow the project's release cadence, whether it's weekly, bi-weekly, monthly, etc., to ensure regular updates.

**Q: Who approves the final release?**
A: Designated stakeholders must manually approve the release through the Manual Release workflow.

**Q: What happens if external approvals are not obtained in a timely manner?**
A: Communicate with stakeholders to address any blockers and ensure that the release schedule accommodates the approval process.
