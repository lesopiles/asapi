<body>
  <h1 align="center">ASAPI Documentation</h1>
  
  <h2>API Endpoints</h2>
  
  <h3>1. GET /api/v1/cars</h3>
  <p><strong>Description</strong>: Получение списка автомобилей с возможностью фильтрации и пагинации.</p>
  
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
  </ul>
  
  <h4>Example Request:</h4>
  <pre><code>GET /api/v1/cars?brand=Toyota&amp;model=Camry&amp;page_num=2</code></pre>
  
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
              "image": "http://example.com/image1.jpg"
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
  
  <h3>2. GET /api/v1/filters</h3>
  <p><strong>Description</strong>: Получение всех доступных фильтров для поиска автомобилей.</p>
  
  <h4>Example Request:</h4>
  <pre><code>GET /api/v1/filters</code></pre>
  
  <h4>Example Response:</h4>
  <pre><code class="language-json">{
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
  }</code></pre>
  
  <h4>Status Codes:</h4>
  <ul>
      <li>200: Успешный запрос</li>
      <li>404: Фильтры не найдены</li>
      <li>500: Внутренняя ошибка сервера</li>
  </ul>
  
  <h3>3. GET /api/v1/filters/models</h3>
  <p><strong>Description</strong>: Получение списка моделей для указанной марки.</p>
  
  <h4>Parameters:</h4>
  <ul>
      <li><code>brand</code> (string, required): Марка автомобиля</li>
  </ul>
  
  <h4>Example Request:</h4>
  <pre><code>GET /api/v1/filters/models?brand=Toyota</code></pre>
  
  <h4>Example Response:</h4>
  <pre><code class="language-json">{
      "success": true,
      "models": ["Camry", "Corolla", "RAV4"]
  }</code></pre>
  
  <h3>4. GET /api/v1/filters/gens</h3>
  <p><strong>Description</strong>: Получение списка поколений для указанной модели и марки.</p>
  
  <h4>Parameters:</h4>
  <ul>
      <li><code>brand</code> (string, required): Марка автомобиля</li>
      <li><code>model</code> (string, required): Модель автомобиля</li>
  </ul>
  
  <h4>Example Request:</h4>
  <pre><code>GET /api/v1/filters/gens?brand=Toyota&amp;model=Camry</code></pre>
  
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
</body>
