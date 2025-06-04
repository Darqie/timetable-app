import streamlit as st
import streamlit.components.v1 as components
import uuid
from datetime import date, timedelta
from fpdf import FPDF # Переконайтеся, що це fpdf або fpdf2

st.set_page_config(page_title="Розклад пар", layout="wide")

st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Розклад пар</h2>", unsafe_allow_html=True)

# 📅 Вибір тижня
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Початок тижня", date(2025, 6, 2))
with col2:
    end_date = start_date + timedelta(days=4)
    st.markdown(f"### 📆 {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}")

# 🕒 Пари + час
pairs = [
    ("I", "8:30 – 9:50"),
    ("II", "10:00 – 11:20"),
    ("III", "11:35 – 12:55"),
    ("IV", "13:15 – 14:35"),
    ("V", "14:45 – 16:05"),
]

days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
num_groups_per_day = 6 # Кількість груп під кожним днем

# Створюємо список груп
group_names = [f"Група {i+1}" for i in range(num_groups_per_day)]

# Генерація даних
# Ключі schedule_data будуть (день_індекс, група_індекс, пара_індекс)
schedule_data = {}
for i_day in range(len(days)):
    for i_group in range(num_groups_per_day):
        for i_pair in range(len(pairs)):
            key = (i_day, i_group, i_pair)
            schedule_data[key] = {
                "teacher": f"Вч.{chr(65 + i_day)}.{i_group+1}.{i_pair+1}",
                "group": group_names[i_group],
                "subject": f"Предм.{i_pair+1}-{i_group+1}",
                "id": str(uuid.uuid4())
            }

# HTML + CSS для нового дизайну: дні зліва, 6 груп під кожним днем
html_code = f"""
<style>
/* Блакитно-жовті кольори, тіні, напівпрозорість */
:root {{
    --main-bg-color: #F8F8F8; /* Світлий задній фон */
    --header-bg-top-left: rgba(220, 230, 240, 0.8); /* Світло-блакитний, напівпрозорий */
    --header-bg-pair: rgba(180, 210, 230, 0.8); /* Трохи темніший блакитний для пар */
    --header-bg-group: rgba(200, 220, 240, 0.8); /* Блакитний для підзаголовків груп */
    --header-bg-day: rgba(240, 200, 100, 0.9); /* Жовтуватий для днів, майже непрозорий */
    --cell-bg: rgba(255, 255, 255, 0.7); /* Білий, напівпрозорий фон для клітинок */
    --border-color: #C0D0E0; /* Блакитнуватий для рамок */
    --draggable-bg: rgba(255, 240, 180, 0.8); /* Світло-жовтий для draggable елементів */
    --text-color: #333333;
    --shadow-light: 0 2px 5px rgba(0,0,0,0.1);
    --shadow-medium: 0 4px 8px rgba(0,0,0,0.15);
}}

body {{
    background-color: var(--main-bg-color);
}}

.timetable {{
    display: grid;
    /* Перший стовпець для днів, другий для груп, потім стовпці для кожної пари */
    grid-template-columns: 120px 80px repeat({len(pairs)}, 1fr);
    /* Висота рядка зменшена з 80px до 55px */
    grid-auto-rows: minmax(55px, auto);
    gap: 1px; /* Менші проміжки для більш щільної таблиці */
    font-family: 'Roboto', sans-serif;
    border: 1px solid var(--border-color); /* Зовнішня рамка таблиці */
    border-radius: 12px; /* Округлені кути для таблиці */
    overflow: hidden; /* Щоб рамка округлилась коректно */
    box-shadow: var(--shadow-medium); /* Легка тінь */
    margin-top: 20px;
    background-color: var(--main-bg-color); /* Фон для таблиці */
    max-width: 100%; /* Обмежуємо ширину */
    overflow-x: auto; /* Горизонтальна прокрутка, якщо таблиця заширока */
}}

.cell {{
    border: 1px solid var(--border-color);
    background: var(--cell-bg);
    position: relative;
    padding: 4px; /* Ще зменшений padding */
    overflow: hidden;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box;
    font-size: 10px; /* Ще зменшений шрифт */
}}
.cell-header {{
    font-weight: bold;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6px; /* Зменшений padding для заголовків */
    color: var(--text-color);
    box-shadow: var(--shadow-light); /* Тінь для заголовків */
}}
.top-left-corner {{
    background: var(--header-bg-top-left);
    border-radius: 12px 0 0 0; /* Округлення для верхнього лівого кута */
}}
.pair-header {{
    background: var(--header-bg-pair);
    font-size: 16px;
    border-radius: 0;
}}
.day-header-main {{ /* Новий клас для заголовків днів, які охоплюють рядки */
    background: var(--header-bg-day);
    font-size: 16px;
    grid-row: span {num_groups_per_day}; /* Заголовок дня охоплює 6 рядків груп */
    border-radius: 0;
}}
.group-sub-header {{ /* Заголовки груп зліва */
    background: var(--header-bg-group);
    font-size: 12px;
    padding: 5px;
    border-radius: 0;
}}
.draggable {{
    background: var(--draggable-bg);
    border-radius: 6px; /* Трохи менше округлення */
    padding: 4px; /* Зменшений padding */
    cursor: grab;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.15);
    width: 95%;
    font-size: 9px; /* Ще менший шрифт для draggable */
    line-height: 1.2; /* Зменшений міжрядковий інтервал */
    transition: transform 0.1s ease-in-out;
}}
.draggable:active {{
    transform: scale(1.03);
}}
.time-block {{
    font-size: 13px;
    color: var(--text-color);
    line-height: 1.2;
}}
</style>

<div class="timetable">
    <div class="cell cell-header top-left-corner"></div>
    <div class="cell cell-header top-left-corner">Група</div>
"""

