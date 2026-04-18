<#
.SYNOPSIS
    Unified runner-ops tool for OCR self-hosted GitHub Actions runners.

.DESCRIPTION
    Single entry point for every runner lifecycle operation. Conforms to
    OCR_STANDARD_selfHostedRunners.md. All subcommands are idempotent
    where correctness permits, non-interactive, and return proper exit
    codes — safe for scripted automation.

.PARAMETER Command
    install  — install a new runner (fresh download + register + service + start)
    convert  — retrofit an existing interactive runner to a Windows service
    start    — start an existing runner service
    stop     — stop an existing runner service
    restart  — stop + start a runner service
    status   — list all OCR runners + their state (read-only, always safe)
    retire   — stop + uninstall service + deregister from GitHub + delete dir

.PARAMETER Name
    Runner name (e.g. BLOODRAVEN, BLOODRAVEN-2). Required for convert /
    start / stop / restart / retire. Derived from -Number for install.
    Convention: BLOODRAVEN -> actions-runner/, BLOODRAVEN-<N> -> actions-runner-<N>/.

.PARAMETER Number
    Runner index for install. 2 for BLOODRAVEN-2, 3 for BLOODRAVEN-3.
    The unnumbered BLOODRAVEN is never created by `install` (it was
    the original seed runner).

.PARAMETER RegistrationToken
    Short-lived org registration token for install. Generate via:
        gh api orgs/ourCommunityRituals/actions/runners/registration-token -X POST --jq .token

.PARAMETER RemovalToken
    Short-lived org removal token for retire. Generate via:
        gh api orgs/ourCommunityRituals/actions/runners/remove-token -X POST --jq .token

.PARAMETER RunnerGroup
    Org-level runner group. Defaults to ocr-default.

.PARAMETER Labels
    Comma-separated labels. Defaults to self-hosted,windows,ocr-default.

.PARAMETER OcrRoot
    OCR workspace root. Defaults to C:\Users\mzdan\dev\ourCommunityRituals.

.PARAMETER Force
    For retire: skip confirmation prompt. No effect on other subcommands.

.PARAMETER Json
    Status output as JSON instead of formatted table. Useful for automation.

.EXAMPLE
    # Install BLOODRAVEN-2 as a Windows service from scratch
    $token = gh api orgs/ourCommunityRituals/actions/runners/registration-token -X POST --jq .token
    .\runner.ps1 install -Number 2 -RegistrationToken $token

.EXAMPLE
    # Retrofit the existing interactive BLOODRAVEN to a Windows service
    .\runner.ps1 convert -Name BLOODRAVEN

.EXAMPLE
    # Check health across all OCR runners (read-only)
    .\runner.ps1 status

.EXAMPLE
    # Retire BLOODRAVEN-3 (stop + uninstall + deregister + delete dir)
    $removal = gh api orgs/ourCommunityRituals/actions/runners/remove-token -X POST --jq .token
    .\runner.ps1 retire -Name BLOODRAVEN-3 -RemovalToken $removal -Force

.NOTES
    Canonical path: OCR-docs/shared/runner.ps1
    Requires: PowerShell 5+, local admin (for service operations).
    Rejects OneDrive paths per feedback_no_onedrive_paths.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('install', 'convert', 'start', 'stop', 'restart', 'status', 'retire')]
    [string] $Command,

    [string] $Name,
    [int] $Number,
    [string] $RegistrationToken,
    [string] $RemovalToken,
    [string] $RunnerGroup = 'ocr-default',
    [string] $Labels = 'self-hosted,windows,ocr-default',
    [string] $OcrRoot = 'C:\Users\mzdan\dev\ourCommunityRituals',
    [string] $OrgUrl = 'https://github.com/ourCommunityRituals',
    [string] $RunnerVersion = '',
    [switch] $Force,
    [switch] $Json
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

# ─── Helpers ────────────────────────────────────────────────────────────

function Require-Admin {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Must run as Administrator (service operations require it).'
    }
}

function Reject-OneDrivePath($path) {
    if ($path -match 'OneDrive') {
        throw "Path contains OneDrive - forbidden per feedback_no_onedrive_paths: $path"
    }
}

function Get-RunnerDir($runnerName) {
    if (-not $runnerName) { throw 'Runner name required' }
    if ($runnerName -eq 'BLOODRAVEN') {
        return Join-Path $OcrRoot 'actions-runner'
    }
    if ($runnerName -match '^BLOODRAVEN-(\d+)$') {
        return Join-Path $OcrRoot ("actions-runner-$($Matches[1])")
    }
    throw "Runner name must be BLOODRAVEN or BLOODRAVEN-<N>, got: $runnerName"
}

function Get-ServiceName($runnerName) {
    return "actions.runner.ourCommunityRituals.$runnerName"
}

function Assert-RunnerDir($runnerDir) {
    if (-not (Test-Path $runnerDir)) {
        throw "Runner dir not found: $runnerDir"
    }
    if (-not (Test-Path (Join-Path $runnerDir '.runner'))) {
        throw "Not a configured runner (no .runner file): $runnerDir"
    }
}

