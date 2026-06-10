# Script para exportar la base de datos a Excel
param(
    [switch]$Open
)

$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$exportScript = Join-Path $projectPath "export_excel.py"

Write-Host "Ejecutando exportación de Excel..." -ForegroundColor Cyan

# Cambiar al directorio del proyecto
Push-Location $projectPath

# Ejecutar el script Python
python $exportScript

if ($LASTEXITCODE -eq 0) {
    $excelFile = Join-Path $projectPath "base_de_datos_exportada.xlsx"
    Write-Host "[OK] Excel generado en: $excelFile" -ForegroundColor Green
    
    # Si se pasa el parámetro -Open, abre el archivo
    if ($Open -and (Test-Path $excelFile)) {
        Start-Process $excelFile
    }
} else {
    Write-Host "[ERROR] Error al generar el Excel" -ForegroundColor Red
}

Pop-Location
