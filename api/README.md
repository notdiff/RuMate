# API интерфейс
При развертывании необходимо скачать файлы [документации](https://drive.google.com/file/d/10n-65J4MK5kf58vs1DZ965eW3ceCEfKy/view?usp=sharing).
Необходимо разместить папку в директории `full_docs`

### Представленно 3 файла с инфренсом
* [mistral_search.py](https://github.com/notdiff/RuMate/blob/main/api/mistral_search.py) - инференс полностью локальной модели mistralai/Mistral-7B-v0.3
* [search_agents.py](https://github.com/notdiff/RuMate/blob/main/api/search_agents.py) - работа агентов на основе LLM
* [yandex_search.py](https://github.com/notdiff/RuMate/blob/main/api/yandex_search.py) - обработка через api yandexGPT

### Остальные файлы
* [main.py](https://github.com/notdiff/RuMate/blob/main/api/main.py) - основной файл api, со всем эндпоинтами
* [parce.py](https://github.com/notdiff/RuMate/blob/main/api/parce.py) - файл автоматического парсера
