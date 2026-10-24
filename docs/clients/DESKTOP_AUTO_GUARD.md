# Linux Auto traffic guard / Защита трафика Auto

Status,24.10: implemented and exercised against the isolated local Linux kernel.
Not installed and not a complete Auto VPN. The native Go policy now invokes the
guard through `clients/linux/auto_policy.py`; isolated kernel checks use synthetic
platform callbacks. A real single-attempt MESH adapter shares the packet lifecycle
with manual MESH. Protected normal configuration and one-attempt AWG/TCP helper
adapters, coordinator/capability host and root service/UID socket now exist.
Authorized GUI activation, root/user floor synchronization and installed handoff
acceptance remain open.
See [normal adapter ownership](DESKTOP_AUTO_NORMAL.md). Installed helpers, GUI, versions, public catalogs and
server permissions are unchanged. Internal component builds are not desktop installers.

## Root service contract

`clients/linux/auto_guard.py` owns only the `inet family_connect_auto` nftables
table. No global flush, resolver change, route replacement or other VPN cleanup.
It adds output and forward filtering at priority10, with default drop. These
accept verdicts do not bypass a drop in another base chain. Existing established
connections are not an output escape hatch. Forward replies require the pinned
VPN input interface and established/related conntrack state; blocked/probe states
permit no forwarded traffic.

The root coordinator supplies the authenticated user's UID and its persistent
session generation, not arbitrary GUI commands or nftables expressions. A root
0700 directory,0600 no-follow/single-link journal and lifetime exclusive lock own
the table. The generation is recorded in its comment and every rule/chain is
read back, not merely the comment. A conflicting table is not adopted or deleted.
The bounded subprocess runner has a5-second per-command timeout and64KiB
input/output limits. The host must still enforce its overall cancellation budget.

Lifecycle:

1. `acquire()` installs a verified blocking table **before** configuration or a
   candidate. Existing journal state is reconciled to blocked, never resumed as
   ready. The class is root-internal; it exposes no new unprivileged IPC endpoint.
2. `prepare(candidate(...))` accepts only the existing fcawg/fctcp/fcmesh interface
   patterns. Previous and next interfaces must be absent. Public unicast IPv4
   gateway/port arguments come from validated material; the guard is not a
   replacement for signature, entitlement, identity or revocation checks.
3. During probe, only root can send through the planned IPv4 VPN interface.
   AWG outer UDP is restricted to its exact gateway/port; TCP also requires
   mark64630. MESH/bootstrap requires root and exact mark64640, IPv4 only.
   An ordinary application cannot bypass through those gateway or DNS addresses.
4. After authenticated session, TUN, routing, DNS and health checks, the host may
   call `ready(ifindex)`. It verifies an up TUN and pins both name and index.
   Its snapshot is **firewall state, not complete VPN health**. Normal IPv6 is
   opt-in only after platform checks; MESH IPv6 is rejected. The root probe
   allowance disappears in ready state, so reusing a name cannot revive it.
5. `block()` atomically closes user traffic before stopping the candidate. Only
   after helpers/children have stopped and the old interface is absent may the
   next candidate prepare. `release()` requires blocked state and an absent
   candidate interface. It removes only its verified own table and journal.
6. `close()` only releases the userspace lock. It never opens traffic. A lost
   reply, failed journal commit or process crash retains the journal and kernel
   guard; the next owner reconciles to blocked. Do not retry an unknown operation
   by starting a second coordinator or dropping its rules.

State changes journal intent before one atomic nftables transaction (delete and
recreate **within the same batch**), then verify and commit the journal. Both
possible exact rule states are recognized during recovery. A missing guard is
not reported ready; block/acquire may repair its absence. Unknown added/modified
rules are not silently discarded. nft JSON resolves indices to names, including
numeric strings for disappeared interfaces; readback resolves them against a
stable before/after kernel interface inventory without ignoring the index pin.

Root DHCPv4/v6 and narrowly scoped IPv6 router/neighbor discovery remain possible:
DHCP ports only, link-local/multicast DHCPv6, permitted ICMPv6 discovery types with
hop limit255 and code0. No general IPv6 or user UDP exemption. Non-root network
manager DHCP credentials need capability review before claiming support on such
systems; this checkpoint does not establish that OS integration.

## Verification / Проверка

`clients/desktop/tests/test_auto_guard.py` covers policy, bounded execution,
ownership, journal uncertainty, terminal conflicts, crash reconciliation and stale
callbacks. Existing AWG/TCP/auth/profile/MESH tests are separate regression gates.

`scripts/check_desktop_auto_guard.py` refuses the caller's host network inode or
any nonempty initial network/firewall. It uses real nftables, real TUN file
descriptors and actual root/non-root UDP/TCP/forwarded packets. It matches the
specific test packet, not unrelated IPv6 neighbor-discovery background traffic.
Addresses such as8.8.8.8 are routed only into an isolated dummy-underlay TUN;
there is no external connection. Tests verify ordinary DNS/IPv6 containment,
exact privileged bypass, block/probe/ready/handoff, interface-name reuse, owner
exit/restart, protected journal paths, cleanup and an unrelated table's retention.

The prepared `desktop-auto-guard.yml` CI job uses root `unshare --net` and a hard
deadline. Local validation uses an existing local Docker image with `--network
none`,NET_ADMIN plus test-only SETUID/SETGID, `/dev/net/tun`, read-only source/tools,
0.5 CPU,256MiB,32 PIDs and45s inner timeout. It never uses host networking or
`--privileged`. The local runner removes only its nonce-labelled test container
on completion/cancellation; the thermal wrapper also enforces the laptop limits.
This is local Linux kernel evidence, not installed desktop or remote CI evidence.

## Remaining product integration / Что ещё необходимо

Root-служба соединяет общий Go Auto с guard и существующими helper; реализованы
UID-привязанный IPC, capability-проверки и memory-only intent/generation. Нужны
штатная авторизация запуска из GUI, root/user floor sync и установленная приёмка
переключений, cleanup и защищённых служебных сокетов при смене транспорта.
Firewall-разрешение **не создаёт** underlying-маршрут и не заменяет SO_MARK,
привязку сокета/интерфейса или действующие правила MESH/TCP/AWG. Не разрешать
произвольные адреса/команды клиенту и не удалять защиту ради успешного bootstrap.

Только после этой интеграции включать Auto в GTK и проверять установленную версию,
DNS/IPv6, сон/возврат сети, MESH/P1 и обновление с сохранением identity. Guard и
служба входят в закрытый компонент-r10, но не установлены и не включены из GUI.
Нет рекомендации запускать GUI через sudo и нет заявления PARITY PASS.
Windows broker/WinForms и полные установочные пакеты остаются отдельными
обязательными этапами исходной задачи, не заменёнными этими тестами.
