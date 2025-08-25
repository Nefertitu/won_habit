# Проект 'won_habit'

Проект 'won_habit' - бэкенд-часть SPA веб-приложения, являющегося трекером 
полезных привычек.

В 2018 году Джеймс Клир написал книгу «Атомные привычки», которая посвящена 
приобретению новых полезных привычек и искоренению старых плохих привычек.
Идея данной книги и взята за основу для содания проекта 'won_habit'/

Привычка - это конкретное действие, которое можно уложить в одно предложение:
я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО].

За каждую полезную привычку необходимо себя вознаграждать или сразу после 
делать приятную привычку. Но при этом привычка не должна расходовать на 
выполнение больше двух минут.

Чем отличается полезная привычка от приятной и связанной?
Полезная привычка — это само действие, которое пользователь будет совершать и 
получать за его выполнение определенное вознаграждение (приятная привычка или 
любое другое вознаграждение).

Приятная привычка — это способ вознаградить себя за выполнение полезной привычки.

Например: в качестве полезной привычки вы будете выходить на прогулку вокруг 
квартала сразу же после ужина. Вашим вознаграждением за это будет приятная 
привычка — принять ванну с пеной. То есть такая полезная привычка будет иметь 
связанную привычку.

## Локальная установка и запуск проекта через Docker Compose

1. Клонируйте репозиторий:
```
git clone https://github.com/Nefertitu/won_habit
```
или
```
git clone git@github.com:Nefertitu/won_habit.git
```

```
cd won_habit
```

2. Скопируйте `.env.example` в `.env` и заполните переменные окружения:
   ```
   cp .env.sample .env
   ```
   
2. Запустите проект:
    ```
    docker-compose build --no-cache
    docker-compose up -d
    ```
   
3. Проверьте работоспособность (проверка логов):

- Откройте в браузере: http://localhost:8000

- База данных: 
```
   docker-compose logs db

```
```
  docker-compose exec db psql -U your_user -d your_db
```

- Redis:
```
   docker-compose logs redis
```
```
   docker-compose exec redis redis-cli ping
```

- Celery: 
```
   docker-compose logs celery
```
```
   docker-compose exec celery celery -A config status

```


- Celery Beat: 
```
   docker-compose logs celery-beat
```

- Выполните миграции и создайте суперпользователя:
```
docker-compose exec web python manage.py migrate
```
```
docker-compose exec web python manage.py csu
```
- Откройте в браузере: http://localhost:8000/admin/


## Настройка виртуальной машины (предварительная подготовка для деплоя):

** Предварительные требования:
- Yandex Cloud аккаунт
- Доступ по SSH
- Ubuntu 22.04 LTS или новее

1. Пошаговая настройка

* Подключение к VM:
```
ssh username@your-vm-ip
```
* Обновление системы
```
sudo apt update && sudo apt upgrade -y
```
* Установка Docker
```
sudo apt install docker.io docker-compose-plugin -y
sudo systemctl enable docker
sudo systemctl start docker
```
* Установка Python
```
sudo apt install python3 python3-pip python3-venv -y
```
* Установка Poetry
```
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```
* Настройка прав
```
sudo usermod -aG docker $USER
newgrp docker
```

##  Автоматический деплой на сервер через GitHub Actions

При push в ветку `development` автоматически запускается CI/CD pipeline который:

✅ Тестирует код
✅ Собирает Docker образы  
✅ Деплоит на сервер
✅ Применяет миграции
✅ Собирает статические файлы
✅ Перезапускает сервисы

*Подробнее в [.github/workflows/ci.yml](.github/workflows/ci.yml)*


1. Форкните репозиторий
Перейдите на https://github.com/Nefertitu/won_habit и нажмите "Fork"

2. Настройте сервер (Docker + Git)
```
ssh your_username@your_server_ip
```

3. Установите Docker и Git:
```
sudo apt update && sudo apt install docker.io docker-compose-plugin git -y
sudo usermod -aG docker $USER
newgrp docker
```
4. Настройте секреты в GitHub:
* В вашем форкнутом репозитории перейдите в Settings → Secrets → Actions
* Добавьте следующие секреты:
- DJANGO_SECRET_KEY - секретный ключ Django, можно сгенерировать: openssl rand -base64 32
- DOCKER_HUB_TOKEN - Токен из Docker Hub account settings
- DOCKER_HUB_USERNAME - Username из Docker Hub account settings
- SSH_USER - имя пользователя на сервере
- SERVER_IP - IP-адрес вашего сервера
- SSH_KEY - приватный SSH ключ
- POSTGRES_USER - postgres (или ваше значение)
- POSTGRES_PASSWORD - ваш_пароль
- POSTGRES_DB - won_habit
- POSTGRES_PORT - 5432
- POSTGRES_SUPERUSER_PASSWORD - postgres

4. Проверка работоспособности:
* После деплоя проверьте:
- Статус контейнеров
```
docker-compose ps
```
- Логи приложения
```
docker-compose logs web
```
- Проверьте API
```
curl http://your-server-ip/api/courses/
```
7. Доступ к админке:

* Для первого входа создайте суперпользователя:
```
docker-compose exec web python manage.py csu
```
* Откройте в браузере: http://your-server-ip/admin/