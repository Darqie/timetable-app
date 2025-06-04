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

# Дні тижня зліва
days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
num_groups_per_pair = 6 # Кількість груп під кожною парою

# Створюємо список груп
group_names = [f"Група {i+1}" for i in range(num_groups_per_pair)]

# Генерація даних
# Ключі schedule_data будуть (день_індекс, пара_індекс, група_індекс)
schedule_data = {}
for i_day in range(len(days)):
    for i_pair in range(len(pairs)):
        for i_group in range(num_groups_per_pair):
            key = (i_day, i_pair, i_group)
            schedule_data[key] = {
                "teacher": f"Викладач {i_day+1}-{i_pair+1}-{i_group+1}",
                "group": group_names[i_group],
                "subject": f"Предмет {i_pair+1}-{i_day+1}-{i_group+1}",
                "id": str(uuid.uuid4())
            }

# HTML + CSS для нового дизайну та 6 груп під парами
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
    /* Перший стовпець для днів, потім для кожної пари (яка охоплює 6 груп) */
    grid-template-columns: 180px repeat({len(pairs) * num_groups_per_pair}, 1fr);
    grid-auto-rows: minmax(80px, auto); /* Адаптивна висота рядків */
    gap: 1px; /* Менші проміжки для більш щільної таблиці */
    font-family: 'Roboto', sans-serif;
    border: 1px solid var(--border-color); /* Зовнішня рамка таблиці */
    border-radius: 12px; /* Округлені кути для таблиці */
    overflow: hidden; /* Щоб рамка округлилась коректно */
    box-shadow: var(--shadow-medium); /* Легка тінь */
    margin-top: 20px;
    background-color: var(--main-bg-color); /* Фон для таблиці */
    max-width: 100%; /* Обмежуємо ширину, щоб не виходило за межі */
    overflow-x: auto; /* Горизонтальна прокрутка */
}}

.cell {{
    border: 1px solid var(--border-color);
    background: var(--cell-bg);
    position: relative;
    padding: 6px; /* Зменшений padding для великої кількості клітинок */
    overflow: hidden;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box;
    font-size: 11px; /* Зменшений шрифт для вмісту */
    min-width: 80px; /* Мінімальна ширина для комірки групи */
}}
.cell-header {{
    font-weight: bold;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 8px;
    color: var(--text-color);
    box-shadow: var(--shadow-light); /* Тінь для заголовків */
}}
.top-left-corner {{
    background: var(--header-bg-top-left);
    border-radius: 12px 0 0 0; /* Округлення для верхнього лівого кута */
}}
.pair-header {{
    background: var(--header-bg-pair);
    grid-column: span {num_groups_per_pair}; /* Заголовок пари охоплює 6 колонок груп */
    font-size: 16px;
    border-radius: 0; /* Видаляємо округлення, якщо не кутовий елемент */
}}
.group-sub-header {{
    background: var(--header-bg-group);
    font-size: 12px;
    padding: 5px;
    border-radius: 0;
}}
.day-name-header {{
    background: var(--header-bg-day);
    font-size: 16px;
    border-radius: 0;
}}
.draggable {{
    background: var(--draggable-bg);
    border-radius: 8px; /* Більш округлі draggable елементи */
    padding: 6px;
    cursor: grab;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.15); /* Легка тінь для draggable */
    width: 95%; /* Займає більшість клітинки */
    font-size: 10px; /* Ще менший шрифт для draggable */
    transition: transform 0.1s ease-in-out; /* Анімація при перетягуванні */
}}
.draggable:active {{
    transform: scale(1.03); /* Збільшення при активації */
}}
.time-block {{
    font-size: 13px;
    color: var(--text-color);
    line-height: 1.2;
}}
</style>

<div class="timetable">
    <div class="cell cell-header top-left-corner"></div>
