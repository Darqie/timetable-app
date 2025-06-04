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

# Генерація даних
schedule_data = {}
for i in range(5):
    for j in range(5):
        schedule_data[(i, j)] = {
            "teacher": f"Викладач {i+1}",
            "group": f"Група {chr(65 + j)}",
            "subject": f"Предмет {j+1}",
            "id": str(uuid.uuid4())
        }

# HTML + CSS (оновлено для зміни формату нумерації)
html_code = f"""
<style>
.timetable {{
    display: grid;
    grid-template-columns: 180px repeat(5, 1fr);
    grid-auto-rows: 110px;
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
</style>

<div class="timetable">
    <div class="cell cell-header"></div>
"""

# Дні
for day in days:
    html_code += f'<div class="cell cell-header">{day}</div>'

# Пари зліва + клітинки (оновлено: "Пара" і час на різних рядках)
for i, (roman, time_range) in enumerate(pairs):
    html_code += f'''
        <div class="cell cell-header time-block">
            <div><strong>{roman} Пара</strong></div> 
            <div>({time_range})</div>
        </div>
    '''
    for j in range(5):
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

components.html(html_code, height=820, scrolling=True)

# ⬇️ ОДНА КНОПКА ЗАВАНТАЖЕННЯ PDF ⬇️
# Функція для генерації PDF-файлу
def generate_pdf(schedule_data, start_date, end_date, pairs, days):
    pdf = FPDF()
    pdf.add_page()

    # Шлях до файлу шрифту (відносно кореня вашого додатку)
    font_path = "fonts/DejaVuSans.ttf" 

    try:
        pdf.add_font("DejaVuSans", "", font_path, uni=True)
        pdf.set_font("DejaVuSans", size=12)
    except Exception as e:
        st.error(f"Помилка завантаження шрифту: {e}. Переконайтеся, що файл {font_path} існує і доступний.")
        return None 

    pdf.cell(200, 10, txt=f"Розклад: {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}", ln=True, align="C")
    
    # Оновлено для PDF: "Пара" і час на різних рядках
    for i, (roman, time_range) in enumerate(pairs):
        pdf.set_font("DejaVuSans", "B", 12) # Жирний шрифт для "Римська цифра Пара"
        pdf.cell(0, 10, txt=f"{roman} Пара", ln=True) 
        
        pdf.set_font("DejaVuSans", "", 12) # Звичайний шрифт для часу
        pdf.cell(0, 10, txt=f"({time_range})", ln=True)
        
        for j, day in enumerate(days):
            item = schedule_data[(i, j)]
            text = f"  {day}: {item['subject']} — {item['teacher']} ({item['group']})"
            pdf.cell(0, 10, txt=text, ln=True)
        pdf.ln(2)

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
