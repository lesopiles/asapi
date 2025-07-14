from flask import Flask, request, Response
from flask_caching import Cache
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import logging
import signal
import sys
import json
from time import time
from scraper import Scraper
import atexit
from dotenv import load_dotenv
import os

# Конфигурация flask
app = Flask(__name__)
app.config['CACHE_TYPE'] = 'SimpleCache'  
app.config['CACHE_DEFAULT_TIMEOUT'] = 3600 # Кэш храним час
CORS(app)
cache = Cache(app)

# Логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
logger = logging.getLogger(__name__)

# Настройка воркеров для многопоточности
MAX_WORKERS = 3 # число ядер * 1.5
executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
driver_pool = []
pool_lock = Lock()

# Настройки URL для скрапинга (загружаются из .env файла)
# SEARCHPAGE_URL: Базовый URL для поиска автомобилей
# CARPAGE_URL: Базовый URL для страницы с деталями автомобиля
load_dotenv()
SEARCHPAGE_URL = os.getenv("SEARCHPAGE_URL")
CARPAGE_URL = os.getenv("CARPAGE_URL")

def handle_shutdown(signum, frame):
    """
    Обработчик сигналов завершения работы приложения.

    :param signum: Номер сигнала.
    :type signum: int
    :param frame: Текущий стек вызовов.
    :type frame: frame
    """
    logger.info("Shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

def create_driver():
    """
    Создает и настраивает экземпляр Chrome WebDriver.
ls
    :return: Настроенный экземпляр WebDriver.
    :rtype: webdriver.Chrome
    """
    chrome_service = Service(executable_path='/usr/bin/chromedriver')
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1280,720")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    return driver

def cleanup():
    """
    Очищает пул драйверов при завершении работы приложения.
    """
    with pool_lock:
        for driver in driver_pool:
            driver.quit()
        driver_pool.clear()
atexit.register(cleanup)

@app.route("/api/v1/cars", methods=["GET"])
def get_cars():
    """
    Получение списка автомобилей с возможностью фильтрации, сортировки и пагинации.
    
    Поддерживаемые параметры запроса:
    - brand: Марка автомобиля (опционально)
    - model: Модель автомобиля (опционально)
    - gen: Поколение модели (опционально)
    - page_num: Номер страницы (по умолчанию '1')
    - year_from: Год выпуска от (опционально)
    - year_to: Год выпуска до (опционально)
    - price_from: Цена от (опционально)
    - price_to: Цена до (опционально)
    - order_by: Параметр сортировки (опционально)
    
    Returns:
        Response: JSON ответ с данными об автомобилях и информацией о пагинации
        
    Пример запроса:
        GET /api/v1/cars?brand=Toyota&model=Camry&page_num=2&order_by=sort__price_desc
        
    Структура ответа:
    {
        "success": boolean,  # Статус выполнения запроса
        "count": integer,    # Количество найденных автомобилей
        "page_info": {       # Информация о пагинации
            "pages_nums": [string],  # Доступные страницы
            "cur_page_num": string   # Текущая страница
        },
        "cars": [            # Список автомобилей
            {
                "id": string,        # Уникальный идентификатор
                "title": string,     # Название автомобиля
                "price": string,     # Цена
                "year": string,      # Год выпуска
                "image": string,     # URL изображения
                "fuel": string,      # Тип топлива
                "mileage": string,   # Пробег
                "color": string      # Цвет
            },
            ...
        ]
    }
    
    Коды статуса HTTP:
    - 200: Успешный запрос
    - 404: Данные не найдены
    - 500: Внутренняя ошибка сервера
    - 504: Таймаут при ожидании ответа от сайта
    """
    filters = {
        "brand": request.args.get("brand"),
        "model": request.args.get("model"),
        "gen": request.args.get("gen"),
        "transmission": request.args.get("transmission"),
        "fuel": request.args.get("fuel"),
        "color": request.args.get("color"),
        "mileage_from": request.args.get("mileage_from"),
        "mileage_to": request.args.get("mileage_to"),
        "year_release_from": request.args.get("year_from"),
        "year_release_to": request.args.get("year_to"),
        "price_from": request.args.get("price_from"),
        "price_to": request.args.get("price_to")
    }

    order_by = request.args.get("order_by")

    page_num = request.args.get("page_num", default="1")

    def task():
        with pool_lock:
            driver = driver_pool.pop() if driver_pool else create_driver()
        
        try:
            scraper = Scraper(
                url=SEARCHPAGE_URL,
                driver=driver
            )
            cars_data = scraper.scrape_cars(page_num, filters, order_by=order_by)

            return Response(
                json.dumps({
                    "success": True,
                    "count": len(cars_data),
                    "page_info": scraper._get_pages_nums(),
                    "cars": cars_data
                }, ensure_ascii=False, indent=2),
                status=200,
                content_type='application/json; charset=utf-8'
            )
            
        except NoSuchElementException:
            return Response(
                json.dumps({
                    "success": False,
                    "error": "Данные не найдены"
                }, ensure_ascii=False, indent=2),
                status=404,
                mimetype='application/json; charset=utf-8'
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                    json.dumps({
                        "success": False,
                        "error": str(e)
                    }, ensure_ascii=False, indent=2),
                    status=500,
                    mimetype='application/json; charset=utf-8'
                )
            
        finally:
            with pool_lock:
                driver_pool.append(driver)

    try:
        future = executor.submit(task)
        return future.result(timeout=30)
    except TimeoutException:
        return Response(
            json.dumps({
                "success": False,
                "error": "Сайт не отвечает"
            }, ensure_ascii=False, indent=2),
            status=504,
            mimetype='application/json; charset=utf-8'
        )

@app.route("/api/v1/cars/filters", methods=["GET"])
@cache.cached(make_cache_key=lambda: f"filters_{frozenset(request.args.items())}")
def get_filters():
    """
    Получение всех доступных фильтров для поиска автомобилей.

    :return: JSON со всеми доступными значениями фильтров
    :rtype: flask.Response

    :Example HTTP GET:
        GET /api/v1/cars/filters

    :Example Response:
        {
            "success": true,
            "filters": {
                "brands": ["Toyota", "Honda", "BMW", "Audi"],
                "models": ["Camry", "Corolla", "Accord", "Civic"],
                "transmission": ["Автомат", "Механика", "Робот"],
                "fuel": ["Бензин", "Дизель", "Гибрид", "Электро"],
                "color": ["Белый", "Чёрный", "Серебристый", "Красный"],
                "mileage_from": ["0 км", "10 000 км", "50 000 км"],
                "mileage_to": ["50 000 км", "100 000 км", "150 000 км"],
                "year_release_from": ["2010", "2015", "2020"],
                "year_release_to": ["2015", "2020", "2023"],
                "price_from": ["500 000 ₽", "1 000 000 ₽", "2 000 000 ₽"],
                "price_to": ["1 000 000 ₽", "2 000 000 ₽", "3 000 000 ₽"]
            }
        }

    :status 200: Успешный запрос
    :status 404: Фильтры не найдены
    :status 500: Внутренняя ошибка сервера
    """
    def task():
        with pool_lock:
            driver = driver_pool.pop() if driver_pool else create_driver()
        
        try:
            scraper = Scraper(
                url=SEARCHPAGE_URL,
                driver=driver
            )
            filters_data = scraper.scrape_filters()

            return Response(
                json.dumps({
                    "success": True,
                    "count": len(filters_data),
                    "filters": filters_data
                }, ensure_ascii=False, indent=2),
                status=200,
                content_type='application/json; charset=utf-8'
            )
            
        except NoSuchElementException:
            return Response(
                json.dumps({
                    "success": False,
                    "error": "Данные не найдены"
                }, ensure_ascii=False, indent=2),
                status=404,
                mimetype='application/json; charset=utf-8'
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                    json.dumps({
                        "success": False,
                        "error": str(e)
                    }, ensure_ascii=False, indent=2),
                    status=500,
                    mimetype='application/json; charset=utf-8'
                )
            
        finally:
            with pool_lock:
                driver_pool.append(driver)

    try:
        future = executor.submit(task)
        return future.result(timeout=30)
    except TimeoutException:
        return Response(
            json.dumps({
                "success": False,
                "error": "Сайт не отвечает"
            }, ensure_ascii=False, indent=2),
            status=504,
            mimetype='application/json; charset=utf-8'
        )

@app.route("/api/v1/cars/filters/models", methods=["GET"])
@cache.cached(make_cache_key=lambda: f"filters_models_{frozenset(request.args.items())}")
def get_brand_models():
    """
    Получение списка моделей для указанной марки.

    :query brand: Марка автомобиля (обязательно)

    :return: JSON со списком моделей
    :rtype: flask.Response

    :Example HTTP GET:
        GET /api/v1/cars/filters/models?brand=Toyota

    :Example Response:
        {
            "success": true,
            "models": ["Camry", "Corolla", "RAV4"]
        }
    """
    brand = request.args.get("brand")

    def task():
        with pool_lock:
            driver = driver_pool.pop() if driver_pool else create_driver()
        
        try:
            scraper = Scraper(
                url=SEARCHPAGE_URL,
                driver=driver
            )
            models_data = scraper.scrape_brand_models(brand)

            return Response(
                json.dumps({
                    "success": True,
                    "count": len(models_data),
                    "models": models_data
                }, ensure_ascii=False, indent=2),
                status=200,
                content_type='application/json; charset=utf-8'
            )
            
        except NoSuchElementException:
            return Response(
                json.dumps({
                    "success": False,
                    "error": "Данные не найдены"
                }, ensure_ascii=False, indent=2),
                status=404,
                mimetype='application/json; charset=utf-8'
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                    json.dumps({
                        "success": False,
                        "error": str(e)
                    }, ensure_ascii=False, indent=2),
                    status=500,
                    mimetype='application/json; charset=utf-8'
                )
            
        finally:
            with pool_lock:
                driver_pool.append(driver)

    try:
        future = executor.submit(task)
        return future.result(timeout=30)
    except TimeoutException:
        return Response(
            json.dumps({
                "success": False,
                "error": "Сайт не отвечает"
            }, ensure_ascii=False, indent=2),
            status=504,
            mimetype='application/json; charset=utf-8'
        )

@app.route("/api/v1/cars/filters/gens", methods=["GET"])
@cache.cached(make_cache_key=lambda: f"filters_gens_{frozenset(request.args.items())}")
def get_model_gens():
    """
    Получение списка поколений для указанной модели и марки.

    :query brand: Марка автомобиля (обязательно)
    :query model: Модель автомобиля (обязательно)

    :return: JSON со списком поколений
    :rtype: flask.Response

    :Example HTTP GET:
        GET /api/v1/cars/filters/gens?brand=Toyota&model=Camry

    :Example Response:
        {
            "success": true,
            "gens": ["VII (2017-2020)", "VIII (2021-2023)"]
        }
    """
    brand = request.args.get("brand")
    model = request.args.get("model")

    def task():
        with pool_lock:
            driver = driver_pool.pop() if driver_pool else create_driver()
        
        try:
            scraper = Scraper(
                url=SEARCHPAGE_URL,
                driver=driver
            )
            gens_data = scraper.scrape_model_gens(brand, model)

            return Response(
                json.dumps({
                    "success": True,
                    "count": len(gens_data),
                    "gens": gens_data
                }, ensure_ascii=False, indent=2),
                status=200,
                content_type='application/json; charset=utf-8'
            )
            
        except NoSuchElementException:
            return Response(
                json.dumps({
                    "success": False,
                    "error": "Данные не найдены"
                }, ensure_ascii=False, indent=2),
                status=404,
                mimetype='application/json; charset=utf-8'
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                    json.dumps({
                        "success": False,
                        "error": str(e)
                    }, ensure_ascii=False, indent=2),
                    status=500,
                    mimetype='application/json; charset=utf-8'
                )
            
        finally:
            with pool_lock:
                driver_pool.append(driver)

    try:
        future = executor.submit(task)
        return future.result(timeout=30)
    except TimeoutException:
        return Response(
            json.dumps({
                "success": False,
                "error": "Сайт не отвечает"
            }, ensure_ascii=False, indent=2),
            status=504,
            mimetype='application/json; charset=utf-8'
        )

@app.route("/api/v1/cars/<id>", methods=["GET"])
def get_car_details(id):
    """
    Получение детальной информации об автомобиле по ID.

    :param id: Уникальный идентификатор автомобиля (обязательно)
    :type id: str

    :return: JSON с полной информацией об автомобиле
    :rtype: flask.Response

    :Example HTTP GET:
        GET /api/v1/cars/10420276

    :Example Response:
        {
            "success": true,
            "car": {
                "id": "10420276",
                "title": "Toyota Camry 2020",
                "price": "1 200 000 ₽",
                "photos": [
                    "https://example.com/photo1.jpg",
                    "https://example.com/photo2.jpg"
                ],
                "base_parameters": {
                    "Год выпуска": "2020",
                    "Пробег": "50 000 км",
                    "Двигатель": "2.5 л / 181 л.с.",
                    "Коробка передач": "Автоматическая",
                    "Привод": "Передний",
                    "Цвет": "Серебристый"
                },
                "tech_parameters": {
                    "Мощность двигателя": "181 л.с.",
                    "Тип топлива": "Бензин",
                    "Разгон до 100 км/ч": "8.5 сек"
                },
                "car_check_parameters": {
                    "Состояние": "Не битый",
                    "ПТС": "Оригинал",
                    "Владельцев": "1"
                },
                "inspections": [
                    {
                        "section": "Кузов",
                        "parameter": "Лобовое стекло",
                        "value": "Царапины"
                    },
                    {
                        "section": "Двигатель",
                        "parameter": "Состояние",
                        "value": "Отличное"
                    }
                ],
                "car_body_options": {
                    "Комфорт": ["Климат-контроль", "Подогрев сидений"],
                    "Безопасность": ["Парктроник", "Камера заднего вида"]
                }
            }
        }

    :status 200: Успешный запрос
    :status 404: Автомобиль не найден
    :status 500: Внутренняя ошибка сервера
    """
    def task():
        with pool_lock:
            driver = driver_pool.pop() if driver_pool else create_driver()
        
        try:
            scraper = Scraper(
                url=CARPAGE_URL+str(id),
                driver=driver
            )
            car_data = scraper.scrape_car_details(id)

            return Response(
                json.dumps({
                    "success": True,
                    "count": len(car_data),
                    "cars": car_data
                }, ensure_ascii=False, indent=2),
                status=200,
                content_type='application/json; charset=utf-8'
            )
            
        except NoSuchElementException:
            return Response(
                json.dumps({
                    "success": False,
                    "error": "Данные не найдены"
                }, ensure_ascii=False, indent=2),
                status=404,
                mimetype='application/json; charset=utf-8'
            )
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return Response(
                    json.dumps({
                        "success": False,
                        "error": str(e)
                    }, ensure_ascii=False, indent=2),
                    status=500,
                    mimetype='application/json; charset=utf-8'
                )
            
        finally:
            with pool_lock:
                driver_pool.append(driver)

    try:
        future = executor.submit(task)
        return future.result(timeout=30)
    except TimeoutException:
        return Response(
            json.dumps({
                "success": False,
                "error": "Сайт не отвечает"
            }, ensure_ascii=False, indent=2),
            status=504,
            mimetype='application/json; charset=utf-8'
        )
    
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, threaded=True, debug=True)
    