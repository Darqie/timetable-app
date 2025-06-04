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
# Тепер пари будуть стовпцями зверху
pairs = [
    ("I", "8:30 – 9:50"),
    ("II", "10:00 – 11:20"),
    ("III", "11:35 – 12:55"),
    ("IV", "13:15 – 14:35"),
    ("V", "14:45 – 16:05"),
]

# Дні тижня зліва
days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]


# Генерація даних
# Тепер ключі schedule_data будуть (день_індекс, пара_індекс)
schedule_data = {}
for i_day in range(len(days)):
    for i_pair in range(len(pairs)):
        key = (i_day, i_pair)
        schedule_data[key] = {
            "teacher": f"Викладач {i_day+1}-{i_pair+1}",
            "group": f"Група {chr(65 + i_day)}", # Може бути адаптовано, якщо групи не пов'язані з днями
            "subject": f"Предмет {i_pair+1}",
            "id": str(uuid.uuid4())
        }

# HTML + CSS для нового дизайну
html_code = f"""
<style>
/* Кольори з прикладу */
:root {{
    --header-bg-light: #F0F6F9; /* Для верхнього лівого кута та "Часу" */
    --header-bg-dark: #DDE8EE; /* Для заголовків пар */
    --day-header-bg: #E0ECFF; /* Для заголовків днів */
    --cell-bg: #FFFFFF; /* Колір фону клітинок */
    --border-color: #D3DBE0; /* Колір рамок */
    --draggable-bg: #d0e7ff; /* Збережемо для draggable */
    --text-color: #333;
}}

.timetable {{
    display: grid;
    /* Перший стовпець для днів, потім стовпці для кожної пари */
    grid-template-columns: 180px repeat({len(pairs)}, 1fr); 
    grid-auto-rows: minmax(80px, auto); /* Адаптивна висота рядків */
    gap: 1px; /* Менші проміжки для більш щільної таблиці */
    font-family: 'Roboto', sans-serif; /* Використаємо більш поширений шрифт */
    border: 1px solid var(--border-color); /* Зовнішня рамка таблиці */
    border-radius: 8px; /* Округлені кути для таблиці */
    overflow: hidden; /* Щоб рамка округлилась коректно */
    box-shadow: 2px 2px 10px rgba(0,0,0,0.08); /* Легка тінь */
    margin-top: 20px;
}}

.cell {{
    border: 1px solid var(--border-color);
    background: var(--cell-bg);
    position: relative;
    padding: 8px;
    overflow: hidden;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box; /* Важливо для розрахунку ширини */
}}
.cell-header {{
    background: var(--header-bg-dark); /* Темніший фон для заголовків пар */
    font-weight: bold;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 10px;
    color: var(--text-color);
}}
.top-left-corner {{
    background: var(--header-bg-light); /* Світліший фон для верхнього лівого кута */
}}
.day-name-header {{
    background: var(--day-header-bg); /* Колір для заголовків днів */
    font-size: 16px;
}}
.draggable {{
    background: var(--draggable-bg);
    border-radius: 6px;
    padding: 6px;
    cursor: grab;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.1);
    width: 90%; /* Займає більшість клітинки */
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

# Заголовки пар (верхній рядок)
for roman, time_range in pairs:
    html_code += f'''
        <div class="cell cell-header">
            <div><strong>{roman} ПАРА</strong></div> 
            <div class="time-block">({time_range})</div>
        </div>
    '''

# Основна частина таблиці: Дні зліва, пари з вмістом
for i_day, day_name in enumerate(days):
    # Заголовок дня (перша комірка в кожному рядку)
    html_code += f'<div class="cell cell-header day-name-header">{day_name}</div>'
    
    # Клітинки з вмістом для кожної пари цього дня
    for i_pair in range(len(pairs)):
        item = schedule_data[(i_day, i_pair)]
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
function allowDrop(ev) {
  ev.preventDefault();
}
function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.id);
}
function drop(ev) {
  ev.preventDefault();
  var draggedId = ev.dataTransfer.getData("text");
  var draggedElem = document.getElementById(draggedId);

  var dropTarget = ev.target;
  while (!dropTarget.classList.contains("cell")) {
    dropTarget = dropTarget.parentNode;
    if (!dropTarget) return;
  }

  // Запобігаємо перетягуванню на заголовки
  if (dropTarget.classList.contains("cell-header")) {
    return;
  }

  var existing = dropTarget.querySelector(".draggable");
  var parentOfDragged = draggedElem.parentNode;

  if (existing) {
    dropTarget.appendChild(draggedElem);
    parentOfDragged.appendChild(existing);
  } else {
    dropTarget.appendChild(draggedElem);
  }
}
</script>
"""

# Висота може бути трохи меншою, оскільки менше рядків заголовків
components.html(html_code, height=650, scrolling=True) 

# ⬇️ ОДНА КНОПКА ЗАВАНТАЖЕННЯ PDF ⬇️
# Функція для генерації PDF-файлу
# Тепер PDF буде відображати Дні зліва, а Пари зверху
def generate_pdf(schedule_data, start_date, end_date, pairs, days):
    pdf = FPDF(orientation='P') # Портретна орієнтація повинна підійти
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
    pair_col_width = (page_width - day_col_width) / len(pairs) # Ширина для кожної колонки пари

    # Перший рядок заголовків (пуста комірка + пари)
    pdf.set_font("DejaVuSans", "B", 10)
    pdf.cell(day_col_width, 10, txt="", border=1, align="C") # Верхній лівий кут
    for roman, time_range in pairs:
        pdf.multi_cell(pair_col_width, 5, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C", center=True)
        # Переміщуємо курсор, щоб продовжити в тому ж рядку
        pdf.set_xy(pdf.get_x() + pair_col_width, pdf.get_y() - 10) # Відкорегувати Y

    pdf.ln(10) # Перейти на новий рядок після заголовків пар

    # Основний контент таблиці
    pdf.set_font("DejaVuSans", "", 8) # Зменшений шрифт для вмісту
    for i_day, day_name in enumerate(days):
        start_x = pdf.get_x()
        start_y = pdf.get_y()
        
        # Заголовок дня
        pdf.set_font("DejaVuSans", "B", 10)
        pdf.cell(day_col_width, 20, txt=day_name, border=1, align="C", center=True) # Висота 20, щоб відповідати вмісту клітинок
        pdf.set_font("DejaVuSans", "", 8) # Повернути звичайний шрифт для даних
        
        # Перемістити курсор на початок стовпців з даними
        pdf.set_xy(start_x + day_col_width, start_y)

        for i_pair in range(len(pairs)):
            item = schedule_data[(i_day, i_pair)]
            text = f"{item['subject']}\n{item['teacher']}\n{item['group']}"
            
            current_x = pdf.get_x()
            current_y = pdf.get_y()

            pdf.multi_cell(pair_col_width, 20 / 3, txt=text, border=1, align="C") # 20 / 3 для 3-х рядків тексту
            # Повертаємося на поточну Y-позицію, щоб продовжити наступну клітинку в тому ж рядку
            pdf.set_xy(current_x + pair_col_width, current_y)
            
        pdf.ln(20) # Переходимо на новий рядок після заповнення всіх пар для поточного дня
        
    return pdf.output(dest='S').encode('latin1')

# Кнопка для завантаження PDF
pdf_bytes = generate_pdf(schedule_data, start_date, end_date, pairs, days)

if pdf_bytes: 
    st.download_button(
        label="⬇️ Завантажити PDF",
        data=pdf_bytes,
        file_name="розклад.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Не вдалося згенерувати PDF-файл через помилку шрифту.")