# Верхній рядок: Заголовки пар
for roman, time_range in pairs:
    html_code += f'''
        <div class="cell cell-header pair-header">
            <div><strong>{roman} ПАРА</strong></div>
            <div class="time-block">({time_range})</div>
        </div>
    '''

# Основна частина таблиці: Дні зліва (об'єднані), потім групи, потім дані
for i_day, day_name in enumerate(days):
    # Заголовок дня, що охоплює 6 рядків
    html_code += f'<div class="cell cell-header day-header-main">{day_name}</div>'

    # Для кожної групи цього дня
    for i_group in range(num_groups_per_day):
        # Заголовок групи (після заголовка дня)
        html_code += f'<div class="cell group-sub-header">{group_names[i_group]}</div>'

        # Клітинки з вмістом для кожної пари
        for i_pair in range(len(pairs)):
            item = schedule_data[(i_day, i_group, i_pair)]
            html_code += f'''
            <div class="cell" ondrop="drop(event)" ondragover="allowDrop(event)">
                <div id="{item['id']}" class="draggable" draggable="true" ondragstart="drag(event)">
                    <strong>{item["subject"]}</strong><br>
                    {item["teacher"]}
                </div>
            </div>
            '''

html_code += """
</div>

<script>
function allowDrop(ev) {{
  ev.preventDefault();
}}
function drag(ev) {{
  ev.dataTransfer.setData("text", ev.target.id);
}}
function drop(ev) {{
  ev.preventDefault();
  var draggedId = ev.dataTransfer.getData("text");
  var draggedElem = document.getElementById(draggedId);

  var dropTarget = ev.target;
  // Перевірка на заголовки. Подвоєні дужки {{ }} для JavaScript
  while (!dropTarget.classList.contains("cell") || dropTarget.classList.contains("cell-header")) {{
    dropTarget = dropTarget.parentNode;
    if (!dropTarget) return;
  }}

  var existing = dropTarget.querySelector(".draggable");
  var parentOfDragged = draggedElem.parentNode;

  if (existing) {{
    dropTarget.appendChild(draggedElem);
    parentOfDragged.appendChild(existing);
  }} else {{
    dropTarget.appendChild(draggedElem);
  }}
}}
</script>
"""

components.html(html_code, height=800, scrolling=True)

