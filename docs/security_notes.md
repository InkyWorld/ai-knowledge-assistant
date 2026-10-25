# Security notes — Text-to-SQL (Day 25)

Стан: 25.10.2026. Стосується шляху `generate_sql` → `app/db/sql_guard.validate_and_normalize` → `app/db/readonly.run_readonly_query`.

## Що захищено

- **Роль.** Окрема роль `assistant_ro` (`scripts/sql/create_readonly_role.sql`): лише `GRANT SELECT ON documents`, решта таблиць відкликана (`REVOKE ALL`), `default_transaction_read_only = on`.
- **Один запит.** Guard приймає рівно один statement і лише звичайний `SELECT` — будь-які `INSERT/UPDATE/DELETE/DROP/DDL/COPY/INTO/UNION`-мутації відкидаються (`SqlRejected`).
- **Білий список таблиць.** Дозволена тільки `documents` (+ CTE запиту); таблиці зі схемою/каталогом (`pg_catalog.*`, `public.*`) заборонені.
- **LIMIT.** Примусове обмеження `MAX_LIMIT = 100` для `LIMIT n` і `FETCH FIRST n ROWS` (включно з `WITH TIES`).
- **EXPLAIN.** Перед виконанням — `EXPLAIN (FORMAT JSON)`; план із `Total Cost > 10000` відхиляється до виконання запиту.
- **Таймаут.** `statement_timeout = 5000ms` на з'єднанні readonly-ролі (`connect_args`) + `SET TRANSACTION READ ONLY` у сесії.

Перевірка: `tests/security/test_sql_guard.py` (REJECTED-кейси, clamp) і
`tests/security/test_readonly_role.py` (інтеграційно: роль не пише, не бачить чужі таблиці, дорогий запит відхиляється).

## Чого немає (відомі обмеження)

- **Чорний список функцій неповний.** `DENY_FUNCS` у `app/db/sql_guard.py` — лише перелік відомих небезпечних функцій PG (`pg_sleep`, `pg_read_file` тощо); нові/менш очевидні функції можуть пройти, якщо їх немає в списку.
- **Немає ізоляції за користувачами.** Каталог `documents` спільний: будь-хто з доступом до запиту бачить усі рядки; обмежень на рівень користувача/команди немає.
- **Результат запиту — недовірені дані.** Рядки з БД передаються далі (у відповідь/ланцюг LLM) без екранування: значення з `title`/`file_source` можуть містити prompt-інструкції — на них не можна покладатися як на інструкції.

## Не є захистом від

- складних дорогих запитів, що вписуються в `MAX_COST` (поріг статичний);
- DoS через багаторазові запити в межах ліміту (rate limiting на рівні API відсутній).
