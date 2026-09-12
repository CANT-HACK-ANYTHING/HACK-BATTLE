# AegisOS :: Git Sync & GitHub Deployment Script
param (
    [string]$RepoUrl = ""
)

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  AEGIS-OS :: GITHUB REPOSITORY SYNC & DEPLOYMENT" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Find Git executable
$gitCmd = "git"
$gitFound = $false
try {
    $ver = & git --version 2>$null
    if ($ver) { $gitFound = $true }
} catch {}

if (-not $gitFound) {
    $possiblePaths = @(
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe",
        "C:\Users\Piyush\AppData\Local\Programs\Git\cmd\git.exe"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) {
            $gitCmd = $p
            $gitFound = $true
            break
        }
    }
}

if (-not $gitFound) {
    Write-Host "[-] Git is currently being installed or not found in PATH." -ForegroundColor Yellow
    Write-Host "    Please wait for the installer to finish, then rerun this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "[+] Using Git: $gitCmd" -ForegroundColor Green

# 1. Git Init
if (-not (Test-Path ".git")) {
    Write-Host "[*] Initializing local Git repository..." -ForegroundColor Cyan
    & $gitCmd init -b main
} else {
    Write-Host "[+] Local Git repository already initialized." -ForegroundColor Green
}

# 2. Stage files
Write-Host "[*] Staging files for commit..." -ForegroundColor Cyan
& $gitCmd add .

# 3. Commit
Write-Host "[*] Creating commit..." -ForegroundColor Cyan
& $gitCmd commit -m "feat(hackbattle): AegisOS autonomous operator mission control & HUD" 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Commit created successfully." -ForegroundColor Green
} else {
    Write-Host "[*] No new changes to commit." -ForegroundColor DarkGray
}

# 4. Remote Origin
$remotes = & $gitCmd remote -v 2>$null
if (-not $remotes) {
    if (-not $RepoUrl) {
        Write-Host ""
        Write-Host "Enter your GitHub repository URL" -ForegroundColor Yellow
        Write-Host "Example: https://github.com/Piyush/HackBattle.git" -ForegroundColor DarkGray
        $RepoUrl = Read-Host "GitHub Repo URL"
    }
    if ($RepoUrl) {
        & $gitCmd remote add origin $RepoUrl
        Write-Host "[+] Added remote origin: $RepoUrl" -ForegroundColor Green
    }
} else {
    Write-Host "[+] Remote origin is configured:" -ForegroundColor Green
    Write-Host $remotes -ForegroundColor DarkGray
}

# 5. Push
Write-Host ""
Write-Host "To push your changes to GitHub, run:" -ForegroundColor Cyan
Write-Host "  $gitCmd push -u origin main" -ForegroundColor White
Write-Host ""
