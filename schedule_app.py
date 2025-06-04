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

# Створюємо список груп для зручності відображення
# (можна адаптувати, якщо назви груп не просто "Група X")
group_names = [f"Група {i+1}" for i in range(num_groups_per_day)]


# Генерація даних
# Тепер ключі schedule_data будуть (пара_індекс, день_індекс, група_індекс)
schedule_data = {}
for i_pair in range(len(pairs)):
    for i_day in range(len(days)):
        for i_group in range(num_groups_per_day):
            # Унікальний ключ для кожної клітинки
            key = (i_pair, i_day, i_group)
            schedule_data[key] = {
                "teacher": f"Викладач {i_pair+1}-{i_day+1}-{i_group+1}",
                "group": group_names[i_group],
                "subject": f"Предмет {i_pair+1}-{i_day+1}-{i_group+1}",
                "id": str(uuid.uuid4())
            }

# HTML + CSS
html_code = f"""
<style>
.timetable {{
    display: grid;
    /* 180px для часу, потім (кількість днів * кількість груп на день) стовпців */
    grid-template-columns: 180px repeat({len(days) * num_groups_per_day}, 1fr);
    grid-auto-rows: minmax(50px, auto); /* Адаптивна висота рядків */
    gap: 2px;
    font-family: 'Segoe UI', sans-serif;
    overflow-x: auto; /* Додаємо горизонтальну прокрутку */
    max-width: 100%; /* Обмежуємо ширину, щоб не виходило за межі */
}}
.cell {{
    border: 1px solid #ccc;
    background: #f9f9f9;
    position: relative;
    padding: 4px; /* Зменшений padding для великої кількості клітинок */
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
    font-size: 12px; /* Зменшений шрифт для вмісту */
    min-width: 80px; /* Мінімальна ширина для клітинки групи */
    box-sizing: border-box; /* Важливо для розрахунку ширини */
}}
.cell-header {{
    background: #e0ecff;
    font-weight: bold;
    text-align: center;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5px;
}}
.draggable {{
    background: #d0e7ff;
    border-radius: 6px;
    padding: 4px; /* Зменшений padding */
    cursor: grab;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
    font-size: 11px; /* Зменшений шрифт для draggable елементів */
}}
.time-block {{
    font-size: 14px;
    color: #444;
    text-align: center;
    line-height: 1.2; 
}}
.day-header {{
    grid-column: span {num_groups_per_day}; /* Заголовок дня охоплює 6 колонок */
    background: #cce0ff; /* Трохи інший колір для заголовків днів */
    font-size: 16px;
}}
.group-sub-header {{
    background: #e0ecff;
    font-weight: bold;
    text-align: center;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3px; /* Ще менший відступ */
    font-size: 12px;
}}
</style>

<div class="timetable">
    <div class="cell cell-header"></div> """

# Перший рядок: Заголовки днів (об'єднані комірки)
for day in days:
    html_code += f'<div class="cell cell-header day-header">{day}</div>'

# Другий рядок: Заголовки груп під відповідними днями
html_code += f'<div class="cell cell-header"></div>' # Пуста комірка для відповідності з першим стовпцем (часом)
for day in days:
    for group_name in group_names:
        html_code += f'<div class="cell group-sub-header">{group_name}</div>'

