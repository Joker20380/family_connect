# Windows Friends: первая живая проверка

Принятый source:7835b4feecc9383fc4cdb13e8071411facb27bf1.
[Сборка и platform jobs](https://github.com/Joker20380/family_connect/actions/runs/35495850992).
[Скачать Windows ZIP](https://github.com/Joker20380/family_connect/actions/runs/35495850992/artifacts/10600990083).
Для скачивания GitHub Actions artifact может понадобиться вход в GitHub.
Выбирайте `FamilyConnect-Windows-Installer-pilot-unsigned`, не старый releasev0.2.9.
Это тестовая неподписанная сборка, внутренний installer version0.2.9.

1. Скачайте ZIP на Windows. SHA256 ZIP (из GitHub artifact metadata):
   `86129b9ad5f8c026d23727d3d283214474d7ac9df59c921d179a128efeaf4904`.
   Проверка: `Get-FileHash .\FamilyConnect-Windows-Installer-pilot-unsigned.zip -Algorithm SHA256`.
   Если браузер изменил имя, подставьте фактический путь. Распакуйте архив.
   Сверьте EXE с файлом SHA256SUMS внутри; установите FamilyConnect-Setup-0.2.9-pilot-unsigned.exe.
2. Откройте Family Connect → «Доступ по приглашению». При первой активации Windows
   нужен отдельный неиспользованный код FC-…: код Linux/Android повторно не подходит.
   На уже активированном Linux/Android получите «Ссылку для друга», откройте страницу
   и получите новый код; перенесите его на Windows и нажмите «Активировать».
   Если Windows уже активирован, повторная активация не нужна. Не отправляйте код в чат.
3. Выберите «Нидерланды» и «TCP REALITY» → «Подключиться». Дождитесь результата,
   откройте обычный сайт. Затем отключитесь в главном окне и проверьте интернет снова.
   Сообщите результат подключения/отключения и точный текст ошибки, если она есть.

Первый проход только NL/TCP; AWG3.1 и другая страна — после успешного отключения.
CI уже проверил install/service/driver/broker/UI/scaling/uninstall; это не результат
живой проверки на ПК пользователя. РФ-сети нет, обход блокировок в РФ не подтверждён.

При ошибке сначала штатное «Отключить»; не удалять device identity/journal для обхода
восстановления. Не удалять старую установку заранее: удаление может затронуть данные.
Если требуется rollback, остановить VPN и вернуться к прежнему проверенному installer,
сохранив identity/configuration storage; CI artifact не является новым публичным release.