"""

# Перший рядок: Заголовки пар (об'єднані комірки)
for roman, time_range in pairs:
    html_code += f'''
        <div class="cell cell-header pair-header">
            <div><strong>{roman} ПАРА</strong></div>
            <div class="time-block">({time_range})</div>
        </div>
    '''

# Другий рядок: Заголовки груп під відповідними парами
html_code += f'<div class="cell cell-header"></div>' # Пуста комірка для відповідності з першим стовпцем (днем)
for i_pair in range(len(pairs)):
    for group_name in group_names:
        html_code += f'<div class="cell group-sub-header">{group_name}</div>'

# Основна частина таблиці: Дні зліва, а потім 6 груп під кожною парою
for i_day, day_name in enumerate(days):
    # Заголовок дня (перша комірка в кожному рядку)
    html_code += f'<div class="cell cell-header day-name-header">{day_name}</div>'

    # Клітинки з вмістом для кожної пари та групи цього дня
    for i_pair in range(len(pairs)):
        for i_group in range(num_groups_per_pair):
            item = schedule_data[(i_day, i_pair, i_group)]
            html_code += f'''
            <div class="cell" ondrop="drop(event)" ondragover="allowDrop(event)">
                <div id="{item['id']}" class="draggable" draggable="true" ondragstart="drag(event)">
                    <strong>{item["subject"]}</strong><br>
                    {item["teacher"]}<br>
                    {item["group"]}
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

# Висота може бути досить значною через кількість клітинок
components.html(html_code, height=800, scrolling=True)

# ⬇️ ОДНА КНОПКА ЗАВАНТАЖЕННЯ PDF ⬇️
# Функція для генерації PDF-файлу
# PDF тепер буде відображати Дні зліва, а Пари зверху, з 6 групами під кожною парою
def generate_pdf(schedule_data, start_date, end_date, pairs, days, group_names, num_groups_per_pair):
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
    day_col_width = 35 # Ширина для колонки днів
    # Ширина однієї під-колонки для групи
    group_sub_col_width = (page_width - day_col_width) / (len(pairs) * num_groups_per_pair)

    # Перший рядок заголовків (пуста комірка + пари, об'єднані)
    pdf.set_font("DejaVuSans", "B", 10)
    pdf.cell(day_col_width, 10, txt="", border=1, align="C") # Верхній лівий кут

    # Зберігаємо позицію X для заголовків пар
    start_x_headers = pdf.get_x()
    start_y_headers = pdf.get_y()

    for roman, time_range in pairs:
        # FPDF не має прямого colspan, тому ми просто малюємо комірку потрібної ширини
        pdf.cell(group_sub_col_width * num_groups_per_pair, 10, txt=f"{roman} ПАРА", border=1, align="C")
    pdf.ln()

    # Другий рядок заголовків (пуста комірка + назви груп)
    pdf.set_font("DejaVuSans", "", 8) # Зменшений шрифт для груп
    # Повертаємось на початок рядка
    pdf.set_xy(pdf.l_margin, pdf.get_y())

    pdf.cell(day_col_width, 10, txt="", border=1, align="C") # Пуста комірка
    for i_pair in range(len(pairs)):
        for group_name in group_names:
            pdf.cell(group_sub_col_width, 10, txt=group_name, border=1, align="C")
    pdf.ln()

    # Основний контент таблиці
    pdf.set_font("DejaVuSans", "", 7) # Ще менший шрифт для вмісту клітинок
    for i_day, day_name in enumerate(days):
        start_x_row = pdf.get_x()
        start_y_row = pdf.get_y()

        # Заголовок дня
        pdf.set_font("DejaVuSans", "B", 9) # Трохи більший шрифт для дня
        # Змінюємо висоту клітинки дня, щоб відповідати висоті всього рядка даних
        pdf.cell(day_col_width, 40, txt=day_name, border=1, align="C")
        pdf.set_font("DejaVuSans", "", 7) # Повернути звичайний шрифт для даних

        # Перемістити курсор на початок стовпців з даними
        pdf.set_xy(start_x_row + day_col_width, start_y_row)

        for i_pair in range(len(pairs)):
            for i_group in range(num_groups_per_pair):
                item = schedule_data[(i_day, i_pair, i_group)]
                text = f"{item['subject']}\n{item['teacher']}\n{item['group']}"

                current_x = pdf.get_x()
                current_y = pdf.get_y()

                pdf.multi_cell(group_sub_col_width, 40 / 3, txt=text, border=1, align="C")
                # Повертаємося на поточну Y-позицію, щоб продовжити наступну клітинку в тому ж рядку
                pdf.set_xy(current_x + group_sub_col_width, current_y)

        pdf.ln(40) # Переходимо на новий рядок після заповнення всіх груп для поточної пари

    return pdf.output(dest='S').encode('latin1')

# Кнопка для завантаження PDF
pdf_bytes = generate_pdf(schedule_data, start_date, end_date, pairs, days, group_names, num_groups_per_pair)

if pdf_bytes:
    st.download_button(
        label="⬇️ Завантажити PDF",
        data=pdf_bytes,
        file_name="розклад.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Не вдалося згенерувати PDF-файл через помилку шрифту.")
