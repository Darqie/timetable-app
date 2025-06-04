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

# Додаємо список груп
groups = ["Група 1", "Група 2", "Група 3", "Група 4", "Група 5"] # Змінено на 5 груп для відповідності 5 дням

# Генерація даних (можливо, потрібно буде адаптувати, якщо груп буде більше, ніж колонок для днів)
schedule_data = {}
for i in range(5): # Індекс для пар (рядків)
    for j in range(5): # Індекс для днів/груп (колонок)
        schedule_data[(i, j)] = {
            "teacher": f"Викладач {i+1}",
            "group": f"Група {j+1}", # Змінено для відповідності 'Група 1', 'Група 2'
            "subject": f"Предмет {j+1}",
            "id": str(uuid.uuid4())
        }

# HTML + CSS (оновлено для зміни формату нумерації)
html_code = f"""
<style>
.timetable {{
    display: grid;
    /* Оновлено: 180px для часу, потім 5 стовпців для днів/груп */
    grid-template-columns: 180px repeat({len(days)}, 1fr);
    grid-auto-rows: minmax(50px, auto); /* Адаптивна висота рядків */
    gap: 2px;
    font-family: 'Segoe UI', sans-serif;
}}
.cell {{
    border: 1px solid #ccc;
    background: #f9f9f9;
    position: relative;
    padding: 8px;
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
}}
.cell-header {{
    background: #e0ecff;
    font-weight: bold;
    text-align: center;
    border-radius: 8px;
    display: flex;
    flex-direction: column; /* Змінено на column для вертикального розташування */
    align-items: center;
    justify-content: center;
    padding: 5px; /* Зменшений відступ для заголовків */
}}
.draggable {{
    background: #d0e7ff;
    border-radius: 6px;
    padding: 6px;
    cursor: grab;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
}}
.time-block {{
    font-size: 14px;
    color: #444;
    text-align: center;
    line-height: 1.2; 
}}
.group-header {{
    background: #e0ecff; /* Той самий колір, що й для інших заголовків */
    font-weight: bold;
    text-align: center;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 5px;
}}
</style>

<div class="timetable">
    <div class="cell cell-header"></div> """

# Дні тижня (перший рядок заголовків)
for day in days:
    html_code += f'<div class="cell cell-header">{day}</div>'

# Рядок з групами (другий рядок заголовків)
html_code += f'<div class="cell group-header"></div>' # Пуста комірка або "Час" для відповідності сітці
for group in groups:
    html_code += f'<div class="cell group-header">{group}</div>'

# Пари зліва + клітинки (оновлено: "Пара" і час на різних рядках)
for i, (roman, time_range) in enumerate(pairs):
    html_code += f'''
        <div class="cell cell-header time-block">
            <div><strong>{roman} Пара</strong></div> 
            <div>({time_range})</div>
        </div>
    '''
    for j in range(5):
        # Важливо: Якщо ви хочете, щоб дані відповідати групам,
        # то індекс 'j' має відповідати індексу групи.
        # Наразі 'j' йде від 0 до 4, що відповідає кількості днів.
        # Якщо у вас 6 груп, а днів 5, вам потрібно буде переглянути логіку 'schedule_data'.
        # Я залишаю 5 груп, щоб відповідати 5 дням.
        item = schedule_data[(i, j)] 
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

# Збільшимо висоту компонента, щоб врахувати новий рядок
components.html(html_code, height=880, scrolling=True) # Збільшено висоту

# ⬇️ ОДНА КНОПКА ЗАВАНТАЖЕННЯ PDF ⬇️
# Функція для генерації PDF-файлу
def generate_pdf(schedule_data, start_date, end_date, pairs, days, groups): # Передаємо groups
    pdf = FPDF()
    pdf.add_page()

    # Шлях до файлу шрифту (відносно кореня вашого додатку)
    regular_font_path = "fonts/DejaVuSans.ttf"
    bold_font_path = "fonts/DejaVuSans-Bold.ttf" # Припускаємо, що файл називається так

    try:
        # Додаємо регулярний шрифт
        pdf.add_font("DejaVuSans", "", regular_font_path, uni=True)
        
        # Додаємо жирний шрифт
        pdf.add_font("DejaVuSans", "B", bold_font_path, uni=True) 
        
        pdf.set_font("DejaVuSans", "", size=12) # Встановлюємо поточний шрифт як регулярний за замовчуванням
    except Exception as e:
        st.error(f"Помилка завантаження шрифту: {e}. Переконайтеся, що файли шрифтів (регулярний та жирний) існують у папці 'fonts' та правильно вказані шляхи.")
        return None 

    pdf.set_font("DejaVuSans", "B", 14)
    pdf.cell(200, 10, txt=f"Розклад: {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}", ln=True, align="C")
    pdf.ln(5)

    # Заголовки днів тижня у PDF
    pdf.set_font("DejaVuSans", "B", 10)
    # Налаштуйте ширину колонок для PDF, щоб відповідати кількості днів + час
    col_width = 180 / (len(days) + 1) # приблизна ширина для дня
    
    # Заголовок для часу
    pdf.cell(col_width, 10, txt="", border=1, align="C") # Пуста комірка для часу
    for day in days:
        pdf.cell(col_width, 10, txt=day, border=1, align="C")
    pdf.ln()

    # Заголовки груп у PDF
    pdf.set_font("DejaVuSans", "", 10) # Звичайний шрифт для груп
    pdf.cell(col_width, 10, txt="", border=1, align="C") # Пуста комірка
    for group in groups:
        pdf.cell(col_width, 10, txt=group, border=1, align="C")
    pdf.ln()


    # Оновлено для PDF: "Пара" і час на різних рядках
    for i, (roman, time_range) in enumerate(pairs):
        # Комірка для часу та номера пари
        pdf.set_font("DejaVuSans", "B", 10)
        pdf.cell(col_width, 20, txt=f"{roman} Пара\n({time_range})", border=1, align="C", center=True) # Використовуємо multi_cell, якщо це можливо, або 2 cell
        
        pdf.set_font("DejaVuSans", "", 8) # Зменшимо шрифт для вмісту клітинок
        for j, day in enumerate(days): # Тут 'j' відповідає дням, а не групам
            item = schedule_data[(i, j)]
            # Можливо, потрібно буде адаптувати, як відображається інформація в PDF
            # Залежить від того, чи хочете ви, щоб PDF відображав групи як окремі стовпці
            # або просто включав групу в опис предмета.
            # Якщо ви хочете, щоб кожна клітинка в HTML відповідала клітинці в PDF,
            # логіка PDF має бути більш складною.
            text = f"{item['subject']}\n{item['teacher']}\n{item['group']}"
            pdf.multi_cell(col_width, 10, txt=text, border=1, align="C") # Використовуємо multi_cell для кількох рядків
            
        pdf.ln(2) # Новий рядок після кожної пари


    return pdf.output(dest='S').encode('latin1') 

# Кнопка для завантаження PDF
pdf_bytes = generate_pdf(schedule_data, start_date, end_date, pairs, days, groups) # Передаємо groups в функцію

if pdf_bytes: 
    st.download_button(
        label="⬇️ Завантажити PDF",
        data=pdf_bytes,
        file_name="розклад.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Не вдалося згенерувати PDF-файл через помилку шрифту.")
