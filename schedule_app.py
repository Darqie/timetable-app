import streamlit as st
import streamlit.components.v1 as components
import uuid
from datetime import date, timedelta
from fpdf import FPDF
import os
import json
import psycopg2
from sqlalchemy import text # Імпортуємо text для виконання DDL-запитів через SQLAlchemy

st.set_page_config(page_title="Розклад пар", layout="wide")

# --- Налаштування бази даних ---
@st.cache_resource
def get_db_connection():
    """Створює та кешує з'єднання з базою даних PostgreSQL."""
    try:
        conn = st.connection('postgresql', type='sql')
        # Спроба виконати простий запит для перевірки з'єднання
        # conn.query("SELECT 1;") # Цей рядок можна використовувати для швидкої перевірки, але він може бути зайвим
        st.success("Успішно підключено до PostgreSQL через st.connection!")
        return conn
    except Exception as e:
        st.error(f"Помилка підключення до бази даних: {e}")
        st.info("Перевірте ваш файл .streamlit/secrets.toml або налаштування секретів у Streamlit Cloud.")
        st.stop() # Зупиняємо виконання додатка, якщо немає з'єднання

def init_db(conn):
    """Ініціалізує базу даних, створює таблицю, якщо її немає.
       Використовує conn.session.execute() для DDL."""
    try:
        # Використовуємо conn.session.execute() для виконання DDL (CREATE TABLE)
        # text() потрібен для того, щоб SQLAlchemy обробляв рядок як сирий SQL
        conn.session.execute(text('''
            CREATE TABLE IF NOT EXISTS schedule (
                week_start_date TEXT PRIMARY KEY,
                data TEXT
            );
        '''))
        conn.session.commit() # Підтверджуємо зміни
        st.success("База даних ініціалізована. Таблиця 'schedule' існує або була створена.")
    except Exception as e:
        # Якщо виникає помилка під час створення таблиці, відкатуємо транзакцію
        conn.session.rollback()
        st.error(f"Помилка при ініціалізації бази даних (створення таблиці): {e}")
        st.stop() # Зупиняємо виконання, якщо не вдалося створити таблицю

def save_schedule_to_db(conn, week_start_date, schedule_data):
    """Зберігає дані розкладу для конкретного тижня в базу даних.
       Використовує conn.query() для INSERT/UPDATE."""
    week_start_date_str = week_start_date.strftime('%Y-%m-%d')
    serializable_schedule_data = {}
    for (day_idx, group_idx, pair_idx), item in schedule_data.items():
        key_str = f"{day_idx},{group_idx},{pair_idx}"
        serializable_schedule_data[key_str] = item

    data_json = json.dumps(serializable_schedule_data, ensure_ascii=False)
    
    try:
        # Використовуємо conn.query() для INSERT/UPDATE
        # Streamlit Connection автоматично обробляє параметри
        conn.query(
            "INSERT INTO schedule (week_start_date, data) VALUES (:week_start_date, :data) ON CONFLICT (week_start_date) DO UPDATE SET data = EXCLUDED.data;",
            params={
                "week_start_date": week_start_date_str,
                "data": data_json
            }
        )
        # conn.query автоматично commit() для INSERT/UPDATE для більшості випадків
        st.toast("Розклад збережено!")
    except Exception as e:
        st.error(f"Помилка при збереженні розкладу: {e}")

def load_schedule_from_db(conn, week_start_date):
    """Завантажує дані розкладу для конкретного тижня з бази даних.
       Використовує conn.query() для SELECT."""
    week_start_date_str = week_start_date.strftime('%Y-%m-%d')
    try:
        # conn.query() повертає DataFrame за замовчуванням
        df = conn.query("SELECT data FROM schedule WHERE week_start_date = :week_start_date;",
                        params={"week_start_date": week_start_date_str})
        
        if not df.empty:
            loaded_data_json = df.iloc[0]['data'] # Беремо дані з першого рядка
            deserialized_data = json.loads(loaded_data_json)
            schedule_data = {}
            for key_str, item in deserialized_data.items():
                day_idx, group_idx, pair_idx = map(int, key_str.split(','))
                schedule_data[(day_idx, group_idx, pair_idx)] = item
            return schedule_data
        return None
    except Exception as e:
        st.error(f"Помилка при завантаженні розкладу: {e}")
        # Ця помилка "UndefinedTable" свідчить про те, що таблиця не існує.
        # Це очікувана поведінка при першому запуску, якщо таблиці ще немає.
        # Ми можемо повернути None і дозволити ініціалізації створити її.
        return None


