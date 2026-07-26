# git_sync.ps1
# Commits local changes, pulls the latest changes from origin (rebase), then pushes.
# Runs automatically via a Kiro hook when an agent turn finishes.

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $repoRoot

# Check this is a git repo with at least one commit
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) {
    Write-Output "[git_sync] Not a git repo or no commits yet. Skipping sync."
    exit 0
}

# Commit local changes if any
$status = git status --porcelain
if ($status) {
    git add -A
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Auto-sync: $timestamp" | Out-Null
    Write-Output "[git_sync] Committed local changes ($timestamp)"
} else {
    Write-Output "[git_sync] No local changes to commit"
}

# Pull latest changes from origin
git pull --rebase origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Output "[git_sync] git pull failed or conflict occurred. Manual check needed."
    exit 1
}

# Push
git push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Output "[git_sync] git push failed."
    exit 1
}

Write-Output "[git_sync] Sync complete."
