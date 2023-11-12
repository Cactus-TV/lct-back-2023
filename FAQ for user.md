# Переменные среды в файле .env для запуска:
__DEBUG=False__ - включение/выключение дебага в Django
__ALLOWED_HOSTS=localhost|127.0.0.1|0.0.0.0__ - разрешённые хосты (через |)
__MEDIA_PATH=media/__ - путь до папка с сохранёнными фото
__RABBITMQ_QUEUE_NAME_POST=test_rtsp_get_1|test_rtsp_get_2__ - имя очередей из экземпляров контейнеров с нейросетью на get (через |)
__RABBITMQ_QUEUE_NAME_GET=test_rtsp_post_1|test_rtsp_post_2__ - имя очередей из экземпляров контейнеров с нейросетью на post (через |)
__RABBITMQ_LOGIN=test_user__ - логин в RabbitMQ
__RABBITMQ_PASSSWORD=test__ - пароль от RabbitMQ
__RABBITMQ_PORT=5672__ - стандартный порт RabbitMQ
__RABBITMQ_HOST=255.255.255.255__ - ip сервера
