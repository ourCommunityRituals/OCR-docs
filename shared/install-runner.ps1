<#
.SYNOPSIS
    Install an additional self-hosted GitHub Actions runner for the
    ourCommunityRituals org.

.DESCRIPTION
    Conforms to OCR_STANDARD_selfHostedRunners.md. Idempotent — safe to
    re-run for upgrades. Downloads the same runner version as the
    canonical install, extracts to actions-runner-<N>/, configures with
    the standard labels + runner group, registers as a Windows service,
    and starts it.

    Never run this from OneDrive paths or inside an app repo. The runner
    dir MUST be a sibling of the OCR app repos under
    C:\Users\mzdan\dev\ourCommunityRituals\ (per feedback_no_onedrive_paths
    + OCR_STANDARD_selfHostedRunners §4).

.PARAMETER Number
    The runner index. 2 for BLOODRAVEN-2, 3 for BLOODRAVEN-3, etc.
    The unnumbered original BLOODRAVEN at ../actions-runner/ is never
    reinstalled by this script.

.PARAMETER RegistrationToken
    Short-lived org registration token (~1 hour TTL). Generate via:
        gh api orgs/ourCommunityRituals/actions/runners/registration-token -X POST --jq .token
    Never commit. Never persist to disk.

.PARAMETER RunnerGroup
    Optional. Defaults to 'ocr-default'. The org-level runner group the
    new runner joins.

.PARAMETER Labels
    Optional. Defaults to 'self-hosted,windows,ocr-default'. Comma-separated.

.PARAMETER OcrRoot
    Optional. Defaults to C:\Users\mzdan\dev\ourCommunityRituals. The
    parent directory where runner install dirs live as siblings to app repos.

.EXAMPLE
    $token = gh api orgs/ourCommunityRituals/actions/runners/registration-token -X POST --jq .token
    powershell -ExecutionPolicy Bypass -File install-runner.ps1 -Number 2 -RegistrationToken $token

.NOTES
    Canonical path: OCR-docs/shared/install-runner.ps1
    Requires: PowerShell 5+, local admin (for New-Service), gh CLI
    authenticated with admin:org scope (to generate the token).
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(2, 99)]
    [int] $Number,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string] $RegistrationToken,

    [string] $RunnerGroup = 'ocr-default',

    [string] $Labels = 'self-hosted,windows,ocr-default',

    [string] $OcrRoot = 'C:\Users\mzdan\dev\ourCommunityRituals',

    [string] $OrgUrl = 'https://github.com/ourCommunityRituals',

    # Override only if upgrading. Default pins to the version of the
    # existing BLOODRAVEN install, discovered at script start.
    [string] $RunnerVersion = ''
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'  # faster download

function Require-Admin {
    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw 'Must run as Administrator (New-Service + svc.sh require it).'
    }
}

function Reject-OneDrivePath($path) {
    if ($path -match 'OneDrive') {
        throw "Path contains OneDrive — forbidden per feedback_no_onedrive_paths: $path"
    }
}

function Discover-RunnerVersion($canonicalRunnerDir) {
    if ($RunnerVersion) { return $RunnerVersion }
    # Prefer pinning to the canonical runner's version for fleet consistency.
    $zip = Get-ChildItem -Path $canonicalRunnerDir -Filter 'actions-runner-win-x64-*.zip' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($zip) {
        if ($zip.Name -match 'actions-runner-win-x64-([0-9.]+)\.zip') {
            return $Matches[1]
        }
    }
    # Fallback: ask GitHub for latest
    $latest = Invoke-RestMethod -Uri 'https://api.github.com/repos/actions/runner/releases/latest'
    return $latest.tag_name.TrimStart('v')
}