# Основна частина таблиці: Пари + клітинки з даними
for i_pair, (roman, time_range) in enumerate(pairs):
    html_code += f'''
        <div class="cell cell-header time-block">
            <div><strong>{roman} Пара</strong></div> 
            <div>({time_range})</div>
        </div>
    '''
    # Для кожної пари проходимося по днях, а потім по групах
    for i_day in range(len(days)):
        for i_group in range(num_groups_per_day):
            item = schedule_data[(i_pair, i_day, i_group)]
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
  // Перевіряємо, чи dropTarget є .cell або його дочірнім елементом
  while (!dropTarget.classList.contains("cell")) {
    dropTarget = dropTarget.parentNode;
    if (!dropTarget) return; // Вихід, якщо батьківський елемент не знайдено
  }

  // Перевіряємо, чи dropTarget є заголовком, якщо так, то не дозволяємо перетягування
  if (dropTarget.classList.contains("cell-header") || dropTarget.classList.contains("group-sub-header")) {
    return; // Не дозволяємо кидати на заголовки
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

# Збільшимо висоту компонента
components.html(html_code, height=880, scrolling=True) # Можливо, знадобиться ще більше, залежить від вмісту


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

    # Ширина сторінки мінус відступи
    page_width = pdf.w - 2 * pdf.l_margin
    # Ширина однієї комірки для групи
    group_col_width = (page_width - 30) / (len(days) * num_groups_per_day) # 30px для колонки часу

    # Заголовки днів (об'єднані)
    pdf.set_font("DejaVuSans", "B", 12)
    # Зберігаємо X-позицію для наступного рядка
    start_x = pdf.get_x()
    start_y = pdf.get_y()

    # Заголовок для "Пари/Часу"
    pdf.multi_cell(30, 20, txt="Пара\nЧас", border=1, align="C", valign="M") # Початкова комірка для часу
    pdf.set_xy(start_x + 30, start_y) # Переміщуємося на початок першого дня

    for day in days:
        # FPDF не має прямого grid-column-span. Ми вручну малюємо об'єднану комірку
        # Комірка дня охоплює N колонок груп
        pdf.cell(group_col_width * num_groups_per_day, 10, txt=day, border=1, align="C")
    pdf.ln()

    # Заголовки груп
    pdf.set_font("DejaVuSans", "", 8) # Зменшений шрифт для груп
    # Відновлюємо X-позицію
    pdf.set_xy(start_x, pdf.get_y()) # Повертаємося до початку рядка

    pdf.cell(30, 10, txt="", border=1, align="C") # Пуста комірка під "Пара/Час"
    for day in days:
        for group_name in group_names:
            pdf.cell(group_col_width, 10, txt=group_name, border=1, align="C")
    pdf.ln()

    # Основний контент таблиці
    pdf.set_font("DejaVuSans", "", 7) # Ще менший шрифт для вмісту клітинок
    for i_pair, (roman, time_range) in enumerate(pairs):
        start_x = pdf.get_x() # Зберігаємо X-позицію початку рядка
        start_y = pdf.get_y() # Зберігаємо Y-позицію початку рядка

        # Комірка для часу та номера пари
        pdf.multi_cell(30, 20, txt=f"{roman} Пара\n({time_range})", border=1, align="C", valign="M")
        
        # Переміщуємося на початок колонок для даних
        pdf.set_xy(start_x + 30, start_y)

        for i_day in range(len(days)):
            for i_group in range(num_groups_per_day):
                item = schedule_data[(i_pair, i_day, i_group)]
                text = f"{item['subject']}\n{item['teacher']}\n{item['group']}"
                # multi_cell для вмісту, щоб він міг переноситись
                # Перевіряємо, чи влізе текст в клітинку
                current_x = pdf.get_x()
                current_y = pdf.get_y()

                # Створюємо тимчасовий об'єкт FPDF для розрахунку висоти тексту
                temp_pdf = FPDF()
                temp_pdf.add_font("DejaVuSans", "", regular_font_path, uni=True)
                temp_pdf.add_font("DejaVuSans", "B", bold_font_path, uni=True)
                temp_pdf.set_font("DejaVuSans", "", 7)
                
                # Обчислюємо висоту, яку займе multi_cell
                text_height = temp_pdf.get_string_width(text) / group_col_width * temp_pdf.font_size * 1.2 # Приблизна висота
                
                # Встановлюємо максимальну висоту клітинки
                cell_height = max(20, text_height + 2) # Мінімальна 20, або більше якщо текст великий

                pdf.multi_cell(group_col_width, 20 / 3, txt=text, border=1, align="C") # 20 / 3 для 3-х рядків тексту
                # Повертаємося на поточну Y-позицію, щоб продовжити наступну клітинку в тому ж рядку
                pdf.set_xy(current_x + group_col_width, current_y)
        
        pdf.ln(20) # Переходимо на новий рядок після заповнення всіх груп для поточної пари
        # Увага: FPDF не дуже добре працює з автоматичним вирівнюванням рядків,
        # якщо комірки мають різну висоту. Можливо, доведеться вручну обчислювати max_row_height

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
