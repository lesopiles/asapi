from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import JavascriptException, TimeoutException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class Scraper:
    """
    Основной класс для парсинга данных об автомобилях с сайта.

    :param url: Базовый URL для парсинга.
    :type url: str
    :param driver: Экземпляр WebDriver для взаимодействия с браузером.
    :type driver: WebDriver

    :ivar _filters_map: Соответствие между именами фильтров в API и на сайте.
    :vartype _filters_map: Dict[str, str]
    """
    
    def __init__(self, url: str, driver: WebDriver):
        self.driver = driver
        self.url = url
        self._filters_map = {
            'brand': 'brand',
            'model': 'model',
            'gen': 'gen',
            'transmission': 'transmission',
            'fuel': 'fuel',
            'color': 'color',
            'mileage_from': 'mileage_from',
            'mileage_to': 'mileage_to',
            'year_release_from': 'year_release_from',
            'year_release_to': 'year_release_to',
            'price_from': 'price_from',
            'price_to': 'price_to'
        }

    def _load_searchpage(self, url: str) -> None:
        """
        Загружает указанную страницу и ожидает её полной загрузки.

        :param url: URL для загрузки.
        :type url: str

        :raises TimeoutException: Если страница не загрузилась за отведенное время.
        """
        self.driver.get(url)
        self._wait_for_loading_searchpage()

    def _load_carpage(self, url: str) -> None:
        """
        Загружает указанную страницу и ожидает её полной загрузки.

        :param url: URL для загрузки.
        :type url: str

        :raises TimeoutException: Если страница не загрузилась за отведенное время.
        """
        self.driver.get(url)
        self._wait_for_loading_carpage()

    def _wait_for_loading_searchpage(self) -> None:
        """
        Ожидает исчезновения индикатора загрузки через JavaScript.

        Реализует асинхронное ожидание с использованием MutationObserver.
        Таймаут ожидания - 30 секунд.

        :raises TimeoutException: Если индикатор загрузки не исчез.
        :raises JavascriptException: При ошибках выполнения JavaScript.
        """
        try:
            result = self.driver.execute_async_script("""
                const callback = arguments[arguments.length - 1];
                const loader = document.querySelector('div.big_preloader');
                
                if (!loader || loader.style.opacity === '0') {
                    callback(true);
                    return;
                }
                
                const observer = new MutationObserver(function(mutations) {
                    if (loader.style.opacity === '0') {
                        observer.disconnect();
                        callback(true);
                    }
                });
                
                observer.observe(loader, {
                    attributes: true,
                    attributeFilter: ['style']
                });
                
                // Таймаут на случай если изменения не произойдут
                setTimeout(() => {
                    observer.disconnect();
                    callback(false);
                }, 30000);
            """)
            
            if not result:
                raise TimeoutException("Loader did not disappear")
        except JavascriptException:
            raise TimeoutException("Page loading timeout")
        
    def _wait_for_loading_carpage(self) -> None:
        """
        Ожидает исчезновения индикатора загрузки через JavaScript.

        Реализует асинхронное ожидание с использованием MutationObserver.
        Таймаут ожидания - 30 секунд.

        :raises TimeoutException: Если индикатор загрузки не исчез.
        :raises JavascriptException: При ошибках выполнения JavaScript.
        """
        try:
            result = self.driver.execute_async_script("""
                const callback = arguments[arguments.length - 1];
                const loader = document.querySelector('div.big_preloader');
                
                // Если прелоадер уже скрыт или отсутствует
                if (!loader || loader.classList.contains('hide')) {
                    callback(true);
                    return;
                }
                
                const observer = new MutationObserver(function(mutations) {
                    if (loader.classList.contains('hide')) {
                        observer.disconnect();
                        callback(true);
                    }
                });
                
                observer.observe(loader, {
                    attributes: true,
                    attributeFilter: ['class']
                });
                
                // Таймаут на случай если изменения не произойдут
                setTimeout(() => {
                    observer.disconnect();
                    callback(false);
                }, 30000);
            """)
            if not result:
                raise TimeoutException("Loader did not disappear")
        except JavascriptException:
            raise TimeoutException("Page loading timeout")

    def _apply_filters(self, filters: Dict[str, str]) -> None:
        """
        Применяет фильтры через JavaScript-скрипты.

        :param filters: Словарь фильтров для применения.
        :type filters: Dict[str, str]

        .. note::
            Для каждого фильтра выполняется:
            1. Поиск соответствующего элемента на странице
            2. Клик по элементу
            3. Выбор указанного значения
            4. Пауза 300мс для применения изменений
        """
        for key, value in filters.items():
            if value and key in self._filters_map:
                field_name = self._filters_map[key]
                self.driver.execute_script(f"""
                    const filter = document.querySelector(
                        'div.select__field[data-field_name="{field_name}"]'
                    );
                    if (filter) {{
                        filter.click();
                        const option = filter.querySelector(
                            'div.select__field__variant[data-label="{value}"]'
                        );
                        if (option) {{
                            option.click();
                            return new Promise(resolve => setTimeout(resolve, 300));
                        }}
                    }}
                """)

    def _submit_search(self) -> None:
        """
        Инициирует поиск автомобилей через клик по кнопке.

        :raises JavascriptException: Если кнопка поиска не найдена.
        """
        self.driver.execute_script("""
            const btn = document.querySelector(
                'div.search_car__block__settings__button[data-button_name="show_result"]'
            );
            if (btn) btn.click();
            else throw new Error('Search button not found');
        """)

    def _parse_car_list(self) -> List[Dict]:
        """
        Парсит список автомобилей на странице.

        :return: Список словарей с данными об автомобилях.
        :rtype: List[Dict]

        .. note::
            Логирует процесс парсинга в консоль браузера через console.group.
            Пропускает автомобили без ID.
        """
        try:
            logger.info("Начинаем парсинг списка автомобилей...")
            return self.driver.execute_script("""
                console.group('=== Парсинг автомобилей ===');
                const cars = [];
                const metaKeys = {
                    'Год:': 'year',
                    'Топливо:': 'fuel',
                    'Пробег:': 'mileage',
                    'Цвет:': 'color'
                };
                
                const carElements = document.querySelectorAll('div.car__wrapper');
                console.log(`Найдено элементов автомобилей: ${carElements.length}`);
                
                carElements.forEach((car, index) => {
                    console.group(`Автомобиль #${index}`);
                    const data = {};
                    
                    try {
                        // 2.1. Базовые данные
                        data.id = car.getAttribute('data-car_id') || null;
                        console.log(`ID: ${data.id}`);
                        
                        data.title = car.querySelector('h3.car__content__title')?.textContent.trim() || null;
                        console.log(`Название: ${data.title}`);
                        
                        data.image = car.querySelector('div.car__image img')?.src || null;
                        console.log(`Изображение: ${data.image ? 'есть' : 'нет'}`);
                        
                        // 2.2. Парсинг цены
                        const priceDigits = car.querySelector('span.car__price__value_digits');
                        const priceText = car.querySelector('span.car__price__value_text');
                        data.price = priceDigits?.textContent.trim() || priceText?.textContent.trim() || null;
                        console.log(`Цена: ${data.price}`);
                        
                        // 2.3. Парсинг мета-данных
                        console.group('Мета-данные:');
                        const metaItems = car.querySelectorAll('div.car__content__meta__item');
                        console.log(`Найдено мета-элементов: ${metaItems.length}`);
                        
                        metaItems.forEach(item => {
                            const label = item.querySelector('div.car__content__meta__item__label')?.textContent.trim();
                            const value = item.querySelector('div.car__content__meta__item__value')?.textContent.trim();
                            
                            if (label && metaKeys[label]) {
                                data[metaKeys[label]] = value;
                                console.log(`${label}: ${value}`);
                            }
                        });
                        console.groupEnd();
                        
                        // 2.4. Проверка полноты данных
                        if (!data.id) {
                            console.warn('Автомобиль пропущен - отсутствует ID');
                            console.groupEnd();
                            return;
                        }
                        
                        cars.push(data);
                        console.log('Автомобиль успешно добавлен');
                    } catch (error) {
                        console.error(`Ошибка при парсинге: ${error}`);
                        console.log('Текущие данные:', JSON.stringify(data, null, 2));
                    }
                    
                    console.groupEnd();
                });
                
                console.log(`Успешно распарсено автомобилей: ${cars.length}`);
                console.groupEnd();
                return cars;
            """)
        except Exception as e:
            logger.exception("Критическая ошибка при парсинге списка автомобилей")
            return []

    def _get_initial_filters(self) -> Dict:
        """
        Получает базовые фильтры (кроме моделей).

        :return: Словарь с доступными значениями фильтров:
            - brands (List[str]): Список марок
            - year_release_from (List[str]): Годы от
            - year_release_to (List[str]): Годы до
            - price_from (List[str]): Цены от
            - price_to (List[str]): Цены до
        :rtype: Dict
        """
        return self.driver.execute_script("""
            const result = {
                brands: [],
                transmission: [],
                fuel: [],
                color: [],
                mileage_from: [],
                mileage_to: [],
                year_release_from: [],
                year_release_to: [],
                price_from: [],
                price_to: [],
                
            };
            
            // Получаем бренды
            const brandFilter = document.querySelector('div.select__field[data-field_name="brand"]');
            if (brandFilter) {
                result.brands = Array.from(brandFilter.querySelectorAll('div.select__field__variant'))
                    .map(el => el.dataset.label)
                    .filter(label => label);
            }
            
            // Получаем остальные фильтры
            ['transmission',
            'fuel',
            'color',
            'mileage_from',
            'mileage_to',
            'year_release_from', 
            'year_release_to', 
            'price_from', 
            'price_to'].forEach(name => {
                const filter = document.querySelector(`div.select__field[data-field_name="${name}"]`);
                if (filter) {
                    result[name] = Array.from(filter.querySelectorAll('div.select__field__variant'))
                        .map(el => el.dataset.label)
                        .filter(label => label);
                }
            });
            
            return result;
        """)

    def _get_brand_models(self, brand: str) -> List[str]:
        """
        Получает список моделей для указанной марки.

        :param brand: Название марки автомобиля.
        :type brand: str
        :return: Список доступных моделей.
        :rtype: List[str]

        .. note::
            1. Находит фильтр марок
            2. Выбирает указанную марку
            3. Получает список моделей для выбранной марки
            4. Возвращает выбор марки в исходное состояние
        """
        return self.driver.execute_script("""
            const brandFilter = document.querySelector('div.select__field[data-field_name="brand"]');
            if (!brandFilter) return [];
            
            const brandOption = brandFilter.querySelector(`div.select__field__variant[data-label="${arguments[0]}"]`);
            if (!brandOption) {
                brandFilter.click();
                return [];
            }
            
            brandOption.click();
            
            const modelFilter = document.querySelector('div.select__field[data-field_name="model"]');
            if (!modelFilter) {
                brandOption.click();
                return [];
            }
            
            modelFilter.click();
            await new Promise(resolve => setTimeout(resolve, 300));
            
            const models = Array.from(modelFilter.querySelectorAll('div.select__field__variant'))
                .map(el => el.dataset.label)
                .filter(label => label);
            
            return models;
        """, brand)

    def _get_model_gens(self, brand: str, model: str) -> List[str]:
        """
        Получает список моделей для указанной марки.

        :param brand: Название марки автомобиля.
        :type brand: str
        :return: Список доступных моделей.
        :rtype: List[str]

        .. note::
            1. Находит фильтр марок
            2. Выбирает указанную марку
            3. Получает список моделей для выбранной марки
            4. Возвращает выбор марки в исходное состояние
        """
        return self.driver.execute_script("""

            const brandFilter = document.querySelector('div.select__field[data-field_name="brand"]');
            if (!brandFilter) return [];
            
            const brandOption = brandFilter.querySelector(`div.select__field__variant[data-label="${arguments[0]}"]`);
            if (!brandOption) {
                brandFilter.click();
                return [];
            }
            
            brandOption.click();
            
            const modelFilter = document.querySelector('div.select__field[data-field_name="model"]');
            if (!modelFilter) {
                brandOption.click();
                return [];
            }
            
            modelFilter.click();
            await new Promise(resolve => setTimeout(resolve, 300));
            
            const modelOption = modelFilter.querySelector(`div.select__field__variant[data-label="${arguments[1]}"]`);
            if (!modelOption) {
                modelFilter.click();
                return [];
            }
            
            modelOption.click();
            
            const genFilter = document.querySelector('div.select__field[data-field_name="gen"]');
            if (!genFilter) {
                modelOption.click();
                return [];
            }
            
            genFilter.click();
            await new Promise(resolve => setTimeout(resolve, 300));
            
            const gens = Array.from(genFilter.querySelectorAll('div.select__field__variant'))
                .map(el => el.dataset.label)
                .filter(label => label);
            
            return gens;
        """, brand, model)

    def _get_car_details(self, id: str) -> Dict:
        """
        Получает детальную информацию об автомобиле по его ID.

        :param car_id: ID автомобиля.
        :type car_id: str
        :return: Словарь с детальной информацией об автомобиле.
        :rtype: Dict
        """
        return self.driver.execute_script("""
            const carId = arguments[0];
            const result = {
                id: carId,
                photos: [],
                title: null,
                price: null,
                base_parameters: {},
                tech_parameters: {},
                car_check_parameters: {},
                car_check_inspections: {},
                car_body_options: {}
            };
        const parseInspections = () => {
            const inspectionsData = [];
            const inspectionSections = document.querySelectorAll('details.car_body__car_check__inspections');
            
            inspectionSections.forEach(section => {
                const sectionTitle = section.querySelector('summary')?.textContent.trim() || 'Проверка';
                const tables = section.querySelectorAll('table');
                
                tables.forEach(table => {
                    const rows = table.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            inspectionsData.push({
                                'section': sectionTitle,
                                'parameter': cells[0].textContent.trim(),
                                'value': cells[1].textContent.trim()
                            });
                        }
                    });
                });
            });
            
            return inspectionsData;
        };

        try {
            result.title = document.querySelector('div.car_body__right_part__car_title h2')?.textContent.trim() || null;
            result.price = document.querySelector('div.car_body__right_part__row__price__digits')?.textContent.trim() || null;
            const photoElements = document.querySelectorAll('div.car_body__left_part__car_gallery__image_wrapper img');
            result.photos = Array.from(photoElements).map(img => img.getAttribute('data-big_pict') || img.src).filter(Boolean);
            const baseParamElements = document.querySelectorAll('div.car_body__right_part__base_parameter');
            baseParamElements.forEach(el => {
                const label = el.querySelector('div.car_body__right_part__base_parameter__label')?.textContent.trim();
                const value = el.querySelector('div.car_body__right_part__base_parameter__value')?.textContent.trim();
                if (label && value) {
                    result.base_parameters[label] = value;
                }
            });
            const techParamElements = document.querySelectorAll('div.car_body__tech_parameter');
            techParamElements.forEach(el => {
                const name = el.getAttribute('data-parameter_name');
                const value = el.querySelectorAll('span')[1]?.textContent.trim();
                if (name && value) {
                    result.tech_parameters[name] = value;
                }
            });
            const checkParamElements = document.querySelectorAll('div.car_body__car_check_parameter');
            checkParamElements.forEach(el => {
                const name = el.getAttribute('data-parameter_name');
                const value = el.querySelectorAll('span')[1]?.textContent.trim();
                if (name && value) {
                    result.car_check_parameters[name] = value;
                }
            });
            result.inspections = parseInspections();
            const optionElements = document.querySelectorAll('details.car_body__options');
            optionElements.forEach(details => {
                const summary = details.querySelector('summary.light')?.textContent.trim();
                if (summary) {
                    const options = Array.from(details.querySelectorAll('div.car_body__option.exist span'))
                        .map(span => span.textContent.trim())
                        .filter(Boolean);
                    result.car_body_options[summary] = options;
                }
            });

        } catch (error) {
            console.error('Error getting car details:', error);
            throw error;
        }

        return result;
        """, id)

    def _get_pages_nums(self) -> Dict[str, List[str]]:
        """
        Получает номера доступных страниц и активную страницу.

        :return: Словарь с:
            - "pages": список доступных номеров страниц
            - "active": номер текущей активной страницы
        :rtype: Dict[str, List[int]]
        """
        return self.driver.execute_script("""
            const result = {
                pages_nums: [],
                cur_page_num: null
            };
            
            // Находим все элементы с номерами страниц
            const pageElements = document.querySelectorAll(
                'div.search_car__block__view_settings__pages__page_num:not(.dots)'
            );
            
            // Парсим номера страниц
            pageElements.forEach(element => {
                const pageNum = element.textContent.trim();
                result.pages_nums.push(pageNum);
                
                // Проверяем активна ли страница
                if (element.classList.contains('active')) {
                    result.cur_page_num = pageNum;
                }
            });
            
            return result;
        """)

    def _push_page_next(self) -> None:
            """
            Инициирует поиск автомобилей через клик по кнопке.

            :raises JavascriptException: Если кнопка поиска не найдена.
            """
            self.driver.execute_script("""
                const btn = document.querySelector(
                    'div.search_car__block__view_settings__pages_nav[data-direction="right"]'
                );
                if (btn) btn.click();
                else throw new Error('Next page button not found');
            """)

    def scrape_cars(self, page_num: str, filters: Dict[str, str]) -> List[Dict]:
        """
        Получает список автомобилей по заданным фильтрам.

        :param filters: Словарь параметров фильтрации:
            - brand (str): Марка автомобиля
            - model (str): Модель автомобиля
            - year_release_from (str): Год выпуска от
            - year_release_to (str): Год выпуска до
            - price_from (str): Цена от
            - price_to (str): Цена до

        :return: Список словарей с данными об автомобилях:
            - id (str): Идентификатор автомобиля
            - title (str): Название
            - image (str): URL изображения
            - price (str): Цена
            - year (str): Год выпуска
            - fuel (str): Тип топлива
            - mileage (str): Пробег
            - color (str): Цвет

        :raises JavascriptException: Ошибка выполнения JavaScript
        :raises TimeoutException: Таймаут при загрузке страницы
        :raises Exception: Любая другая ошибка при парсинге

        :Example:

        .. code-block:: python

            scraper = Scraper(url, driver)
            cars = scraper.scrape_cars({
                'brand': 'Toyota',
                'year_from': '2015'
            })
        """
        try:
            self._load_searchpage(self.url)
            self._apply_filters(filters)
            self._submit_search()
            self._wait_for_loading_searchpage()
            while self._get_pages_nums()["cur_page_num"] != page_num:
                self._push_page_next()
                self._wait_for_loading_searchpage()
            return self._parse_car_list()

        except JavascriptException as e:
            logger.error(f"JS error: {str(e)}")
            raise
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except Exception as e:
            logger.exception("Unexpected error during scraping")
            raise

    def scrape_filters(self) -> List[Dict]:
        """
        Получает список доступных фильтров (кроме моделей).

        :return: Список доступных фильтров.
        :rtype: List[Dict]
        :raises JavascriptException: Ошибка выполнения JavaScript
        :raises TimeoutException: Таймаут при загрузке
        :raises Exception: Любая другая ошибка
        """
        try:
            self._load_searchpage(self.url)
            return self._get_initial_filters()
            
        except JavascriptException as e:
            logger.error(f"JS error: {str(e)}")
            raise
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except Exception as e:
            logger.exception("Unexpected error during scraping")
            raise

    def scrape_brand_models(self, brand: str) -> List[Dict]:
        """
        Получает список моделей для указанного бренда.

        :param brand: Название бренда автомобиля.
        :type brand: str
        :return: Список доступных моделей.
        :rtype: List[Dict]
        :raises JavascriptException: Ошибка выполнения JavaScript
        :raises TimeoutException: Таймаут при загрузке
        :raises Exception: Любая другая ошибка
        """
        try:
            self._load_searchpage(self.url)
            return self._get_brand_models(brand)
            
        except JavascriptException as e:
            logger.error(f"JS error: {str(e)}")
            raise
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except Exception as e:
            logger.exception("Unexpected error during scraping")
            raise

    def scrape_model_gens(self, brand:str, model: str) -> List[Dict]:
        """
        Получает список моделей для указанного бренда.

        :param brand: Название бренда автомобиля.
        :type brand: str
        :return: Список доступных моделей.
        :rtype: List[Dict]
        :raises JavascriptException: Ошибка выполнения JavaScript
        :raises TimeoutException: Таймаут при загрузке
        :raises Exception: Любая другая ошибка
        """
        try:
            self._load_searchpage(self.url)
            return self._get_model_gens(brand, model)
            
        except JavascriptException as e:
            logger.error(f"JS error: {str(e)}")
            raise
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except Exception as e:
            logger.exception("Unexpected error during scraping")
            raise

    def scrape_car_details(self, id: str) -> Dict:
        """
        Получает детальную информацию об автомобиле по его ID.

        :param car_id: ID автомобиля.
        :type car_id: str
        :return: Словарь с детальной информацией об автомобиле.
        :rtype: Dict
        :raises JavascriptException: Ошибка выполнения JavaScript
        :raises TimeoutException: Таймаут при загрузке
        :raises Exception: Любая другая ошибка
        """
        try:
            self._load_carpage(self.url)
            return self._get_car_details(id)
        except JavascriptException as e:
            logger.error(f"JS error: {str(e)}")
            raise
        except TimeoutException:
            logger.error("Timeout while waiting for page elements")
            raise
        except Exception as e:
            logger.exception("Unexpected error during scraping")
            raise
