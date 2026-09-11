# Доверенная первичная поставка TCP Setup

TCP Setup устанавливает root-owned updater, который затем проверяет подписанный
TCP-компонент. Bootstrap0.1.0 не запускает VPN и не включает профили/приватные ключи.
Это отдельный архив от desktop0.2.9 и TCP component0.1.0.

До sudo необходимо аутентифицировать архив. SHA256SUMS из того же скачивания проверяет
целостность, но не заменяет доверенный ключ издателя. Отдельная Ed25519-подпись
использует domain family-connect/tcp-setup-release/v1, покрывает версию/архитектуру/
размер/SHA256. App/TCP update catalog signatures не принимаются вместо неё.

Получите tcp_setup_signature.py и update.pub через уже доверенный канал оператора
или доверенный checkout проекта. На уже установленном Linux ключ можно взять из
~/.local/share/family-connect/current/update.pub. Не брать anchor из непроверенного
setup или рядом с ним: на чистом устройстве первоначальное доверие устанавливается
отдельно, например проверкой fingerprint у оператора. Сам скачанный verifier также
должен быть доверенным; подпись не устраняет эту первичную границу доверия.

Нужны python3 и python3-cryptography. В обычном пользовательском терминале:

```sh
python3 /trusted/tcp_setup_signature.py verify \
  --archive FamilyConnect-TCP-Setup-0.1.0.tar.gz \
  --signature tcp-setup-0.1.0.json \
  --anchor /trusted/update.pub --version 0.1.0
```

Только после успешной проверки распакуйте архив в новую личную папку, недоступную
для записи другим пользователям, и запустите sudo python3 -I install.py из неё.
Передача от проверки к исполнению требует сохранения проверенных файлов; не работать
из общей writable папки. Сам install.py проверяет manifest и создаёт private snapshot.
Далее GUI Linux --awg-pilot → «Установить / обновить TCP», либо
pkexec /usr/local/lib/family-connect-tcp-updater/broker install. VPN сам не включается.

Первичная подпись не имеет sequence/expiry: это подпись конкретного immutable release,
а не автоматический каталог обновлений. Verifier требует явную ожидаемую версию;
автоматическое принятие старого подписанного setup не реализовано. Floors последующих
TCP updates отдельные и сохраняются. Проверка не исполняет и не распаковывает архив.

Оператор: CI → новый tcp-setup-vX.Y.Z tag → скачать опубликованный архив → сверить
SHA256/воспроизводимость/CI → локально sign через scripts/tcp_setup_signature.py,
существующий offline key → verify доверенным anchor → опубликовать versioned signature
в updates/tcp-setup-X.Y.Z.json. Не передавать key в CI и не заменять published assets.
Доверенная подпись публикуется после проверки; её отсутствие не разрешает sudo.

## Опубликованный setup0.1.0

- [Архив и SHA256SUMS](https://github.com/Joker20380/family_connect/releases/tag/tcp-setup-v0.1.0)
- [Офлайн-подпись](https://raw.githubusercontent.com/Joker20380/family_connect/main/updates/tcp-setup-0.1.0.json)
- [Verifier source](../scripts/tcp_setup_signature.py), source7eee3c3; его получение
  должно быть доверенным до исполнения. Наличие подписи рядом с архивом не заменяет anchor.

Архив8214B, SHA256 c16c924cac52acc5d3555c38a5260b6f4cdc530b4484a831dc35a47dab025c17.
Fingerprint SHA256 декодированных32B public key: `6a09fb42468acdb4cfcb4f0888e27c13705ac437a45a6624fc21dddbe83fed83`.
Этот fingerprint сверяют по независимо доверенному каналу, не только по этой странице.
