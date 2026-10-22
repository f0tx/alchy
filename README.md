# alchy — личный оверлей Gentoo

Локальный оверлей для пакетов, которых нет в дереве, либо для ebuild'ов, приведённых
в рабочее состояние: PHP-патчи под новый toolchain, PECL-расширения под старые слоты PHP,
openldap 2.7 и т.п.

## Что внутри

- `dev-lang/php` — ebuild'ы 5.4.45, 5.6.40_p*, 7.2.34, 7.4.33_p*, 8.5.2 с набором патчей
  (`files/php-*-regen/` — инструменты пересадки патчей на чистое дерево);
- `dev-php/pecl-memcached` (2.2.0 → PHP 5.6, 3.2.0 → 7.2, 3.4.0-r2 → 7.4) и
  `dev-php/pecl-memcache` (3.0.8 → 5.4) — чтобы `session.save_handler = memcached/memcache`
  работал на всех слотах;
- `dev-python/sphinx-rtd-theme` — снятые верхние границы зависимостей;
- `net-nds/openldap-2.7.1`, `net-wireless/*`, `app-crypt/*`, `www-servers/*` и прочее.

## Подключение

`/etc/portage/repos.conf/alchy.conf`:

```ini
[alchy]
location = /var/db/repos/alchy
masters = gentoo
auto-sync = no
priority = 50
```

Репозиторий не синхронизируется пакетным менеджером (`auto-sync = no`) — обновление
делается `git pull` в `location`. Высокий `priority` нужен, чтобы здешние ebuild'ы
перекрывали одноимённые из `::gentoo`.

Требуется `thin-manifests = true` (задано в `metadata/layout.conf`), манифесты — BLAKE2B.

## Формат

- `metadata/layout.conf`, `profiles/` — стандартная раскладка оверлея;
- ebuild'ы `~amd64`, ключи принимаются через `/etc/portage/package.accept_keywords/`.