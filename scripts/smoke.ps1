param(
  [string]$Base = "http://localhost:8080"
)

function Assert($ok, $msg) {
  if ($ok) { Write-Host "✅ $msg" -ForegroundColor Green }
  else { Write-Host "❌ $msg" -ForegroundColor Red; exit 1 }
}

# Health
$paths = @("/", "/health", "/healthz", "/readyz")
foreach ($p in $paths) {
  $code = curl.exe -s -o $null -w "%{http_code}" "$Base$p"
  Assert ($code -eq "200") "$p is 200"
}

# Plan
$planJson = curl.exe -s "$Base/plan" -H "Content-Type: application/json" `
  -d '{ "high_level_goal":"Smoke plan", "user_context":"smoke" }'
$planId = $planJson | jq -r '.plan_id // .id // empty'
Assert ($planId) "created plan: $planId"

# Inspect
$inspect = curl.exe -s "$Base/state/plans/$planId"
$taskId = $inspect | jq -r '.tasks[0].task_id'
Assert ($taskId) "first task: $taskId"

# Cancel
$ok = (curl.exe -s -X POST "$Base/state/tasks/$taskId/cancel" | jq -r '.ok // true') -eq "true"
Assert $ok "cancel OK"
$state = curl.exe -s "$Base/state/plans/$planId" | jq -r '.tasks[] | select(.task_id=="'"$taskId"'") | .state'
Assert ($state -eq "cancelled") "state -> cancelled"

# Retry
$ok = (curl.exe -s -X POST "$Base/state/tasks/$taskId/retry" | jq -r '.ok // true') -eq "true"
Assert $ok "retry OK"
$state = curl.exe -s "$Base/state/plans/$planId" | jq -r '.tasks[] | select(.task_id=="'"$taskId"'") | .state'
Assert ($state -eq "pending") "state -> pending"

Write-Host "🎉 Smoke passed for plan $planId (task $taskId)" -ForegroundColor Cyan