function Ensure-RunnerBinary($installDir, $version) {
    $zipName = "actions-runner-win-x64-$version.zip"
    $zipPath = Join-Path $installDir $zipName
    if (-not (Test-Path $zipPath)) {
        $url = "https://github.com/actions/runner/releases/download/v$version/$zipName"
        Write-Host "[install-runner] downloading $url"
        Invoke-WebRequest -Uri $url -OutFile $zipPath
    } else {
        Write-Host "[install-runner] runner zip already present at $zipPath"
    }
    # Extract only if the binary isn't already there
    if (-not (Test-Path (Join-Path $installDir 'config.cmd'))) {
        Write-Host "[install-runner] extracting $zipName into $installDir"
        Add-Type -AssemblyName 'System.IO.Compression.FileSystem'
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $installDir)
    } else {
        Write-Host "[install-runner] runner binary already extracted"
    }
}

function Register-Runner($installDir, $name) {
    $configCmd = Join-Path $installDir 'config.cmd'
    if (-not (Test-Path $configCmd)) {
        throw "config.cmd missing at $configCmd"
    }
    # Config.cmd in "unattended" mode re-registers idempotently if .runner
    # exists and the name matches; otherwise it creates a fresh registration.
    Write-Host "[install-runner] registering $name with group $RunnerGroup labels $Labels"
    & $configCmd `
        --unattended `
        --replace `
        --url $OrgUrl `
        --token $RegistrationToken `
        --runnergroup $RunnerGroup `
        --name $name `
        --labels $Labels `
        --work '_work'
    if ($LASTEXITCODE -ne 0) { throw "config.cmd failed with exit $LASTEXITCODE" }
}

function Install-Service($installDir, $name) {
    $svcCmd = Join-Path $installDir 'svc.sh'
    $serviceName = "actions.runner.ourCommunityRituals.$name"
    # On Windows the runner provides svc.sh (invoked via Git Bash) OR
    # alternatively the install/configure process can emit a service via
    # config.cmd itself. The simplest cross-compatible path is to use
    # `config.cmd` with no svc step, then invoke the stand-alone
    # svc-installer below:
    $svcInstaller = Join-Path $installDir 'bin\RunnerService.js'
    # Newer runner versions use `./svc.sh install <user>` via bash OR
    # on Windows, `.\\svc install`. Try the Windows form first.
    $winSvc = Join-Path $installDir 'svc.cmd'
    if (Test-Path $winSvc) {
        Write-Host "[install-runner] installing Windows service via svc.cmd"
        Push-Location $installDir
        try {
            & cmd /c "svc.cmd install"
            if ($LASTEXITCODE -ne 0) { throw "svc.cmd install failed with exit $LASTEXITCODE" }
            & cmd /c "svc.cmd start"
            if ($LASTEXITCODE -ne 0) { throw "svc.cmd start failed with exit $LASTEXITCODE" }
        } finally {
            Pop-Location
        }
        Write-Host "[install-runner] service $serviceName installed and started"
    } else {
        Write-Warning "svc.cmd not found at $winSvc. Run runner interactively with run.cmd, or install as service manually."
    }
}

# ─── Main ──────────────────────────────────────────────────────────────
Require-Admin
Reject-OneDrivePath $OcrRoot

$runnerName   = "BLOODRAVEN-$Number"
$installDir   = Join-Path $OcrRoot "actions-runner-$Number"
$canonicalDir = Join-Path $OcrRoot 'actions-runner'

Reject-OneDrivePath $installDir

Write-Host "============================================================"
Write-Host "  OCR runner install: $runnerName"
Write-Host "  Dir:    $installDir"
Write-Host "  Group:  $RunnerGroup"
Write-Host "  Labels: $Labels"
Write-Host "============================================================"

if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
    Write-Host "[install-runner] created $installDir"
}

$version = Discover-RunnerVersion $canonicalDir
Write-Host "[install-runner] runner version: $version"

Ensure-RunnerBinary -installDir $installDir -version $version
Register-Runner -installDir $installDir -name $runnerName
Install-Service -installDir $installDir -name $runnerName

Write-Host ''
Write-Host "[install-runner] DONE. Verify with:"
Write-Host "  Get-Service 'actions.runner.ourCommunityRituals.$runnerName'"
Write-Host "  gh api orgs/ourCommunityRituals/actions/runners --jq '.runners[] | select(.name | startswith(`"BLOODRAVEN`")) | {name, status, busy}'"
