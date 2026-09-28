Get-ChildItem -Path 'C:/Users/onela/AppData/Local/AI-Breadboard/apps/windows' -Recurse -Filter *.py |
    ForEach-Object {
        $path = $_.FullName
        $content = Get-Content $path -Raw
        $new = $content -replace 'apps\.windows\.api\.', 'apps.windows.telemetry.api_bindings.'
        if ($new -ne $content) {
            Set-Content -Path $path -Value $new -Encoding utf8
            Write-Host "Updated imports in $path"
        }
    }
