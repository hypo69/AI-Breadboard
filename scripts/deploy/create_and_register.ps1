<#
.SYNOPSIS
  Create GitHub repository (using gh CLI or provided remote) and push current workspace, then attempt to register the project on Read the Docs using API token.

.DESCRIPTION
  This script automates two actions that require your credentials/tools:
  1) Create and push a GitHub repository named by -RepoName using gh CLI (or push to provided remote URL).
  2) Register a project on Read the Docs using READTHEDOCS_API_TOKEN (or -RtdToken parameter) via API.

  The script does NOT store any tokens. You must provide them via environment variables or parameters.

.PARAMETER RepoName
  Repository name to create on GitHub and RTD (default: AI-Breadboard).

.PARAMETER Branch
  Branch to push (default: main).

.PARAMETER RemoteUrl
  Optional explicit remote URL (ssh or https). If provided and gh CLI is not available, the script will set this remote and push.

.PARAMETER RtdToken
  Read the Docs API token. If omitted, the script will use environment variable READTHEDOCS_API_TOKEN.

.EXAMPLE
  ./create_and_register.ps1 -RepoName AI-Breadboard

  Requires: gh CLI (recommended) and git. For RTD registration requires a Read the Docs API token in env READTHEDOCS_API_TOKEN.
#>

param(
	[string]$RepoName = "AI-Breadboard",
	[string]$Branch = "main",
	[string]$RemoteUrl = "",
	[string]$RtdToken = $env:READTHEDOCS_API_TOKEN
)

function ExitWithError($msg) {
	Write-Error $msg
	exit 1
}

Write-Host "Repo name: $RepoName"
Write-Host "Branch: $Branch"

# Ensure we are inside a git repository
$gitRoot = & git rev-parse --show-toplevel 2>$null
if ($LASTEXITCODE -ne 0) {
	ExitWithError "Current directory is not a git repository. Initialize with 'git init' or run from the repo root."
}

# Step 1: Create GitHub repo and push
if (Get-Command gh -ErrorAction SilentlyContinue) {
	Write-Host "Found gh CLI. Creating repository with gh..."
	try {
		& gh repo create $RepoName --public --source=. --remote=origin --push --confirm
		if ($LASTEXITCODE -ne 0) {
			Write-Warning "gh repo create returned non-zero exit code ($LASTEXITCODE). Verify repository state and remote."
		}
	} catch {
		Write-Warning "gh repo create failed: $_"
	}
} else {
	Write-Host "gh CLI not found. Will use git remote if RemoteUrl is provided."
	if (-not [string]::IsNullOrWhiteSpace($RemoteUrl)) {
		Write-Host "Setting remote origin to $RemoteUrl"
		& git remote remove origin 2>$null | Out-Null
		& git remote add origin $RemoteUrl
		& git branch -M $Branch
		& git push -u origin $Branch
		if ($LASTEXITCODE -ne 0) { ExitWithError "git push failed. Check remote and credentials." }
	} else {
		ExitWithError "gh CLI not installed and no RemoteUrl provided. Install gh or provide -RemoteUrl."
	}
}

# If remote not set, try to read origin URL
$remoteUrl = & git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) { $remoteUrl = $null }

if (-not $remoteUrl) {
	Write-Warning "Could not determine remote origin URL. RTD registration may require repository URL."
}

# Step 2: Register project on Read the Docs via API (optional, requires token)
if (-not [string]::IsNullOrWhiteSpace($RtdToken)) {
	Write-Host "Attempting to register project on Read the Docs..."

	$slug = ($RepoName.ToLower() -replace '[^a-z0-9\-]', '-')

	$payload = @{ 
		name = $RepoName
		slug = $slug
	}

	if ($remoteUrl) { $payload.repository = $remoteUrl }
	# Prefer to declare repository type as github; RTD may auto-detect on import
	$payload.repository_type = "github"

	$json = $payload | ConvertTo-Json -Depth 5

	try {
		$response = Invoke-RestMethod -Uri "https://readthedocs.org/api/v3/projects/" -Method Post -Headers @{ Authorization = "Token $RtdToken"; "Content-Type" = "application/json" } -Body $json -ErrorAction Stop
		Write-Host "Read the Docs response:`n$(ConvertTo-Json $response -Depth 5)"
		Write-Host "If response indicates success, the project was created. If RTD requires GitHub app integration, complete import on the web UI or enable the GitHub integration in Read the Docs."
	} catch {
		Write-Warning "RTD API call failed: $_. If you use the Read the Docs GitHub integration, go to https://readthedocs.org/ and Import a Project -> GitHub."
	}
} else {
	Write-Host "No Read the Docs API token provided. Skipping RTD registration. To register automatically, set environment variable READTHEDOCS_API_TOKEN or pass -RtdToken."
}

Write-Host "Done. Verify repository at GitHub and project at Read the Docs."
