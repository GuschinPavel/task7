
## Быстрый запуск через Docker

git clone https://github.com/GuschinPavel/task7

cd task7

docker compose up -d



Интерактивная документация Swagger UI будет доступна по адресу:  
http://127.0.0.1:8008/docs

## Как проверить работу в Swagger UI

1. Выполните **`POST /register`**, создав пользователя (например, `username: "alex"`, `email: "alex@example.com"`, `password: "secret123"`).
2. Выполните **`POST /login`** с тем же `username` и `password` — скопируйте значение поля `access_token` из ответа.
3. Нажмите кнопку **Authorize** (с замком в правом верхнем углу Swagger UI), вставьте скопированный токен и нажмите **Authorize**.
4. Выполните **`GET /users/me`** или **`GET /protected`** — запрос пройдет успешно. Без токена маршруты вернут `401 Unauthorized` / `403 Forbidden`.

## Эндпоинты

| Метод | Путь | Доступ | Описание |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Публичный | Регистрация нового пользователя |
| `POST` | `/login` | Публичный | Вход и получение JWT-токена |
| `GET` | `/users/me` | Защищенный (Bearer) | Данные текущего авторизованного пользователя |
| `GET` | `/protected` | Защищенный (Bearer) | Тестовый защищенный маршрут |
