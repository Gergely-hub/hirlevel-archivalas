# Asztali parancsikon: Hírlevél követő — pythonw (exe nélkül)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$mainPy = Join-Path $root "main.py"
$icon = Join-Path $root "app\assets\hirlevel.ico"

$pyw = $null
$candidates = @(
    "$env:LocalAppData\Programs\Python\Python313\pythonw.exe",
    "$env:LocalAppData\Programs\Python\Python314\pythonw.exe",
    "C:\Python314\pythonw.exe"
)
foreach ($c in $candidates) {
    if (Test-Path $c) { $pyw = $c; break }
}
if (-not $pyw -and (Get-Command pythonw -ErrorAction SilentlyContinue)) {
    $pyw = (Get-Command pythonw).Source
}
if (-not $pyw) {
    Write-Error "pythonw nem található. Telepíts Python 3.13-et, vagy futtasd az INSTALL.cmd-t."
}

$desktop = [Environment]::GetFolderPath("Desktop")
$lnkPath = Join-Path $desktop "Hírlevél követő (Python).lnk"

$shell = New-Object -ComObject WScript.Shell
$sc = $shell.CreateShortcut($lnkPath)
$sc.TargetPath = $pyw
$sc.Arguments = "`"$mainPy`""
$sc.WorkingDirectory = $root
if (Test-Path $icon) {
    $sc.IconLocation = "$icon,0"
}
$sc.Description = "Hírlevél követő — forráskódból (pythonw), nem a program\HirlevelKoveto.exe"
$sc.Save()

Write-Host "Parancsikon: $lnkPath"
Write-Host "Indító: $pyw"
