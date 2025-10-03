#!/bin/bash
set -e
set -a
source /opt/star-burger/.env
set +a

echo "Запуск виртуального окружения"
source /opt/star-burger/venv/bin/activate
echo ""

echo "Обновление кода с github"
git pull
echo ""

echo "Обновляем библиотеки"
pip install -r requirements.txt
echo ""

echo "Устанавливаем Node.js-библиотеки и собираем фронтенд"
npm install
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
echo ""

echo "Миграции"
python3 manage.py migrate
echo ""

echo "Сбор статики"
python3 manage.py collectstatic --noinput
echo ""

echo "Перезапускаем сервисы"
sudo systemctl restart star-burger
sudo nginx -s reload
echo ""

echo "Сообщаем Rollbar о деплое"
curl https://api.rollbar.com/api/1/deploy/ \
  -F access_token=$ROLLBAR_ACCESS_TOKEN \
  -F environment=production \
  -F revision=$(git rev-parse HEAD) \
  -F local_username=$(whoami)
echo ""

echo "Деплой завершён"

