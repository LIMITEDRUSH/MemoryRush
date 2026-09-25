param(
    [string]$Python = '',
    [string]$LlamaServer = $env:MEMORYRUSH_LLAMA_SERVER,
    [string]$ModelPath = $env:MEMORYRUSH_MODEL_PATH,
    [switch]$Ollama,
    [switch]$ApiOnly,
    [int]$Port = 8502
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $projectRoot
$privateDir = if ($env:MEMORYRUSH_DATA_DIR) { $env:MEMORYRUSH_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'MemoryRush' }
New-Item -ItemType Directory -Force -Path $privateDir | Out-Null
if (-not $Python) {
    $Python = Join-Path $projectRoot '.venv-reading\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) {
        $uv = (Get-Command uv -ErrorAction Stop).Source
        & $uv venv --python 3.12 .venv-reading
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the reading-assistant environment.' }
        & $uv pip install --python $Python -r requirements.txt
        if ($LASTEXITCODE -ne 0) { throw 'Could not install dependencies.' }
    }
}
if ($ApiOnly) {
    # Starts only the app; saved settings win. Fresh installations use preview
    # until the user configures and explicitly enables an API in Settings.
    $env:MEMORYRUSH_PROVIDER = 'preview'
    Write-Host 'App-only mode. No local model is started. Choose an API in Settings.'
} elseif (-not $Ollama) {
    if (-not $LlamaServer -or -not $ModelPath -or -not (Test-Path -LiteralPath $LlamaServer) -or -not (Test-Path -LiteralPath $ModelPath)) {
        throw 'Supply -LlamaServer and -ModelPath for your existing GGUF runtime/model, or use -Ollama or -ApiOnly.'
    }
    $listener = Get-NetTCPConnection -LocalPort 8384 -State Listen -ErrorAction SilentlyContinue
    if (-not $listener) {
        $argsList = @('-m', ('"' + $ModelPath + '"'), '--alias', 'qwen3:8b',
            '-ngl', 'all', '--fit', 'off', '-c', '16384', '-np', '1', '-b', '256', '-ub', '128',
            '-fa', 'on', '-t', '4', '--host', '127.0.0.1', '--port', '8384', '--offline',
            '--no-webui', '--no-context-shift', '--reasoning', 'off', '--cache-ram', '0', '--log-disable')
        $serverProcess = Start-Process -FilePath $LlamaServer -ArgumentList $argsList -WindowStyle Hidden -PassThru `
            -RedirectStandardOutput (Join-Path $privateDir 'model.stdout.log') `
            -RedirectStandardError (Join-Path $privateDir 'model.stderr.log')
        Write-Host "Local model starting (PID $($serverProcess.Id)); logs: $privateDir"
    } else {
        Write-Host 'Port 8384 is already in use; no second model process started. Verify the selected local endpoint.'
    }
    $env:MEMORYRUSH_PROVIDER = 'llama.cpp'
} else {
    $env:MEMORYRUSH_PROVIDER = 'ollama'
}
Write-Host "Open http://127.0.0.1:$Port . Personal data: $privateDir"
& $Python -m streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port $Port --server.headless true --browser.gatherUsageStats false