# ⬇️ ОДНА КНОПКА ЗАВАНТАЖЕННЯ PDF ⬇️
# Функція для генерації PDF-файлу
def generate_pdf(schedule_data, start_date, end_date, pairs, days, group_names, num_groups_per_day):
    pdf = FPDF(orientation='L') # Орієнтація "L" (Landscape) для широкого розкладу
    pdf.add_page()

    regular_font_path = "fonts/DejaVuSans.ttf"
    bold_font_path = "fonts/DejaVuSans-Bold.ttf"

    try:
        pdf.add_font("DejaVuSans", "", regular_font_path, uni=True)
        pdf.add_font("DejaVuSans", "B", bold_font_path, uni=True)
        pdf.set_font("DejaVuSans", "", size=10)
    except Exception as e:
        st.error(f"Помилка завантаження шрифту: {e}. Переконайтеся, що файли шрифтів (регулярний та жирний) існують у папці 'fonts' та правильно вказані шляхи.")
        return None

    pdf.set_font("DejaVuSans", "B", 14)
    pdf.cell(0, 10, txt=f"Розклад: {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}", ln=True, align="C")
    pdf.ln(5)

    # Загальна ширина сторінки для контенту
    page_width = pdf.w - 2 * pdf.l_margin
    
    # Визначення ширини колонок
    day_col_width = 30 # Ширина для колонки днів
    group_col_width = 30 # Ширина для колонки груп
    pair_col_width = (page_width - day_col_width - group_col_width) / len(pairs) # Ширина для кожної колонки пари

    # Зберегти початкову X-позицію для рядка заголовків
    initial_x = pdf.get_x()
    initial_y = pdf.get_y()

    # Заголовковий рядок (пуста комірка + "Група" + Заголовки пар)
    pdf.set_font("DejaVuSans", "B", 10)
    pdf.cell(day_col_width, 10, txt="", border=1, align="C") # Верхній лівий кут (порожній)
    pdf.cell(group_col_width, 10, txt="Група", border=1, align="C") # Заголовок "Група"
    
    # Позиціонування для заголовків пар
    # Ми хочемо, щоб ці клітинки були на тому ж рівні Y, що й "Група", і починалися після неї.
    current_x = pdf.get_x()
    current_y = pdf.get_y() # Поточна Y після клітинки "Група"
    
    # Висота для multi_cell заголовків пар
    pair_header_h = 10 

    for roman, time_range in pairs:
        pdf.set_xy(current_x, initial_y) # Повернутися на початковий Y для заголовків
        pdf.multi_cell(pair_col_width, pair_header_h / 2, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C")
        current_x += pair_col_width # Перемістити X для наступної пари

    # Після малювання всіх заголовків пар, переходимо на новий рядок
    pdf.set_xy(initial_x, initial_y + pair_header_h) # Перемістити на Y після заголовків

    # Основний контент таблиці
    pdf.set_font("DejaVuSans", "", 7) # Ще менший шрифт для вмісту клітинок
    row_height_pdf = 15 # Фіксована висота рядка для PDF

    for i_day, day_name in enumerate(days):
        # Зберігаємо початкову позицію X та Y для поточного дня
        day_start_x = pdf.get_x()
        day_start_y = pdf.get_y()
        
        # Заголовок дня (охоплює 6 рядків)
        pdf.set_font("DejaVuSans", "B", 9)
        pdf.cell(day_col_width, row_height_pdf * num_groups_per_day, txt=day_name, border=1, align="C")
        
        # Переміщуємо курсор для першої групи цього дня
        # X-позиція: початок колонки груп (day_start_x + day_col_width)
        # Y-позиція: початок рядка дня (day_start_y)
        pdf.set_xy(day_start_x + day_col_width, day_start_y)

        for i_group in range(num_groups_per_day):
            group_current_x = pdf.get_x() # Зберігаємо X на початку колонки групи
            group_current_y = pdf.get_y() # Зберігаємо Y на початку рядка групи
            
            # Заголовок групи
            pdf.set_font("DejaVuSans", "", 8)
            pdf.cell(group_col_width, row_height_pdf, txt=group_names[i_group], border=1, align="C")
            
            # Переміщуємо курсор на початок стовпців з даними
            pdf.set_xy(group_current_x + group_col_width, group_current_y)

            for i_pair in range(len(pairs)):
                item = schedule_data[(i_day, i_group, i_pair)]
                text = f"{item['subject']}\n{item['teacher']}" # Лише предмет та викладач

                current_x = pdf.get_x()
                current_y = pdf.get_y()

                # multi_cell для двох рядків тексту (Subject + Teacher)
                pdf.multi_cell(pair_col_width, row_height_pdf / 2, txt=text, border=1, align="C")
                # Повертаємося на поточну Y-позицію, щоб продовжити наступну клітинку в тому ж рядку
                pdf.set_xy(current_x + pair_col_width, current_y)
            
            # Після заповнення всіх пар для поточної групи, переходимо на новий рядок для наступної групи
            pdf.set_xy(day_start_x + day_col_width, group_current_y + row_height_pdf) # Переміщуємо на початок колонки груп, але на новий рядок.

        # Після завершення всіх груп для поточного дня, переходимо на новий логічний рядок для наступного дня
        pdf.ln(row_height_pdf * num_groups_per_day) # Перехід на новий рядок на висоту всього блоку дня

    return pdf.output(dest='S').encode('latin1')

# Кнопка для завантаження PDF
pdf_bytes = generate_pdf(schedule_data, start_date, end_date, pairs, days, group_names, num_groups_per_day)

if pdf_bytes:
    st.download_button(
        label="⬇️ Завантажити PDF",
        data=pdf_bytes,
        file_name="розклад.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Не вдалося згенерувати PDF-файл через помилку шрифту.")
