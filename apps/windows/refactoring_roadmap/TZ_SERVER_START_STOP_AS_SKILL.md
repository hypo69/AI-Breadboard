Оформи этот конспект как навык для ассистента. Изучи код, посмотри где и как прописываются навыки

```powershell
Start-Sleep -Seconds 5 ; Test-NetConnection -ComputerName localhost -Port 8001
```

То есть про **PowerShell-механику ожидания + проверки состояния TCP endpoint**.

Вот здесь действительно много полезного.

### 1. Ждать не фиксированное время, а готовность

Вместо:

```powershell
Start-Sleep -Seconds 5
Test-NetConnection localhost -Port 8001
```

можно:

```powershell
while (-not (Test-NetConnection localhost -Port 8001 -InformationLevel Quiet)) {
    Start-Sleep -Seconds 1
}

Write-Host 'Port 8001 is ready'
```

То есть:

> **wait until condition**

---

### 2. Ждать с таймаутом

```powershell
$timeout = 30
$elapsed = 0

while (-not (Test-NetConnection localhost -Port 8001 -InformationLevel Quiet)) {
    if ($elapsed -ge $timeout) {
        throw 'Timeout waiting for port 8001'
    }

    Start-Sleep -Seconds 1
    $elapsed++
}

Write-Host 'Port 8001 is ready'
```

Получается универсальный паттерн:

```text
WAIT → CHECK → WAIT → CHECK → ... → TIMEOUT
```

---

### 3. Проверять несколько портов

```powershell
8001
3000
8080
11434
```

Например:

```powershell
8001, 3000, 8080, 11434 | ForEach-Object {
    [PSCustomObject]@{
        Port = $_
        Ready = Test-NetConnection localhost -Port $_ -InformationLevel Quiet
    }
}
```

Получится практически:

```text
Port  Ready
----  -----
8001  True
3000  True
8080  False
11434 True
```

---

### 4. Проверять порт до запуска следующего этапа

Очень полезный сценарий:

```powershell
Start-Process myserver.exe

while (-not (Test-NetConnection localhost -Port 8001 -InformationLevel Quiet)) {
    Start-Sleep -Milliseconds 500
}

Start-Process client.exe
```

То есть:

```text
START SERVER
     ↓
WAIT
     ↓
PORT READY
     ↓
START CLIENT
```

Это уже простой **process orchestration**.

---

### 5. Проверять, что порт появился

```powershell
$before = Test-NetConnection localhost -Port 8001 -InformationLevel Quiet

# запуск приложения

do {
    Start-Sleep -Milliseconds 250
    $after = Test-NetConnection localhost -Port 8001 -InformationLevel Quiet
} until ($after)

if (-not $before -and $after) {
    Write-Host 'Port 8001 has appeared'
}
```

Можно отслеживать:

```text
CLOSED → OPEN
```

---

### 6. Проверять, что порт исчез

Тот же принцип наоборот:

```powershell
while (Test-NetConnection localhost -Port 8001 -InformationLevel Quiet) {
    Start-Sleep -Seconds 1
}

Write-Host 'Port 8001 has closed'
```

Например:

```powershell
Stop-Process -Id $PID

# ждать завершения сервера
```

---

### 7. Ждать смены состояния

Это уже интереснее:

```text
CLOSED
  ↓
OPEN
  ↓
CLOSED
```

Можно использовать как очень простой **state watcher**.

```powershell
$state = $false

while ($true) {
    $newState = Test-NetConnection localhost -Port 8001 -InformationLevel Quiet

    if ($newState -ne $state) {
        $state = $newState

        if ($state) {
            Write-Host '8001: OPEN'
        }
        else {
            Write-Host '8001: CLOSED'
        }
    }

    Start-Sleep -Seconds 1
}
```

---

### 8. Проверять не только TCP, но и HTTP

Вот здесь особенно важная граница.

```powershell
Test-NetConnection localhost -Port 8001
```

отвечает:

> **Есть ли TCP listener?**

Но это не означает:

> **Работает ли приложение?**

Поэтому можно сделать:

```text
TCP 8001
   ↓
OPEN
   ↓
HTTP GET /health
   ↓
200 OK
```

Например:

```powershell
do {
    Start-Sleep -Seconds 1

    $tcp = Test-NetConnection localhost -Port 8001 -InformationLevel Quiet

    if ($tcp) {
        try {
            $response = Invoke-WebRequest `
                -Uri 'http://localhost:8001/health' `
                -UseBasicParsing

            $ready = $response.StatusCode -eq 200
        }
        catch {
            $ready = $false
        }
    }
} until ($ready)

Write-Host 'Application is ready'
```

Это уже настоящий **readiness probe**.

---

### 9. Сделать универсальный `Wait-Port`

Можно вообще превратить это в собственную команду:

```powershell
function Wait-Port {
    param (
        [string]$ComputerName = 'localhost',
        [int]$Port,
        [int]$TimeoutSeconds = 30
    )

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        if (Test-NetConnection `
                -ComputerName $ComputerName `
                -Port $Port `
                -InformationLevel Quiet) {

            return $true
        }

        Start-Sleep -Milliseconds 500
    }

    return $false
}
```

Тогда:

```powershell
if (Wait-Port -Port 8001 -TimeoutSeconds 20) {
    Write-Host 'Ready'
}
else {
    Write-Host 'Timeout'
}
```

---

### 10. А можно сделать уже целый набор примитивов

Например:

```text
Wait-Port
Wait-Http
Wait-Process
Wait-Service
Wait-File
Wait-Registry
Wait-Window
Wait-Event
Wait-Condition
```

И это превращается в очень интересный **Windows automation DSL**:

```powershell
Start-Process server.exe

Wait-Port localhost 8001

Start-Process client.exe

Wait-Process client.exe

Wait-Port localhost 8001 -State Closed
```

То есть твоя исходная конструкция на самом деле относится к гораздо более общей концепции:

> **запустить → ждать → наблюдать условие → продолжить при выполнении условия → остановиться по таймауту/ошибке.**

И `Start-Sleep + Test-NetConnection` — один из самых простых и полезных кирпичиков этой схемы.
