# git_sync.ps1
# 로컬 변경사항을 커밋하고, 원격의 최신 변경사항을 pull(rebase)한 뒤 push합니다.
# Kiro 작업(턴)이 끝날 때마다 hook을 통해 자동 실행됩니다.

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -Path $repoRoot

# git 저장소인지, 커밋 히스토리가 있는지 확인
$branch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $branch) {
    Write-Output "[git_sync] git 저장소가 아니거나 커밋이 없습니다. 동기화를 건너뜁니다."
    exit 0
}

# 변경사항이 있으면 커밋
$status = git status --porcelain
if ($status) {
    git add -A
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    git commit -m "Auto-sync: $timestamp" | Out-Null
    Write-Output "[git_sync] 변경사항 커밋 완료 ($timestamp)"
} else {
    Write-Output "[git_sync] 커밋할 변경사항 없음"
}

# 원격의 최신 변경사항 반영
git pull --rebase origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Output "[git_sync] git pull 실패 또는 충돌 발생. 수동으로 확인이 필요합니다."
    exit 1
}

# push
git push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Output "[git_sync] git push 실패."
    exit 1
}

Write-Output "[git_sync] 동기화 완료."
