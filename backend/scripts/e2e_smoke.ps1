# SleepFlow E2E smoke test: full demo chain over HTTP
$ErrorActionPreference = "Stop"
$base = "http://127.0.0.1:8000"

function Call-Api($method, $path, $body = $null) {
    $params = @{ Method = $method; Uri = ($base + $path); ErrorAction = "Stop" }
    if ($null -ne $body) {
        $params.Body = ($body | ConvertTo-Json -Depth 5)
        $params.ContentType = "application/json"
    }
    try {
        return Invoke-RestMethod @params
    } catch {
        $r = $_.Exception.Response
        if ($r) {
            $reader = [System.IO.StreamReader]::new($r.GetResponseStream())
            $text = $reader.ReadToEnd()
            return [pscustomobject]@{ _error = $true; status = [int]$r.StatusCode; detail = $text }
        }
        return [pscustomobject]@{ _error = $true; status = -1; detail = $_.Exception.Message }
    }
}

function Step($label) { Write-Host ""; Write-Host "=== $label ===" -ForegroundColor Cyan }

# 0) reset demo, then health
Step "0. reset & health"
$vr = Call-Api POST "/api/demo/reset"
Write-Host "reset ok demo=$($vr.clock.demo_active) coins=$($vr.profile.total_coins)"
$h = Call-Api GET "/api/health"
Write-Host ($h | ConvertTo-Json -Compress)

# 1) initial view
Step "1. session/current (initial)"
$v0 = Call-Api GET "/api/session/current"
Write-Host "bedtime=$($v0.profile.weekday_bedtime) wake=$($v0.profile.weekday_wake) phase=$($v0.home.phase) can_start=$($v0.home.can_start)"

# 2) demo enter window
Step "2. demo enter-window"
$v1 = Call-Api POST "/api/demo/enter-window"
Write-Host "virtual_now=$($v1.clock.virtual_now) demo=$($v1.clock.demo_active)"

# 3) start session
Step "3. session start"
$v2 = Call-Api POST "/api/session/start"
Write-Host "state=$($v2.session.state)"

# 4) choose scenario shorts
Step "4. agent/start shorts"
$v3 = Call-Api POST "/api/agent/start" @{ scenario = "shorts" }
Write-Host "state=$($v3.session.state) stage=$($v3.session.stage)"
Write-Host "msg=$($v3.session.message.text)"
Write-Host "can_act=$($v3.session.can_act -join ',')"

# 5) three stages
Step "5. three-stage intervention"
$v4 = Call-Api POST "/api/agent/act" @{ action = "continue" }
Write-Host "continue -> $($v4.session.state) | msg=$($v4.session.message.text)"
$v5 = Call-Api POST "/api/agent/act" @{ action = "continue" }
Write-Host "continue -> $($v5.session.state) | msg=$($v5.session.message.text)"
$v6 = Call-Api POST "/api/agent/act" @{ action = "continue" }
Write-Host "stage3 continue again -> error=$($v6._error) status=$($v6.status)"

# 6) prepare sleep (user picks music)
Step "6. prepare_sleep (content=music)"
$v7 = Call-Api POST "/api/agent/act" @{ action = "prepare_sleep"; content_type = "music" }
Write-Host "state=$($v7.session.state) content=$($v7.session.content.title) remaining=$($v7.session.sleep.remaining_sec)s"

# 7) advance 60 min -> success
Step "7. advance 60 min -> Sleep Success"
$v8 = Call-Api POST "/api/demo/advance" @{ minutes = 60 }
Write-Host "state=$($v8.session.state) reward_ready=$($v8.session.reward_ready)"

# 8) settle next day
Step "8. settle reward"
$r1 = Call-Api POST "/api/reward/settle" @{ session_id = $v8.session.session_id }
Write-Host "settle before next-day -> error=$($r1._error) status=$($r1.status)"
$v9 = Call-Api POST "/api/demo/next-day"
Write-Host "virtual_now=$($v9.clock.virtual_now)"
$r2 = Call-Api POST "/api/reward/settle" @{ session_id = $v8.session.session_id }
Write-Host "coins=$($r2.coins) streak=$($r2.streak_days) total=$($r2.total_coins) already=$($r2.already)"

# 9) history & final view
Step "9. history & current"
$hist = Call-Api GET "/api/reward/history"
Write-Host "history items=$($hist.items.Count) first_state=$($hist.items[0].state) coins=$($hist.items[0].coins)"
$v10 = Call-Api GET "/api/session/current"
Write-Host "active_session=$($v10.session) coins=$($v10.profile.total_coins) streak=$($v10.profile.streak_days)"

Write-Host ""
Write-Host "========== E2E DONE ==========" -ForegroundColor Green
