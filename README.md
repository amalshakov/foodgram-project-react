# Проект «Продуктовый помощник»
Проект «Продуктовый помощник». Создан для публикции рецептов. Это сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
### https://malshakovfoodgram.hopto.org/
### доступ в админку:
- login: admin
- email: admin@fake.ru
- password: change_me
### Запустите проект в контейнерах:
- клонируйте проект:
```
git clone git@github.com:amalshakov/foodgram-project-react.git
```
- Заполните файл .env на основе файла .env.example
- Запустите docker-compose в директории infra
```
sudo docker-compose up -d --build
```
- Выполните миграции
```
sudo docker-compose exec backend python manage.py migrate
```
- Создайте суперпользователя
```
sudo docker-compose exec backend python manage.py createsuperuser
```
- Соберите статику
```
sudo docker-compose exec backend python manage.py collectstatic --no-input
```
- Загрузите ингредиенты в БД
```
sudo docker-compose exec backend python manage.py import_ingredients
```
## Технологии:
- Python
- Django Rest Framework
- Docker
- Nginx
- Postgres
## Автор:
- [Мальшаков Александр](https://github.com/amalshakov)
