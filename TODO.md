# TODO

## Architecture

- [ ] Cache перезаписывает вместо дополнения — повторная отправка при исчезновении и возврате статьи в фид
- [ ] `read()` возвращает `None` как индикатор первого запуска — неочевидно, лучше пустая коллекция + флаг
- [ ] Cache ID из `__repr__` — хрупко, формат может измениться

## Performance

- [ ] Новый `httpx.Client` на каждый запрос — нет переиспользования TCP/TLS

## Security

- [ ] Telegram token в URL — утечка через tracebacks
- [ ] Jinja2 без sandboxing — потенциальный SSTI из YAML-конфига
- [ ] Sentry отправляет данные статей

## Reliability

- [ ] Нет retry с exponential backoff

## Tests

- [ ] Тесты на cache (`InMemoryCache`, `FilesCache`)
- [ ] Тесты на config parsing (`cli/config.py`)

## Infrastructure

- [ ] Нет JSON Schema для YAML-конфига
- [ ] Нет correlation-id на запусках tick (нужен epyxid)
