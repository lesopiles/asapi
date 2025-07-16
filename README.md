<body>
<h1 align="center">ASAPI Documentation</h1>

<h2>API Endpoints</h2>

<h3>1. GET /api/v1/cars</h3>
<p><strong>Description</strong>: Получение списка автомобилей с возможностью фильтрации, сортировки и пагинации.</p>

<h4>Parameters:</h4>
<ul>
    <li><code>brand</code> (string, optional): Марка автомобиля</li>
    <li><code>model</code> (string, optional): Модель автомобиля</li>
    <li><code>gen</code> (string, optional): Поколение модели</li>
    <li><code>page_num</code> (string, default="1"): Номер страницы</li>
    <li><code>year_from</code> (string, optional): Год выпуска от</li>
    <li><code>year_to</code> (string, optional): Год выпуска до</li>
    <li><code>price_from</code> (string, optional): Цена от</li>
    <li><code>price_to</code> (string, optional): Цена до</li>
    <li><code>order_by</code> (string, optional): Сортировка результатов. Доступные значения:
        <ul>
            <li><code>sort__date_added_desc</code> - Дата объявления (новые сначала)</li>
            <li><code>sort__mileage_asc</code> - Пробег (по возрастанию)</li>
            <li><code>sort__mileage_desc</code> - Пробег (по убыванию)</li>
            <li><code>sort__price_asc</code> - Цена (по возрастанию)</li>
            <li><code>sort__price_desc</code> - Цена (по убыванию)</li>
            <li><code>sort__release_asc</code> - Год выпуска (по возрастанию)</li>
            <li><code>sort__release_desc</code> - Год выпуска (по убыванию)</li>
        </ul>
    </li>
</ul>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars?brand=Toyota&amp;model=Camry&amp;page_num=2&amp;order_by=sort__price_desc</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
    "success": true,
    "count": 15,
    "page_info": {
        "pages_nums": ["1", "2", "3"],
        "cur_page_num": "2"
    },
    "cars": [
        {
            "id": "12345",
            "title": "Toyota Camry 2020",
            "price": "1 200 000 ₽",
            "year": "2020",
            "image": "http://example.com/image1.jpg",
            "fuel": "Бензин",
            "mileage": "50 000 км",
            "color": "Серебристый"
        }
    ]
}</code></pre>

<h4>Status Codes:</h4>
<ul>
    <li>200: Успешный запрос</li>
    <li>404: Данные не найдены</li>
    <li>500: Внутренняя ошибка сервера</li>
    <li>504: Сайт не отвечает</li>
</ul>

<h3>2. GET /api/v1/cars/filters</h3>
<p><strong>Description</strong>: Получение всех доступных фильтров для поиска автомобилей.</p>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars/filters</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
    "success": true,
    "filters": {
        "brands": ["Toyota", "Honda", "BMW", "Audi"],
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
}</code></pre>

<h4>Status Codes:</h4>
<ul>
    <li>200: Успешный запрос</li>
    <li>404: Фильтры не найдены</li>
    <li>500: Внутренняя ошибка сервера</li>
</ul>

<h3>3. GET /api/v1/cars/filters/models</h3>
<p><strong>Description</strong>: Получение списка моделей для указанной марки.</p>

<h4>Parameters:</h4>
<ul>
    <li><code>brand</code> (string, required): Марка автомобиля</li>
</ul>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars/filters/models?brand=Toyota</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
    "success": true,
    "models": ["Camry", "Corolla", "RAV4"]
}</code></pre>

<h3>4. GET /api/v1/cars/filters/gens</h3>
<p><strong>Description</strong>: Получение списка поколений для указанной модели и марки.</p>

<h4>Parameters:</h4>
<ul>
    <li><code>brand</code> (string, required): Марка автомобиля</li>
    <li><code>model</code> (string, required): Модель автомобиля</li>
</ul>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars/filters/gens?brand=Toyota&amp;model=Camry</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
    "success": true,
    "gens": ["VII (2017-2020)", "VIII (2021-2023)"]
}</code></pre>

<h3>5. GET /api/v1/cars/&lt;id&gt;</h3>
<p><strong>Description</strong>: Получение детальной информации об автомобиле по ID.</p>

<h4>Parameters:</h4>
<ul>
    <li><code>id</code> (string, required): Уникальный идентификатор автомобиля</li>
</ul>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars/10420276</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
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
            }
        ],
        "car_body_options": {
            "Комфорт": ["Климат-контроль", "Подогрев сидений"],
            "Безопасность": ["Парктроник", "Камера заднего вида"]
        }
    }
}</code></pre>

<h4>Status Codes:</h4>
<ul>
    <li>200: Успешный запрос</li>
    <li>404: Автомобиль не найден</li>
    <li>500: Внутренняя ошибка сервера</li>
</ul>

<h3>6. GET /api/v1/cars/&lt;id&gt;/price</h3>
<p><strong>Description</strong>: Получение детальной информации о расчете цены автомобиля по ID.</p>

<h4>Parameters:</h4>
<ul>
    <li><code>id</code> (string, required): Уникальный идентификатор автомобиля</li>
</ul>

<h4>Example Request:</h4>
<pre><code>GET /api/v1/cars/10420276/price</code></pre>

<h4>Example Response:</h4>
<pre><code class="language-json">{
    "success": true,
    "price_calculation": {
        "currency_date": "16-07-2025 23:21",
        "currency_rates": {
            "EUR": "91.1531"
        },
        "total_price": "6 922 665 ₽",
        "breakdown": {
            "Услуги агента": "100 000 ₽",
            "Стоимость авто + расходы в Корее": "1 856 364 ₽",
            "Таможенные платежи": "1 251 501 ₽ (13 730 € )",
            "Утильсбор": "3 604 800 ₽",
            "Таможенный брокер": "110 000 ₽",
            "Автовоз": "0 ₽"
        }
    }
}</code></pre>

<h4>Status Codes:</h4>
<ul>
    <li>200: Успешный запрос</li>
    <li>404: Автомобиль не найден</li>
    <li>500: Внутренняя ошибка сервера</li>
    <li>504: Сайт не отвечает</li>
</ul>
</body>