# Отримання з'єднання з базою даних
db_conn = get_db_connection()
init_db(db_conn) # Ініціалізація бази даних при старті додатка

# Розміщення назви "Розклад пар" по центру
st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Розклад пар</h2>", unsafe_allow_html=True)

st.markdown("---") # Розділювач

# ----- Блок Опцій: Вибір тижня, Зберегти, Завантажити -----

col_label, col_date_input, col_spacer_date, col_save_btn, col_download_btn, _ = st.columns([0.13, 0.15, 0.03, 0.1, 0.14, 0.45])

if 'start_date' not in st.session_state:
    st.session_state.start_date = date(2025, 6, 2) # Або date.today(), якщо хочете поточну дату як стартову
    initial_load = load_schedule_from_db(db_conn, st.session_state.start_date)
    if initial_load:
        st.session_state.schedule_data = initial_load
    else:
        st.session_state.schedule_data = {} # Буде заповнено стандартними даними нижче

with col_label:
    st.markdown(
        """
        <style>
        .compact-label {
            display: flex;
            align-items: center;
            height: 100%;
            padding-top: 0px;
            padding-bottom: 0px;
            margin-top: 0px;
            margin-bottom: 0px;
            text-align: right;
            line-height: 1;
        }
        </style>
        <p class="compact-label">Перший день тижня:</p>
        """,
        unsafe_allow_html=True
    )

with col_date_input:
    selected_date = st.date_input("", st.session_state.start_date, key="manual_date_picker")
    if selected_date != st.session_state.start_date:
        st.session_state.start_date = selected_date
        loaded_data = load_schedule_from_db(db_conn, st.session_state.start_date)
        if loaded_data:
            st.session_state.schedule_data = loaded_data
        else:
            st.session_state.schedule_data = {}
        st.experimental_rerun()

end_date = st.session_state.start_date + timedelta(days=4)
st.markdown(f"<h3 style='text-align: center; margin-top: 5px; margin-bottom: 5px;'>📆 {st.session_state.start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}</h3>", unsafe_allow_html=True)

# ----- Блок вибору тижнів: Минулий, Поточний, Майбутній -----
spacer_left, col_prev_week, col_current_week, col_next_week, spacer_right = st.columns([1, 0.25, 0.25, 0.25, 1])

def get_monday_of_week(target_date):
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)

with col_prev_week:
    if st.button("⏪ Минулий тиждень", key="prev_week_btn"):
        st.session_state.start_date = get_monday_of_week(st.session_state.start_date - timedelta(weeks=1))
        loaded_data = load_schedule_from_db(db_conn, st.session_state.start_date)
        if loaded_data:
            st.session_state.schedule_data = loaded_data
        else:
            st.session_state.schedule_data = {}
        st.experimental_rerun()

with col_current_week:
    if st.button("🗓️ Поточний тиждень", key="current_week_btn"):
        st.session_state.start_date = get_monday_of_week(date.today())
        loaded_data = load_schedule_from_db(db_conn, st.session_state.start_date)
        if loaded_data:
            st.session_state.schedule_data = loaded_data
        else:
            st.session_state.schedule_data = {}
        st.experimental_rerun()

with col_next_week:
    if st.button("⏩ Майбутній тиждень", key="next_week_btn"):
        st.session_state.start_date = get_monday_of_week(st.session_state.start_date + timedelta(weeks=1))
        loaded_data = load_schedule_from_db(db_conn, st.session_state.start_date)
        if loaded_data:
            st.session_state.schedule_data = loaded_data
        else:
            st.session_state.schedule_data = {}
        st.experimental_rerun()

st.markdown("---") # Розділювач
# ----- Кінець Блоку Опцій -----

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

# Ініціалізація або завантаження schedule_data
if not st.session_state.get('schedule_data') or not st.session_state.schedule_data:
    initial_schedule_data = {}
    for i_day in range(len(days)):
        for i_group in range(num_groups_per_day):
            for i_pair in range(len(pairs)):
                key = (i_day, i_group, i_pair)
                initial_schedule_data[key] = {
                    "teacher": f"Вч.{chr(65 + i_day)}.{i_group+1}.{i_pair+1}",
                    "group": group_names[i_group],
                    "subject": f"Предм.{i_pair+1}-{i_group+1}",
                    "id": str(uuid.uuid4())
                }
    st.session_state.schedule_data = initial_schedule_data
    # Якщо дані завантажуються вперше, зберігаємо їх у БД
    save_schedule_to_db(db_conn, st.session_state.start_date, st.session_state.schedule_data)

