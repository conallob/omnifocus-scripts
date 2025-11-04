# Claude GitHub Actions Setup

This repository uses [Claude Code Action](https://github.com/anthropics/claude-code-action) to provide AI-powered automation for issues and pull requests.

## Workflows

### 1. Claude Assistant (`claude-assistant.yml`)

The main interactive assistant that responds to:
- Issue comments with `@claude` mentions
- Pull request review comments
- New issues (opened, assigned, or labeled)
- Pull request reviews

**Use cases:**
- Ask Claude questions about the codebase
- Request code explanations or implementations
- Get help with debugging
- Discuss architectural decisions

### 2. Claude PR Review (`claude-pr-review.yml`)

Automatically reviews pull requests for:
- Code quality and best practices
- Potential bugs or issues
- Security concerns
- Documentation completeness
- Test coverage

This workflow runs automatically when a PR is opened or updated.

## Setup Instructions

### Quick Setup (Recommended)

The easiest way to set up Claude GitHub Actions is through Claude Code:

1. Open the `claude` terminal application
2. Run `/install-github-app`
3. Follow the guided setup process

This will automatically configure your GitHub app and repository secrets.

### Manual Setup

If you prefer to set up manually:

#### 1. Get an Anthropic API Key

1. Sign up at [Anthropic Console](https://console.anthropic.com/)
2. Create an API key from your account settings
3. Copy the API key (starts with `sk-ant-api03-...`)

#### 2. Add Repository Secret

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ANTHROPIC_API_KEY`
5. Value: Paste your API key
6. Click **Add secret**

#### 3. Enable Workflow Permissions

1. Go to **Settings** → **Actions** → **General**
2. Under "Workflow permissions", select **Read and write permissions**
3. Check **Allow GitHub Actions to create and approve pull requests**
4. Click **Save**

## Usage

### Interactive Mode

Mention Claude in any issue or PR comment:

```
@claude can you help me understand how this script works?
```

```
@claude please review the error handling in this PR
```

### Automatic Reviews

The PR review workflow runs automatically. To customize the review criteria, edit the `prompt` section in `.github/workflows/claude-pr-review.yml`.

## Advanced Configuration

### Custom Prompts

You can create additional workflows for specific automation tasks. Example:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    prompt: |
      Update the documentation to reflect changes in this PR.
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Claude Code SDK Arguments

Use `claude_args` to pass additional parameters:

```yaml
claude_args: |
  --model claude-sonnet-4-5-20250929
  --max-turns 10
  --system-prompt "Follow our coding standards"
```

### Path-Specific Automation

Trigger workflows only when specific files change:

```yaml
on:
  pull_request:
    paths:
      - "src/**/*.js"
      - "lib/**/*.js"
```

## Alternative Authentication Methods

### AWS Bedrock

Instead of `anthropic_api_key`, configure AWS credentials:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    aws_access_key_id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws_secret_access_key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws_region: us-east-1
```

### Google Vertex AI

Configure GCP service account credentials:

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    gcp_service_account_key: ${{ secrets.GCP_SERVICE_ACCOUNT_KEY }}
    gcp_project_id: your-project-id
```

## Troubleshooting

### Action not responding

1. Verify `ANTHROPIC_API_KEY` is set correctly
2. Check workflow permissions are enabled
3. Review the Actions log for error messages

### Permission errors

Ensure the workflow has these permissions:

```yaml
permissions:
  contents: write
  issues: write
  pull-requests: write
```

### Rate limits

If you hit rate limits, consider:
- Using `--max-turns` to limit action complexity
- Implementing branch protections to reduce automated reviews
- Upgrading your Anthropic API plan

## Resources

- [Claude Code Action GitHub](https://github.com/anthropics/claude-code-action)
- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/github-actions)
- [Anthropic Console](https://console.anthropic.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Support

For issues or questions:
- GitHub Issues: [anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/issues)
- Anthropic Support: [support.anthropic.com](https://support.anthropic.com)
