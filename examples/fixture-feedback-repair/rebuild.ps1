param(
  [Parameter(Mandatory=$true)][string]$Python,
  [Parameter(Mandatory=$true)][string]$MatplotlibPath,
  [Parameter(Mandatory=$true)][string]$Output
)
$ErrorActionPreference='Stop'
$previousPythonPath=$env:PYTHONPATH
try {
  $env:PYTHONPATH=$MatplotlibPath
  & $Python -B -X utf8 (Join-Path $PSScriptRoot 'source/build.py') --out $Output --revision final
  if($LASTEXITCODE -ne 0){throw "Build failed: $LASTEXITCODE"}
} finally {
  $env:PYTHONPATH=$previousPythonPath
}
