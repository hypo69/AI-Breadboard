# PostFileSave hook: Warn when saving files that might contain tokens
# Trigger: PostFileSave
# Matcher: \.env$ or \.(py|js|ts|txt|md)$

$filePath = $env:KIRO_FILE_PATH

# Check .env files
if ($filePath -match '\.env$') {
    Write-Output '{"hookSpecificOutput":{"permissionDecision":"ask","permissionDecisionReason":"Editing .env file - verify no tokens are exposed"}}'
    exit 0
}

# Check code/text files for known token patterns
if ($filePath -match '\.(py|js|ts|txt|md)$') {
    try {
        $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
        if ($content -match 'GOCSPX-[a-zA-Z0-9_-]+' -or
            $content -match 'AA[a-zA-Z0-9_:-]+' -or
            $content -match 'NGROCK_AUTOTOKEN\s*=\s*[^\s]+') {
            Write-Output '{"hookSpecificOutput":{"permissionDecision":"ask","permissionDecisionReason":"Potential token found in saved file"}}'
            exit 0
        }
    } catch {
        # File read error - ignore
    }
}

exit 0
