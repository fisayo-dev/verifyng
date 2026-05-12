# Sync backend/ to .hf-publish/ and push to Hugging Face
# Usage: .\sync-to-hf.ps1

Write-Host "Starting sync from backend/ to .hf-publish/" -ForegroundColor Cyan

$backendPath = ".\backend"
$hfPath = ".\.hf-publish"

# Check if paths exist
if (-not (Test-Path $backendPath)) {
    Write-Host "ERROR: backend/ folder not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $hfPath)) {
    Write-Host "ERROR: .hf-publish/ folder not found" -ForegroundColor Red
    exit 1
}

try {
    # Define files/patterns to exclude from sync
    $excludePatterns = @(".git", "*.jpg", "*.png", "*.jpeg", "*.gif", "*.zip", "__pycache__", ".env", "*.pyc")
    
    # Copy files from backend to .hf-publish (excluding .git and binary files)
    Write-Host "Copying files..." -ForegroundColor Yellow
    Get-ChildItem -Path $backendPath -Exclude $excludePatterns | ForEach-Object {
        if ($_.PSIsContainer) {
            $destination = "$hfPath\$($_.Name)"
            if (-not (Test-Path $destination)) {
                New-Item -ItemType Directory -Path $destination | Out-Null
            }
            Copy-Item -Path "$($_.FullName)\*" -Destination $destination -Recurse -Force
        } else {
            Copy-Item -Path $_.FullName -Destination "$hfPath\$($_.Name)" -Force
        }
    }
    
    # Get current branch from backend repo BEFORE changing directory
    $currentBranch = git rev-parse --abbrev-ref HEAD
    
    # Git commit and push in .hf-publish
    Push-Location $hfPath
    
    Write-Host "Files copied. Checking git status..." -ForegroundColor Yellow
    $gitStatus = git status --porcelain
    
    if ($gitStatus) {
        Write-Host "Staging changes..." -ForegroundColor Yellow
        git add .
        
        $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "Committing to Hugging Face..." -ForegroundColor Yellow
        git commit -m "Sync from backend [$timestamp]"
        
        # Always push to main on Hugging Face (HF only has main branch)
        Write-Host "Pushing to Hugging Face (main branch)..." -ForegroundColor Yellow
        git push origin main
        
        Write-Host "Sync complete! Changes pushed to Hugging Face" -ForegroundColor Green
    } else {
        Write-Host "No changes to sync" -ForegroundColor Cyan
    }
    
    Pop-Location
    
} catch {
    Write-Host "Error during sync: $_" -ForegroundColor Red
    exit 1
}