function Get-ExistingService($serviceName) {
    return Get-Service -Name $serviceName -ErrorAction SilentlyContinue
}

function Discover-RunnerVersion($canonicalRunnerDir) {
    if ($RunnerVersion) { return $RunnerVersion }
    $zip = Get-ChildItem -Path $canonicalRunnerDir -Filter 'actions-runner-win-x64-*.zip' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($zip -and ($zip.Name -match 'actions-runner-win-x64-([0-9.]+)\.zip')) {
        return $Matches[1]
    }
    $latest = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest'
    return $latest.tag_name.TrimStart('v')
}

function Log($msg) { Write-Host "[runner] $msg" }

# ─── install ────────────────────────────────────────────────────────────

function Invoke-Install {
    Require-Admin
    Reject-OneDrivePath $OcrRoot
    if (-not $Number -or $Number -lt 2) {
        throw 'install requires -Number <int> >= 2 (BLOODRAVEN-2, -3, ...). The original BLOODRAVEN is not managed by this subcommand.'
    }
    if (-not $RegistrationToken) {
        throw 'install requires -RegistrationToken. Mint via: gh api orgs/ourCommunityRituals/actions/runners/registration-token -X POST --jq .token'
    }

    $runnerName = "BLOODRAVEN-$Number"
    $installDir = Join-Path $OcrRoot ("actions-runner-$Number")
    $canonicalDir = Join-Path $OcrRoot 'actions-runner'
    Reject-OneDrivePath $installDir

    Log "install: $runnerName at $installDir"
    if (-not (Test-Path $installDir)) {
        New-Item -ItemType Directory -Path $installDir | Out-Null
    }

    $version = Discover-RunnerVersion $canonicalDir
    Log "version: $version"

    $zipName = "actions-runner-win-x64-$version.zip"
    $zipPath = Join-Path $installDir $zipName
    if (-not (Test-Path $zipPath)) {
        $url = "https://github.com/actions/runner/releases/download/v$version/$zipName"
        Log "downloading $url"
        Invoke-WebRequest -Uri $url -OutFile $zipPath
    }
    if (-not (Test-Path (Join-Path $installDir 'config.cmd'))) {
        Log "extracting $zipName"
        Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $installDir)
    }

    Log "registering with group=$RunnerGroup labels=$Labels"
    Push-Location $installDir
    try {
        & .\config.cmd `
            --unattended --replace `
            --url $OrgUrl `
            --token $RegistrationToken `
            --runnergroup $RunnerGroup `
            --name $runnerName `
            --labels $Labels `
            --work '_work'
        if ($LASTEXITCODE -ne 0) { throw "config.cmd failed ($LASTEXITCODE)" }
    } finally { Pop-Location }

    Convert-ToService -RunnerName $runnerName -RunnerDir $installDir
    Log "DONE: $runnerName installed + service started"
}

# ─── convert ────────────────────────────────────────────────────────────

function Convert-ToService {
    param([string] $RunnerName, [string] $RunnerDir)
    $serviceName = Get-ServiceName $RunnerName
    $svcCmd = Join-Path $RunnerDir 'svc.cmd'
    if (-not (Test-Path $svcCmd)) {
        throw "svc.cmd missing at $svcCmd - runner not installed correctly"
    }
    $existing = Get-ExistingService $serviceName
    if ($existing) {
        Log "service $serviceName already exists (status: $($existing.Status))"
        if ($existing.Status -ne 'Running') {
            Log "starting $serviceName"
            Push-Location $RunnerDir
            try { & cmd /c "svc.cmd start" } finally { Pop-Location }
            if ($LASTEXITCODE -ne 0) { throw "svc.cmd start failed ($LASTEXITCODE)" }
        }
        return
    }
    Log "installing service $serviceName"
    Push-Location $RunnerDir
    try {
        & cmd /c "svc.cmd install"
        if ($LASTEXITCODE -ne 0) { throw "svc.cmd install failed ($LASTEXITCODE)" }
        & cmd /c "svc.cmd start"
        if ($LASTEXITCODE -ne 0) { throw "svc.cmd start failed ($LASTEXITCODE)" }
    } finally { Pop-Location }
    Log "service $serviceName installed + started"
}

function Invoke-Convert {
    Require-Admin
    Reject-OneDrivePath $OcrRoot
    if (-not $Name) { throw 'convert requires -Name <runner-name>' }
    $runnerDir = Get-RunnerDir $Name
    Reject-OneDrivePath $runnerDir
    Assert-RunnerDir $runnerDir
    Log "convert: $Name at $runnerDir"
    Write-Warning "If an interactive run.cmd process is active for this runner, stop it first (Ctrl+C in its terminal). The service takes over cleanly once installed."
    Convert-ToService -RunnerName $Name -RunnerDir $runnerDir
    Log "DONE: $Name now running as Windows service (survives signals + reboots)"
}

# ─── start / stop / restart ─────────────────────────────────────────────

function Invoke-ServiceOp {
    param([string] $Op)
    Require-Admin
    if (-not $Name) { throw "$Op requires -Name <runner-name>" }
    $serviceName = Get-ServiceName $Name
    $svc = Get-ExistingService $serviceName
    if (-not $svc) {
        throw "Service $serviceName not found. Install first with: runner.ps1 install -Number <N> ...  OR convert with: runner.ps1 convert -Name $Name"
    }
    switch ($Op) {
        'start' {
            if ($svc.Status -eq 'Running') { Log "$serviceName already Running"; return }
            Log "starting $serviceName"
            Start-Service -Name $serviceName
        }
        'stop' {
            if ($svc.Status -eq 'Stopped') { Log "$serviceName already Stopped"; return }
            Log "stopping $serviceName"
            Stop-Service -Name $serviceName
        }
        'restart' {
            Log "restarting $serviceName"
            Restart-Service -Name $serviceName
        }
    }
    $svc.Refresh()
    Log "$serviceName -> $($svc.Status)"
}

# ─── status ─────────────────────────────────────────────────────────────

function Invoke-Status {
    $services = Get-Service "actions.runner.ourCommunityRituals.*" -ErrorAction SilentlyContinue
    $rows = @()
    foreach ($s in $services) {
        $runnerName = $s.Name.Replace('actions.runner.ourCommunityRituals.', '')
        $dir = Get-RunnerDir $runnerName
        $rows += [PSCustomObject]@{
            Name   = $runnerName
            Status = $s.Status
            Dir    = $dir
            DirExists = Test-Path $dir
        }
    }
    # Also list any runner dirs that are NOT services (interactive or orphan)
    $dirs = Get-ChildItem -Path $OcrRoot -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -match '^actions-runner(-\d+)?$' }
    foreach ($d in $dirs) {
        $runnerFile = Join-Path $d.FullName '.runner'
        if (-not (Test-Path $runnerFile)) { continue }
        $cfg = Get-Content $runnerFile | ConvertFrom-Json
        $runnerName = $cfg.agentName
        if ($rows | Where-Object { $_.Name -eq $runnerName }) { continue }
        $rows += [PSCustomObject]@{
            Name   = $runnerName
            Status = 'Interactive (no service)'
            Dir    = $d.FullName
            DirExists = $true
        }
    }
    if ($Json) {
        $rows | ConvertTo-Json -Depth 5
    } else {
        $rows | Format-Table -AutoSize
        Write-Host ''
        Write-Host "Services Running: $(($rows | Where-Object { $_.Status -eq 'Running' }).Count)"
        Write-Host "Services Stopped: $(($rows | Where-Object { $_.Status -eq 'Stopped' }).Count)"
        Write-Host "Interactive: $(($rows | Where-Object { $_.Status -like 'Interactive*' }).Count)"
    }
}

# ─── retire ─────────────────────────────────────────────────────────────

function Invoke-Retire {
    Require-Admin
    if (-not $Name) { throw 'retire requires -Name <runner-name>' }
    if (-not $RemovalToken) {
        throw 'retire requires -RemovalToken. Mint via: gh api orgs/ourCommunityRituals/actions/runners/remove-token -X POST --jq .token'
    }
    $runnerDir = Get-RunnerDir $Name
    $serviceName = Get-ServiceName $Name

    if (-not $Force) {
        Write-Host "About to RETIRE runner $Name" -ForegroundColor Yellow
        Write-Host "  Service : $serviceName (will be stopped + uninstalled)"
        Write-Host "  Dir     : $runnerDir (will be DELETED)"
        Write-Host "  GitHub  : will be deregistered from the org"
        $ans = Read-Host 'Type "yes" to proceed'
        if ($ans -ne 'yes') { Log 'aborted'; return }
    }

    # 1. Stop + uninstall service
    $svc = Get-ExistingService $serviceName
    if ($svc) {
        if ($svc.Status -ne 'Stopped') {
            Log "stopping $serviceName"
            Push-Location $runnerDir
            try { & cmd /c "svc.cmd stop" } finally { Pop-Location }
        }
        Log "uninstalling $serviceName"
        Push-Location $runnerDir
        try { & cmd /c "svc.cmd uninstall" } finally { Pop-Location }
    }

    # 2. Deregister from GitHub
    if (Test-Path (Join-Path $runnerDir 'config.cmd')) {
        Log "deregistering from GitHub"
        Push-Location $runnerDir
        try {
            & .\config.cmd remove --token $RemovalToken
        } finally { Pop-Location }
    }

    # 3. Delete install dir
    Log "deleting $runnerDir"
    Remove-Item -Path $runnerDir -Recurse -Force
    Log "DONE: $Name retired"
}

# ─── Dispatch ───────────────────────────────────────────────────────────

switch ($Command) {
    'install' { Invoke-Install }
    'convert' { Invoke-Convert }
    'start'   { Invoke-ServiceOp -Op 'start' }
    'stop'    { Invoke-ServiceOp -Op 'stop' }
    'restart' { Invoke-ServiceOp -Op 'restart' }
    'status'  { Invoke-Status }
    'retire'  { Invoke-Retire }
}
