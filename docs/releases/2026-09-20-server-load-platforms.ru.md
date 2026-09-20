# Шкала нагрузки на трёх платформах — 2026-09-20

## Метрика и серверы

На RU 185.251.89.19 и NL 186.246.45.246 мониторинг использует
capacity_mbps=200, capacity_direction=egress,
capacity_basis=provider-default-estimate. Это оценка по публичным условиям VDS
https://sprinthost.ru/docs/conditions/limits, не подтверждённый тариф этих VPS.
Рекламируемый порт Sprintbox 10 Гбит/с не принят за индивидуальную гарантированную ёмкость.
Процент = min(100, max(CPU%, TX_Mbps / 200 * 100)); в интерфейсе «≈».
CPU и трафик относятся ко всему VPS. TTL 45 секунд; устаревшие данные не превращаются в 0%.
Пороговые цвета 70/90%; автоматического добавления серверов нет.
Endpoint: https://185.251.89.19:8443/status/server-load.json.
Обновлены только monitor.py/config.json и мониторинговая служба, не VPN-службы.
Откат на обоих хостах: в /opt/apps/family_connect/server-load восстановить
config.json.before-provider-capacity-20260920 и monitor.py.before-provider-capacity-20260920,
перезапустить family-connect-server-load.service. Это вернёт неизвестную ёмкость.

## Linux

Установлен 0.2.9 preview/source dde902a:
3ef22e124f177f82c6dcfef017e53babea3f2656f2e2ed34758c23ff50252dfc.
Архив FamilyConnect-Control-Linux-preview-3ef22e124f177f82.tar.gz;
SHA256 4e02c8db3226bdc4e6c29e28723e87ef2a0f4c897f9ff8a9018a33c0953f4c89.
14 targeted Python tests passed; GTK load/map/dial rendering and interaction passed;
24 layouts прошли перед добавлением обозначения оценки ёмкости.
Receipt: state-client-build/linux-capacity-20260920/installed.json.
Откат после штатного отключения VPN и закрытия GUI: desktop aliases из *.previous
в том же каталоге; прежний bundle c55149740c24618c. Не удалять состояние активации.
Шестифайловый legacy-архив совместим с прежним updater; preview остаётся ручным архивом.

## Android

0.1.18-beta26 / versionCode 26 / ARM64 установлен поверх beta25 на Redmi Note 9 Pro,
Android 12. Установленный APK сверен по SHA256:
57acefa8c1c5ce0a4735b3a89d9f6251a3a4c1a2f9fd68f657034de9f0e2fc09 (36395084 bytes).
Постоянная beta-подпись: 67a90d1bfcd5a2c0666f0cff1b0ac5e43aaa661ca1196f89e879aa39fe20848a.
Кнопка/переключатель под кругом заменены шкалой; круг сохраняет управление подключением.
143 JUnit tests passed, lint 0 errors (18 warnings), APK ABI/payload/подпись проверены.
Финальный APK собран с Python 3.10; первоначальная сборка с системным Python не прошла
проверку bytecode и не устанавливалась. Четыре runtime-теста карты, круга и главного
экрана passed; отрисовка показывает живую нагрузку ≈20%. VPN в этих тестах не включался.
Артефакты, точный snapshot 180 исходных файлов и хеши:
state-client-build/android-pilots/beta26/ (ignored, ключей в snapshot нет).
Root Android содержит ранее принятые, ещё не перенесённые в scoped release branch
изменения; Windows commit не является полным Android source revision.
Откат без удаления данных — новый исправленный APK с более высоким versionCode,
подписанный прежним beta-ключом. Не удалять приложение ради downgrade.

## Windows

Source a1be617f4fae2eac82ef5945bd7e36c325f891a5, 0.2.9 manual preview.
Client builds 35506170039: windows/linux jobs success; Android setup failed отдельно.
Desktop visual checks 35506170233 success; реальная Windows-отрисовка просмотрена.
Native AWG 35506170083 success. Локальный cross-build: 0 errors, 0 warnings.
Native TCP 35506170019 остановился до тестовых раундов: UDP fixture bind WinError10013.
Диагностика 35506659612 подтвердила конфликт тестового порта. Исправление стенда
234734a резервирует TCP/UDP до старта, ограничивает повтор 32 попытками только для
10013/10048. Повторный native TCP 35506712715 ещё проверяется на 11:13 UTC; UI/installer/AWG
проверки этого исходного кода уже завершены успешно.
Installer artifact 10603579913, digest
sha256:c3fa041702c32096b4393fae53c04496358493e1d6c6ccc9c03f20f9af176d82.
Отдельный tag desktop-preview-20260920-a1be617 опубликован, run35507071302 success.
Installer FamilyConnect-Setup-0.2.9-preview-a1be617.exe, 49933632 bytes,
SHA256 761365eb886bdf6e416c1a98a5de92ba1249271d35dd4ae7eb98bf077b2e2a85.
Установщик скачан из release и сверен с receipt проверенного CI-артефакта.
Два первых запуска35506773406/35506931449 получили403 при создании release:
CI-токен не мог создать source tag; тег опубликован через авторизованный Git,
после чего выпуск создан с --verify-tag. Старые теги/файлы не заменялись.
Физического Windows-ПК сейчас нет; установку и пользовательскую VPN-матрицу не заявляем.

## Осталось

Проверить итог длительного повторного TCP35506712715.
Публичная https://185.251.89.19:8443/invite/ содержит beta26/Linux3ef22e/Windowsa1be617.
Все четыре файла (три клиента и инструкция) скачаны целиком, размеры/SHA256 совпали;
HTML/CSP/no-store и прежний universal beta13 URL проверены.
Машиночитаемый отчёт: 2026-09-20-server-load-downloads.json.
Server staging: /opt/apps/family_connect/state-product-https/config/load-platforms-20260920.
Откат страницы: вернуть invite.html, nginx.conf и nginx-final.conf из соседних
*.before-load-platforms-20260920, проверить nginx -t -c /etc/fc/nginx.conf
в family-connect-product-https и послать HUP только этому контейнеру.
Старые APK/архивы/installer и прежние ссылки сохранены; новые файлы не перезаписывать.
Старые файлы и подписанные каталоги обновления не заменялись.
Глобально остаёмся на этапе4; российской сети для живой проверки нет.

Android «Проверить обновления» и обновление из приложения пока НЕ реализованы.
Ближайшая отдельная задача: показать текущую/новую версию, проверить подписанные
метаданные и APK hash/signing identity, скачать APK, открыть системное подтверждение
установки; корректно обработать отсутствие обновления/сети и сохранить активацию.
Текущий путь — ручной APK поверх установленного приложения с той же подписью.
