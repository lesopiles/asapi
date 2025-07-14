from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import JavascriptException, TimeoutException
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class Scraper:

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
        self.driver.get(url)
        self._wait_for_loading_searchpage()

    def _load_carpage(self, url: str) -> None:
        self.driver.get(url)
        self._wait_for_loading_carpage()

    def _wait_for_loading_searchpage(self) -> None:
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
        self.driver.execute_script("""
            const btn = document.querySelector(
                'div.search_car__block__settings__button[data-button_name="show_result"]'
            );
            if (btn) btn.click();
            else throw new Error('Search button not found');
        """)

    def _parse_car_list(self) -> List[Dict]:
        try:
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
            return []

    def _get_initial_filters(self) -> Dict:
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
        self.driver.execute_script("""
            const btn = document.querySelector(
                'div.search_car__block__view_settings__pages_nav[data-direction="right"]'
            );
            if (btn) btn.click();
            else throw new Error('Next page button not found');
        """)

    def _apply_sorting(self, sort_value: str) -> None:
        self.driver.execute_script("""
            const sortValue = arguments[0];
            const sortblock = document.querySelector('div.search_car__block__view_settings__sort__options');
            
            const dropdown = sortblock.querySelector('div.select__field__variants.js__select__field__variants');
            
            if (!dropdown) {
                return {success: false, error: 'Выпадающий список сортировки не найден'};
            }
            dropdown.click();
                                   
            // Ищем нужный вариант по data-value
            const option = dropdown.querySelector(`div.select__field__variant[data-value="${sortValue}"]`);
            
            if (!option) {
                const option = dropdown.querySelector(`div.select__field__variant_choosed[data-value="${sortValue}"]`);
                if (!option) {
                    return {success: false, error: 'Указанный вариант сортировки не найден'};
                }
            }
            
            // Кликаем по варианту
            option.click();
        """, sort_value)

    def scrape_cars(self, page_num: str, filters: Dict[str, str], order_by: str | None) -> List[Dict]:
        try:
            self._load_searchpage(self.url)
            self._apply_filters(filters)
            self._submit_search()
            self._wait_for_loading_searchpage()
            if order_by:
                self._apply_sorting(order_by)
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