# Отримуємо поточні дані розкладу для відображення
current_schedule_data = st.session_state.schedule_data

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
.day-header-main {{
    background: var(--header-bg-day);
    font-size: 16px;
    grid-row: span {num_groups_per_day};
    border-radius: 0;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
}}
.day-header-text {{
    transform: rotate(-90deg);
    white-space: nowrap;
    transform-origin: center center;
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
    html_code += f'<div class="cell cell-header day-header-main"><span class="day-header-text">{day_name}</span></div>'

    for i_group in range(num_groups_per_day):
        html_code += f'<div class="cell group-sub-header">{group_names[i_group]}</div>'

        for i_pair in range(len(pairs)):
            item = current_schedule_data.get((i_day, i_group, i_pair), {
                "teacher": "Немає", "group": group_names[i_group], "subject": "Пусто", "id": str(uuid.uuid4())
            })
            item_id = item.get('id', str(uuid.uuid4()))
            
            # Екранування даних для HTML атрибутів, щоб уникнути проблем з лапками
            # Додаємо replace для лапок, щоб не ламався HTML/JS
            escaped_subject = item["subject"].replace('"', '&quot;')
            escaped_teacher = item["teacher"].replace('"', '&quot;')

            html_code += f'''
            <div class="cell" ondrop="drop(event, {i_day}, {i_group}, {i_pair})" ondragover="allowDrop(event)">
                <div id="{item_id}" class="draggable" draggable="true"
                     data-day="{i_day}" data-group="{i_group}" data-pair="{i_pair}"
                     data-subject="{escaped_subject}" data-teacher="{escaped_teacher}"
                     ondragstart="drag(event)">
                    <strong>{item["subject"]}</strong><br>
                    {item["teacher"]}
                </div>
            </div>
            '''

html_code += """
</div>

<script>
    function sendDataToStreamlit(data) {
        if (window.parent && window.parent.streamlit) {
            window.parent.streamlit.setComponentValue(data);
        } else {
            console.warn("Streamlit parent not found. Data not sent.");
        }
    }

    function allowDrop(ev) {
        ev.preventDefault();
    }

    function drag(ev) {
        ev.dataTransfer.setData("text", ev.target.id);
        ev.dataTransfer.setData("fromDay", ev.target.dataset.day);
        ev.dataTransfer.setData("fromGroup", ev.target.dataset.group);
        ev.dataTransfer.setData("fromPair", ev.target.dataset.pair);
        // Тут ми вже беремо з dataset, як і має бути
        ev.dataTransfer.setData("fromSubject", ev.target.dataset.subject);
        ev.dataTransfer.setData("fromTeacher", ev.target.dataset.teacher);
    }

    function drop(ev, toDay, toGroup, toPair) {
        ev.preventDefault();
        var draggedId = ev.dataTransfer.getData("text");
        var draggedElem = document.getElementById(draggedId);

        var fromDay = parseInt(ev.dataTransfer.getData("fromDay"));
        var fromGroup = parseInt(ev.dataTransfer.getData("fromGroup"));
        var fromPair = parseInt(ev.dataTransfer.getData("fromPair"));
        // Ці змінні (fromSubject, fromTeacher) більше не використовуються для обміну,
        // оскільки ми беремо їх з draggedElem.dataset після переміщення
        // var fromSubject = ev.dataTransfer.getData("fromSubject");
        // var fromTeacher = ev.dataTransfer.getData("fromTeacher");

        var dropTarget = ev.target;
        while (!dropTarget.classList.contains("cell") || dropTarget.classList.contains("cell-header")) {
            dropTarget = dropTarget.parentNode;
            if (!dropTarget) return;
        }

        var existing = dropTarget.querySelector(".draggable");

        if (existing) {
            // Swap logic
            dropTarget.appendChild(draggedElem); // Place dragged item into new cell
            var originalParentOfDragged = document.querySelector(`.cell[ondrop*="drop(event, ${fromDay}, ${fromGroup}, ${fromPair})"]`);
            if (originalParentOfDragged) {
                 originalParentOfDragged.appendChild(existing); // Place existing item into original cell
                 // Update dataset for swapped item
                 existing.dataset.day = fromDay;
                 existing.dataset.group = fromGroup;
                 existing.dataset.pair = fromPair;
            }
        } else {
            // Just move logic
            dropTarget.appendChild(draggedElem);
        }
        
        // Update dataset for the dragged item
        draggedElem.dataset.day = toDay;
        draggedElem.dataset.group = toGroup;
        draggedElem.dataset.pair = toPair;

        var updatedSchedule = {};
        document.querySelectorAll('.draggable').forEach(function(el) {
            var day = parseInt(el.dataset.day);
            var group = parseInt(el.dataset.group);
            var pair = parseInt(el.dataset.pair);
            var subject = el.dataset.subject; // Беремо з data-атрибута елемента
            var teacher = el.dataset.teacher; // Беремо з data-атрибута елемента
            var id = el.id;
            updatedSchedule[`${day},${group},${pair}`] = {
                subject: subject,
                teacher: teacher,
                group: el.parentNode.previousElementSibling ? el.parentNode.previousElementSibling.innerText : 'Unknown Group',
                id: id
            };
        });
        sendDataToStreamlit(updatedSchedule);
    }
</script>
"""

# Видалено 'key' з components.html, як було виправлено
component_value = components.html(html_code, height=800, scrolling=True)

# Додано перевірку типу для component_value
if component_value is not None and isinstance(component_value, dict):
    new_schedule_data = {}
    for key_str, item in component_value.items():
        day_idx, group_idx, pair_idx = map(int, key_str.split(','))
        new_schedule_data[(day_idx, group_idx, pair_idx)] = item
    
    if new_schedule_data != st.session_state.schedule_data:
        st.session_state.schedule_data = new_schedule_data
        save_schedule_to_db(db_conn, st.session_state.start_date, st.session_state.schedule_data)
        st.experimental_rerun()
# else: # Закоментуйте або видаліть цей else блок, щоб уникнути помилки DeltaGenerator, якщо компонент ще не повернув дані
#     st.info("HTML-компонент ще не повернув дані або повернув неочікуваний тип.") # Додано для налагодження
#     st.error(f"Неочікуваний тип даних від HTML-компонента: {type(component_value)}. Повинно бути 'dict'.")


def generate_pdf(schedule_data_pdf, start_date_pdf, end_date_pdf, pairs_pdf, days_pdf, group_names_pdf, num_groups_per_day_pdf):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    regular_font_path = "fonts/DejaVuSans.ttf"
    bold_font_path = "fonts/DejaVuSans-Bold.ttf"

    try:
        if not os.path.exists("fonts"):
            os.makedirs("fonts")
        if not os.path.exists(regular_font_path):
            st.error(f"Шрифт не знайдено: {regular_font_path}. Будь ласка, завантажте 'DejaVuSans.ttf' у папку 'fonts'.")
            return None
        if not os.path.exists(bold_font_path):
            st.error(f"Шрифт не знайдено: {bold_font_path}. Будь ласка, завантажте 'DejaVuSans-Bold.ttf' у папку 'fonts'.")
            return None

        pdf.add_font("DejaVuSans", "", regular_font_path, uni=True)
        pdf.add_font("DejaVuSans", "B", bold_font_path, uni=True)
        pdf.set_font("DejaVuSans", "", size=10)
    except Exception as e:
        st.error(f"Помилка завантаження шрифту: {e}. Переконайтеся, що файли шрифтів існують і доступні.")
        return None

    pdf.set_font("DejaVuSans", "B", 14)
    pdf.cell(0, 10, txt=f"Розклад: {start_date_pdf.strftime('%d.%m.%Y')} – {end_date_pdf.strftime('%d.%m.%Y')}", ln=True, align="C")
    pdf.ln(5)

    page_width = pdf.w - 2 * pdf.l_margin
    day_col_width = 30
    group_col_width = 30
    pair_col_width = (page_width - day_col_width - group_col_width) / len(pairs_pdf)

    header_height = 15
    content_cell_height = 15

    initial_x = pdf.l_margin
    initial_y = pdf.get_y()

    pdf.set_font("DejaVuSans", "B", 10)

    pdf.set_xy(initial_x, initial_y)
    pdf.cell(day_col_width, header_height, txt="", border=1, align="C")

    pdf.set_xy(initial_x + day_col_width, initial_y)
    pdf.cell(group_col_width, header_height, txt="Група", border=1, align="C")

    current_x_for_pairs = initial_x + day_col_width + group_col_width
    for roman, time_range in pairs_pdf:
        pdf.set_xy(current_x_for_pairs, initial_y)
        pdf.multi_cell(pair_col_width, header_height / 2, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C")
        current_x_for_pairs += pair_col_width

    pdf.set_xy(initial_x, initial_y + header_height)

    pdf.set_font("DejaVuSans", "", 7)

    for i_day, day_name in enumerate(days_pdf):
        required_height_for_day_block = content_cell_height * num_groups_per_day_pdf

        if pdf.get_y() + required_height_for_day_block > (pdf.h - pdf.b_margin):
            pdf.add_page()
            pdf.set_font("DejaVuSans", "B", 10)
            pdf.set_xy(initial_x, pdf.t_margin)
            pdf.cell(day_col_width, header_height, txt="", border=1, align="C")
            pdf.set_xy(initial_x + day_col_width, pdf.t_margin)
            pdf.cell(group_col_width, header_height, txt="Група", border=1, align="C")

            current_x_for_pairs = initial_x + day_col_width + group_col_width
            for roman, time_range in pairs_pdf:
                pdf.set_xy(current_x_for_pairs, pdf.t_margin)
                pdf.multi_cell(pair_col_width, header_height / 2, txt=f"{roman} ПАРА\n({time_range})", border=1, align="C")
                current_x_for_pairs += pair_col_width
            pdf.set_xy(initial_x, pdf.t_margin + header_height)
            pdf.set_font("DejaVuSans", "", 7)

        day_block_start_y = pdf.get_y()

        day_text_center_x = initial_x + day_col_width / 2
        day_text_center_y = day_block_start_y + required_height_for_day_block / 2

        pdf.set_fill_color(240, 200, 100)
        pdf.rect(initial_x, day_block_start_y, day_col_width, required_height_for_day_block, 'F')
        pdf.rect(initial_x, day_block_start_y, day_col_width, required_height_for_day_block, 'D')

        pdf.set_font("DejaVuSans", "B", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.rotate(90, day_text_center_x, day_text_center_y)

        text_width = pdf.get_string_width(day_name)
        pdf.set_xy(day_text_center_x - text_width / 2, day_text_center_y - pdf.font_size / 2)
        pdf.cell(text_width, pdf.font_size, txt=day_name, align="C")
        pdf.rotate(0)
        pdf.set_font("DejaVuSans", "", 7)

        for i_group in range(num_groups_per_day_pdf):
            current_row_start_x = initial_x + day_col_width
            current_row_start_y = day_block_start_y + (i_group * content_cell_height)

            pdf.set_xy(current_row_start_x, current_row_start_y)

            pdf.set_font("DejaVuSans", "", 8)
            pdf.cell(group_col_width, content_cell_height, txt=group_names_pdf[i_group], border=1, align="C")

            pdf.set_xy(current_row_start_x + group_col_width, current_row_start_y)

            pdf.set_font("DejaVuSans", "", 7)
            for i_pair in range(len(pairs_pdf)):
                item = schedule_data_pdf.get((i_day, i_group, i_pair), {
                    "subject": "Пусто", "teacher": "Немає"
                })
                text = f"{item['subject']}\n{item['teacher']}"

                cell_start_x = pdf.get_x()
                cell_start_y = pdf.get_y()

                pdf.multi_cell(pair_col_width, content_cell_height / 2, txt=text, border=1, align="C")

                pdf.set_xy(cell_start_x + pair_col_width, cell_start_y)

        pdf.set_xy(initial_x, day_block_start_y + required_height_for_day_block)

    return pdf.output(dest='S').encode('latin1')

pdf_file_name = f"розклад_{st.session_state.start_date.strftime('%d.%m')}–{end_date.strftime('%d.%m')}.pdf"

with col_save_btn:
    if st.button("💾 Зберегти", key="save_button"):
        save_schedule_to_db(db_conn, st.session_state.start_date, st.session_state.schedule_data)
        st.success("Розклад збережено в базу даних!")

with col_download_btn:
    pdf_bytes = generate_pdf(st.session_state.schedule_data, st.session_state.start_date, end_date, pairs, days, group_names, num_groups_per_day)

    if pdf_bytes:
        st.download_button(
            label="⬇️ Завантажити PDF",
            data=pdf_bytes,
            file_name=pdf_file_name,
            mime="application/pdf",
            key="download_button"
        )
    else:
        st.warning("Не вдалося згенерувати PDF-файл.")
