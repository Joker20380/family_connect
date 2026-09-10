# Current state / Текущее состояние

Updated: 2026-09-10. Release 0.2.1 rollout **in progress**.

- Source: product registration, authenticated provisioning/version cache, migration v3,
  local gateway reconciliation, Linux/Windows responsive UI and signed client updates.
- Local checks: 171 Python tests; shared Python/C# catalog verification; Linux 18 layouts.
- Linux installed application: still previous version until rollout verification below.
- Windows 0.2.1: preparing CI installer; no accessible personal Windows PC was supplied.
- Server 185.251.89.19: old pilot still running; 3 existing peers. Product DB absent at preflight.
- Product API planned binding: 127.0.0.1:18082 (18080 and 18081 belong to existing labs).
- Signing private key persisted locally under state-client-build/update-signing; never sent to CI/server.
- Signed update catalog not published yet. New clients cannot offer updates until it is signed.

Next: finish platform CI, install Linux, deploy product API/worker and gateway helper,
verify existing peers and health, publish signed update catalog, then update this file
with actual results and links. See [PLAN](PLAN.md) and [release](releases/0.2.1.ru.md).
