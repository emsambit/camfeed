# Run after compiling CameraWebServer; close Serial Monitor first.
# Connect ESP32 GPIO0 to GND and reset before running.
# Example:
# .\flash.ps1 -Port COM10 -BuildDir .\build
param(
    [string]$Port = "COM10",
    [string]$BuildDir = ".\build",
    [string]$EsptoolPath = "$env:LOCALAPPDATA\Arduino15\packages\esp32\tools\esptool_py\5.3.1\esptool.exe"
)
$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $EsptoolPath -PathType Leaf)) {
    throw "esptool not found. Supply -EsptoolPath with your installed esptool.exe path."
}
$images = @(
    "CameraWebServer.ino.bootloader.bin",
    "CameraWebServer.ino.partitions.bin",
    "boot_app0.bin",
    "CameraWebServer.ino.bin"
)
foreach ($image in $images) {
    if (-not (Test-Path -LiteralPath (Join-Path $BuildDir $image) -PathType Leaf)) {
        throw "Missing $image in $BuildDir. Compile with --build-path first."
    }
}
$resolvedBuild = (Resolve-Path -LiteralPath $BuildDir).Path
# Working settings: 115200 baud, no flasher stub, DIO, 40 MHz, 4 MB.
# This writes firmware and erases the flash sectors occupied by these images.
& $EsptoolPath --chip esp32 --port $Port --baud 115200 --no-stub write-flash --flash-mode dio --flash-freq 40m --flash-size 4MB 0x1000 (Join-Path $resolvedBuild $images[0]) 0x8000 (Join-Path $resolvedBuild $images[1]) 0xe000 (Join-Path $resolvedBuild $images[2]) 0x10000 (Join-Path $resolvedBuild $images[3])
if ($LASTEXITCODE -ne 0) { throw "Flashing failed with exit code $LASTEXITCODE." }
Write-Host "Flash verified. Remove GPIO0 from GND, reset ESP32-CAM, then open Serial Monitor at 115200 baud."
