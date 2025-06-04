import streamlit as st
import streamlit.components.v1 as components
import uuid
from datetime import date, timedelta
from fpdf import FPDF
import os

st.set_page_config(page_title="Розклад пар", layout="wide")

st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Розклад пар</h2>", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Початок тижня", date(2025, 6, 2))
with col2:
    end_date = start_date + timedelta(days=4)
    st.markdown(f"### 📆 {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}")

pairs = [
    ("I", "8:30 – 9:50"),
    ("II", "10:00 – 11:20"),
    ("III", "11:35 – 12:55"),
    ("IV", "13:15 – 14:35"),
    ("V", "14:45 – 16:05"),
]

days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
num_groups_per_day = 6

group_names = [f"Група {i+1}" for i in range(num_groups_per_day)]

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

html_code = f"""
<style>
:root {{
    --main-bg-color: #F8F8F8;
    --header-bg-top-left: rgba(220, 230, 240, 0.8);
    --header-bg-pair: rgba(180, 210, 230, 0.8);
    --header-bg-group: rgba(200, 220, 240, 0.8);
    --header-bg-day: rgba(240, 200, 100, 0.9);
    --cell-bg: rgba(255, 255, 255, 0.7);
    --border-color: #C0D0E0;
    --draggable-bg: rgba(255, 240, 180, 0.8);
    --text-color: #333333;
    --shadow-light: 0 2px 5px rgba(0,0,0,0.1);
    --shadow-medium: 0 4px 8px rgba(0,0,0,0.15);
}}

body {{ background-color: var(--main-bg-color); }}

.timetable {{
    display: grid;
    grid-template-columns: 120px 80px repeat({len(pairs)}, 1fr);
    grid-auto-rows: minmax(55px, auto);
    gap: 1px;
    font-family: 'Roboto', sans-serif;
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-medium);
    margin-top: 20px;
    background-color: var(--main-bg-color);
    max-width: 100%;
    overflow-x: auto;
}}

.cell {{
    border: 1px solid var(--border-color);
    background: var(--cell-bg);
    position: relative;
    padding: 4px;
    overflow: hidden;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box;
    font-size: 10px;
}}
.cell-header {{
    font-weight: bold;
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 6px;
    color: var(--text-color);
    box-shadow: var(--shadow-light);
}}
.top-left-corner {{
    background: var(--header-bg-top-left);
    border-radius: 12px 0 0 0;
}}
.pair-header {{
    background: var(--header-bg-pair);
    font-size: 16px;
    border-radius: 0;
}}
/* Оновлені стилі для заголовка дня */
.day-header-main {{
    background: var(--header-bg-day);
    font-size: 16px;
    grid-row: span {num_groups_per_day};
    border-radius: 0;
    position: relative; /* Для позиціонування внутрішнього span */
    display: flex;
    align-items: center; /* Вирівнюємо по вертикалі */
    justify-content: center; /* Вирівнюємо по горизонталі */
    border: none; /* Забираємо всі рамки з контейнера */
}}
.day-header-text {{
    transform: rotate(-90deg);
    white-space: nowrap;
    transform-origin: center center;
    /* Оновлено: якщо потрібно, для більш точного центрування */
    /* top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) rotate(-90deg); */
    font-weight: bold;
}}
.group-sub-header {{
    background: var(--header-bg-group);
    font-size: 12px;
    padding: 5px;
    border-radius: 0;
}}
.draggable {{
    background: var(--draggable-bg);
    border-radius: 6px;
    padding: 4px;
    cursor: grab;
    box-shadow: 1px 1px 3px rgba(0,0,0,0.15);
    width: 95%;
    font-size: 9px;
    line-height: 1.2;
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

for roman, time_range in pairs:
    html_code += f'''
        <div class="cell cell-header pair-header">
            <div><strong>{roman} ПАРА</strong></div>
            <div class="time-block">({time_range})</div>
        </div>
    '''

for i_day, day_name in enumerate(days):
    # Обгортаємо текст дня в span для повороту
    html_code += f'<div class="cell cell-header day-header-main"><span class="day-header-text">{day_name}</span></div>'

    for i_group in range(num_groups_per_day):
        html_code += f'<div class="cell group-sub-header">{group_names[i_group]}</div>'

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

def generate_pdf(schedule_data, start_date, end_date, pairs, days, group_names, num_groups_per_day):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    regular_font_path = "fonts/DejaVuSans.ttf"
    bold_font_path = "fonts/DejaVuSans-Bold.ttf"

    try:
        if not os.path.exists(regular_font_path):
            raise FileNotFoundError(f"Шрифт не знайдено: {regular_font_path}. Переконайтеся, що файли шрифтів (DejaVuSans.ttf) існують у папці 'fonts'.")
        if not os.path.exists(bold_font_path):
            raise FileNotFoundError(f"Шрифт не знайдено: {bold_font_path}. Переконайтеся, що файли шрифтів (DejaVuSans-Bold.ttf) існують у папці 'fonts'.")

        pdf.add_font("DejaVuSans", "", regular_font_path, uni=True)
        pdf.add_font("DejaVuSans", "B", bold_font_path, uni=True)
        pdf.set_font("DejaVuSans", "", size=10)
    except Exception as e:
        st.error(f"Помилка завантаження шрифту: {e}")
        return None

    pdf.set_font("DejaVuSans", "B", 14)
    pdf.cell(0, 10, txt=f"Розклад: {start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}", ln=True, align="C")
    pdf.ln(5)

    page_width = pdf.w - 2 * pdf.l_margin
    day_col_width = 30
    group_col_width = 30
    pair_col_width = (page_width - day_col_width - group_col_width) / len(pairs)

    header_height = 15
    content_cell_height = 15

    initial_x = pdf.l_margin 
    initial_y = pdf.get_y()

    # Малюємо верхні заголовки (порожня комірка, "Група", "Пари")
    pdf.set_font("DejaVuSans", "B", 10)
    
    # Верхній лівий кут (порожній)
    pdf.set_xy(initial_x, initial_y)
    pdf.cell(day_col_width, header_height, txt="", border=1, align="C")

    # Заголовок "Група"
    pdf.set_xy(initial_x + day_col_width, initial_y)
    pdf.cell(group_col_width, header_height, txt="Група", border=1, align="C")

    # Заголовки пар
    current_x_for_pairs = initial_x + day_col_width + group_col_width
    for roman, time_range in pairs:
        pdf.set_xy(current_x_for_pairs, initial_y)
        pdf.multi_cell(pair_col_width, header_height / 2, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C")
        current_x_for_pairs += pair_col_width
    
    pdf.set_xy(initial_x, initial_y + header_height)

    pdf.set_font("DejaVuSans", "", 7)
    
    for i_day, day_name in enumerate(days):
        # Перевіряємо, чи вміститься блок дня на поточній сторінці
        if pdf.get_y() + (content_cell_height * num_groups_per_day) > (pdf.h - pdf.b_margin):
            pdf.add_page()
            # Перемальовуємо верхні заголовки на новій сторінці
            pdf.set_font("DejaVuSans", "B", 10)
            pdf.set_xy(initial_x, pdf.t_margin)
            pdf.cell(day_col_width, header_height, txt="", border=1, align="C")
            pdf.set_xy(initial_x + day_col_width, pdf.t_margin)
            pdf.cell(group_col_width, header_height, txt="Група", border=1, align="C")
            
            current_x_for_pairs = initial_x + day_col_width + group_col_width
            for roman, time_range in pairs:
                pdf.set_xy(current_x_for_pairs, pdf.t_margin)
                pdf.multi_cell(pair_col_width, header_height / 2, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C")
                current_x_for_pairs += pair_col_width
            pdf.set_xy(initial_x, pdf.t_margin + header_height)
            pdf.set_font("DejaVuSans", "", 7)

        day_block_start_y = pdf.get_y()

        # Позиція для центрування повернутого тексту дня
        day_text_center_x = initial_x + day_col_width / 2
        day_text_center_y = day_block_start_y + (content_cell_height * num_groups_per_day) / 2

        # Малюємо вертикальний текст дня лише один раз для всього блоку дня
        if i_day == 0 or (i_day > 0 and pdf.get_page_height() - day_block_start_y > content_cell_height * num_groups_per_day): # Продовжуємо, якщо є місце або це перший день
             pdf.set_font("DejaVuSans", "B", 12)
             pdf.rotate(90, day_text_center_x, day_text_center_y)
             # Центруємо текст відносно його власної ширини
             text_width = pdf.get_string_width(day_name)
             # У rotated state, x-coord = y-coord from unrotated origin, y-coord = -x-coord from unrotated origin
             # Отже, щоб центрувати, ми віднімаємо половину ширини тексту від day_text_center_x (яка є y-координатою для rotated тексту)
             # І для y-координати (x-координата для rotated тексту), ми використовуємо day_text_center_y
             pdf.set_xy(day_text_center_x - text_width / 2, day_text_center_y - pdf.font_size / 2)
             pdf.cell(text_width, pdf.font_size, txt=day_name, align="C")
             pdf.rotate(0) # Повертаємо назад
             pdf.set_font("DejaVuSans", "", 7) # Повертаємо основний шрифт

        for i_group in range(num_groups_per_day):
            current_row_start_x = pdf.get_x()
            current_row_start_y = pdf.get_y()

            # Малюємо тільки праву вертикальну межу для стовпця дня
            # та горизонтальні межі між групами
            pdf.line(initial_x + day_col_width, current_row_start_y, initial_x + day_col_width, current_row_start_y + content_cell_height) # Права вертикальна лінія для стовпця дня
            pdf.line(initial_x, current_row_start_y + content_cell_height, initial_x + day_col_width, current_row_start_y + content_cell_height) # Горизонтальна лінія знизу (якщо не остання група)

            # Малюємо ліву вертикальну межу для стовпця дня
            # Це потрібно, щоб стовпець дня мав ліву межу, яка не є частиною rotated text
            if i_group == 0:
                pdf.line(initial_x, day_block_start_y, initial_x, day_block_start_y + content_cell_height * num_groups_per_day)

            # Повертаємо курсор на початок стовпця "Група" для поточного рядка
            pdf.set_xy(initial_x + day_col_width, current_row_start_y)

            pdf.set_font("DejaVuSans", "", 8)
            pdf.cell(group_col_width, content_cell_height, txt=group_names[i_group], border=1, align="C")
            
            pdf.set_xy(initial_x + day_col_width + group_col_width, current_row_start_y)

            pdf.set_font("DejaVuSans", "", 7)
            for i_pair in range(len(pairs)):
                item = schedule_data[(i_day, i_group, i_pair)]
                text = f"{item['subject']}\n{item['teacher']}"

                cell_start_x = pdf.get_x()
                cell_start_y = pdf.get_y()

                pdf.multi_cell(pair_col_width, content_cell_height / 2, txt=text, border=1, align="C")
                
                pdf.set_xy(cell_start_x + pair_col_width, cell_start_y)
            
            pdf.set_xy(initial_x, current_row_start_y + content_cell_height)
        
    return pdf.output(dest='S').encode('latin1')

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
