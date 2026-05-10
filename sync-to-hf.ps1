# Sync backend/ to .hf-publish/ and push to Hugging Face
# Usage: .\sync-to-hf.ps1

Write-Host "🔄 Starting sync from backend/ to .hf-publish/" -ForegroundColor Cyan

$backendPath = ".\backend"
$hfPath = ".\.hf-publish"

# Check if paths exist
if (-not (Test-Path $backendPath)) {
    Write-Host "❌ backend/ folder not found" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $hfPath)) {
    Write-Host "❌ .hf-publish/ folder not found" -ForegroundColor Red
    exit 1
}

try {
    # Copy files from backend to .hf-publish (excluding .git)
    Write-Host "📋 Copying files..." -ForegroundColor Yellow
    Get-ChildItem -Path $backendPath -Exclude ".git" | ForEach-Object {
        if ($_.PSIsContainer) {
            Copy-Item -Path $_.FullName -Destination "$hfPath\$($_.Name)" -Recurse -Force
        } else {
            Copy-Item -Path $_.FullName -Destination "$hfPath\$($_.Name)" -Force
        }
    }
    
    # Git commit and push in .hf-publish
    Push-Location $hfPath
    
    Write-Host "✅ Files copied. Checking git status..." -ForegroundColor Yellow
    $gitStatus = git status --porcelain
    
    if ($gitStatus) {
        Write-Host "📝 Staging changes..." -ForegroundColor Yellow
        git add .
        
        $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        Write-Host "💾 Committing to Hugging Face..." -ForegroundColor Yellow
        git commit -m "Sync from backend [$timestamp]"
        
        Write-Host "🚀 Pushing to Hugging Face..." -ForegroundColor Yellow
        git push origin main
        
        Write-Host "✨ Sync complete! Changes pushed to Hugging Face" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  No changes to sync" -ForegroundColor Cyan
    }
    
    Pop-Location
    
} catch {
    Write-Host "❌ Error during sync: $_" -ForegroundColor Red
    exit 1
}
