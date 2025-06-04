import streamlit as st
import streamlit.components.v1 as components
import uuid
from datetime import date, timedelta
from fpdf import FPDF
import os
import sqlite3

# --- Налаштування Streamlit ---
st.set_page_config(page_title="Розклад пар", layout="wide")

# --- Константы ---
DB_NAME = "schedule.db"
MONDAY_INITIAL_DATE = date(2025, 6, 2) # Понеділок для початкової дати

PAIRS = [
    ("I", "8:30 – 9:50"),
    ("II", "10:00 – 11:20"),
    ("III", "11:35 – 12:55"),
    ("IV", "13:15 – 14:35"),
    ("V", "14:45 – 16:05"),
]

DAYS = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
NUM_GROUPS_PER_DAY = 6 # ЗВЕРНІТЬ УВАГУ: Велика 'D'

GROUP_NAMES = [f"Група {i+1}" for i in range(NUM_GROUPS_PER_DAY)]

# --- Функції для роботи з базою даних SQLite ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Дозволяє доступ до колонок за іменем
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_start_date TEXT NOT NULL,
            day_index INTEGER NOT NULL,
            group_index INTEGER NOT NULL,
            pair_index INTEGER NOT NULL,
            subject TEXT,
            teacher TEXT,
            item_id TEXT NOT NULL UNIQUE,
            UNIQUE(week_start_date, day_index, group_index, pair_index)
        )
    """)
    conn.commit()
    conn.close()

def save_schedule(week_start_date, schedule_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Видаляємо всі записи для цього тижня, щоб уникнути дублікатів перед збереженням
    cursor.execute("DELETE FROM schedules WHERE week_start_date = ?", (week_start_date.isoformat(),))
    
    for (day_idx, group_idx, pair_idx), item in schedule_data.items():
        cursor.execute("""
            INSERT INTO schedules (week_start_date, day_index, group_index, pair_index, subject, teacher, item_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (week_start_date.isoformat(), day_idx, group_idx, pair_idx, item['subject'], item['teacher'], item['id']))
    
    conn.commit()
    conn.close()
    st.success(f"Розклад для тижня {week_start_date.strftime('%d.%m.%Y')} збережено!")

def load_schedule(week_start_date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules WHERE week_start_date = ?", (week_start_date.isoformat(),))
    rows = cursor.fetchall()
    conn.close()
    
    loaded_data = {}
    if rows:
        for row in rows:
            key = (row['day_index'], row['group_index'], row['pair_index'])
            loaded_data[key] = {
                "teacher": row['teacher'],
                "group": GROUP_NAMES[row['group_index']], # Група не зберігається в DB, але її можна відновити
                "subject": row['subject'],
                "id": row['item_id']
            }
        st.info(f"Розклад для тижня {week_start_date.strftime('%d.%m.%Y')} завантажено.")
    else:
        st.warning(f"Розклад для тижня {week_start_date.strftime('%d.%m.%Y')} не знайдено в базі даних. Створюється шаблонний розклад.")
        # Якщо розкладу немає, генеруємо шаблонний
        for i_day in range(len(DAYS)):
            for i_group in range(NUM_GROUPS_PER_DAY): # ВИПРАВЛЕНО ТУТ: NUM_GROUPS_PER_DAY
                for i_pair in range(len(PAIRS)):
                    key = (i_day, i_group, i_pair)
                    loaded_data[key] = {
                        "teacher": f"Вч.{chr(65 + i_day)}.{i_group+1}.{i_pair+1}",
                        "group": GROUP_NAMES[i_group],
                        "subject": f"Предм.{i_pair+1}-{i_group+1}",
                        "id": str(uuid.uuid4())
                    }
    return loaded_data

def get_all_saved_weeks():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT week_start_date FROM schedules ORDER BY week_start_date DESC")
    weeks = [date.fromisoformat(row['week_start_date']) for row in cursor.fetchall()]
    conn.close()
    return weeks

# --- Ініціалізація бази даних та стану сесії ---
init_db()

if 'start_date' not in st.session_state:
    st.session_state.start_date = MONDAY_INITIAL_DATE # Початкова дата

if 'schedule_display_data' not in st.session_state:
    # Завантажуємо розклад при першому запуску або якщо стан пустий
    st.session_state.schedule_display_data = load_schedule(st.session_state.start_date)

# --- Функції для навігації по тижнях ---
def get_monday_of_week(target_date):
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)

def set_week_and_rerun(new_start_date):
    st.session_state.start_date = new_start_date
    st.session_state.schedule_display_data = load_schedule(new_start_date) # Завантажуємо новий розклад при зміні тижня
    st.experimental_rerun()

# --- UI Компоненти Streamlit ---
st.markdown("<h2 style='text-align: center; margin-bottom: 10px;'>Розклад пар</h2>", unsafe_allow_html=True)
st.markdown("---")

# ----- Блок Опцій: Вибір тижня, Зберегти, Завантажити -----
col_label, col_date_input, col_spacer_date, col_load_select, col_save_btn, col_download_btn = st.columns([0.13, 0.15, 0.03, 0.15, 0.1, 0.14])

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
    selected_date_manual = st.date_input("", st.session_state.start_date, key="manual_date_picker")
    if selected_date_manual != st.session_state.start_date:
        set_week_and_rerun(selected_date_manual)

with col_spacer_date:
    st.write("")

with col_load_select:
    saved_weeks = get_all_saved_weeks()
    # Форматування дат для відображення в селектбокс
    saved_weeks_formatted = {wk.strftime('%d.%m.%Y'): wk for wk in saved_weeks}
    
    # Додаємо "Обрати збережений розклад" як перший елемент
    options = ["Обрати збережений розклад"] + list(saved_weeks_formatted.keys())
    
    selected_saved_week_str = st.selectbox("Завантажити:", options=options, key="load_week_selector")
    
    if selected_saved_week_str != "Обрати збережений розклад":
        selected_saved_week_date = saved_weeks_formatted[selected_saved_week_str]
        if selected_saved_week_date != st.session_state.start_date:
            set_week_and_rerun(selected_saved_week_date)

end_date = st.session_state.start_date + timedelta(days=4)

st.markdown(f"<h3 style='text-align: center; margin-top: 5px; margin-bottom: 5px;'>📆 {st.session_state.start_date.strftime('%d.%m.%Y')} – {end_date.strftime('%d.%m.%Y')}</h3>", unsafe_allow_html=True)

# ----- Блок кнопок навігації по тижнях -----
spacer_left, col_prev_week, col_current_week, col_next_week, spacer_right = st.columns([1, 0.25, 0.25, 0.25, 1])

with col_prev_week:
    if st.button("⏪ Минулий тиждень", key="prev_week_btn"):
        set_week_and_rerun(get_monday_of_week(st.session_state.start_date - timedelta(weeks=1)))

with col_current_week:
    if st.button("🗓️ Поточний тиждень", key="current_week_btn"):
        set_week_and_rerun(get_monday_of_week(date.today()))

with col_next_week:
    if st.button("⏩ Майбутній тиждень", key="next_week_btn"):
        set_week_and_rerun(get_monday_of_week(st.session_state.start_date + timedelta(weeks=1)))

st.markdown("---")

# --- Рендеринг таблиці розкладу з можливістю редагування ---
# Тепер ми будемо використовувати Streamlit input widgets для кожної клітинки,
# щоб зміни могли бути відстежені Python і збережені в БД.

st.markdown("""
<style>
.schedule-grid-container {
    display: grid;
    grid-template-columns: 120px 80px repeat(5, 1fr); /* 5 колонок для пар */
    gap: 1px;
    font-family: 'Roboto', sans-serif;
    border: 1px solid #C0D0E0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    margin-top: 20px;
    background-color: #F8F8F8;
    max-width: 100%;
    overflow-x: auto;
}
.grid-cell {
    border: 1px solid #C0D0E0;
    background: rgba(255, 255, 255, 0.7);
    padding: 4px;
    text-align: center;
    box-sizing: border-box;
    font-size: 10px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
.header-cell {
    font-weight: bold;
    background: rgba(220, 230, 240, 0.8);
}
.top-left-header {
    background: rgba(220, 230, 240, 0.8);
    border-radius: 12px 0 0 0;
}
.pair-header-cell {
    background: rgba(180, 210, 230, 0.8);
    font-size: 16px;
}
.day-header-cell {
    background: rgba(240, 200, 100, 0.9);
    font-size: 16px;
    grid-row: span 6; /* Spans 6 rows (number of groups) */
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
}
.day-header-text {
    transform: rotate(-90deg);
    white-space: nowrap;
    transform-origin: center center;
    font-weight: bold;
}
.group-header-cell {
    background: rgba(200, 220, 240, 0.8);
    font-size: 12px;
}
/* Стилі для Streamlit TextInput, щоб вони краще виглядали в сітці */
.stTextInput > div > div > input {
    text-align: center !important;
    font-size: 9px !important;
    padding: 2px !important;
    margin: 0 !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    width: 95% !important;
}
.stTextInput > label {
    display: none !important; /* Hide default Streamlit labels for compactness */
}
</style>
<div class="schedule-grid-container">
    <div class="grid-cell top-left-header"></div>
    <div class="grid-cell header-cell">Група</div>
""", unsafe_allow_html=True)

# Pair headers
for roman, time_range in PAIRS:
    st.markdown(f'''
        <div class="grid-cell header-cell pair-header-cell">
            <div><strong>{roman} ПАРА</strong></div>
            <div style="font-size: 13px; color: #333333; line-height: 1.2;">({time_range})</div>
        </div>
    ''', unsafe_allow_html=True)

# Main content rows
# Замість одного components.html для всієї таблиці, ми будемо генерувати її за допомогою Streamlit columns
# Це дозволить нам використовувати st.text_input безпосередньо.

# Streamlit не дозволяє напряму вбудовувати віджети в HTML-рядок, який передається в st.markdown або components.html.
# Тому ми повинні використовувати вкладені st.columns для створення візуальної сітки з віджетами.

# Динамічне створення колонок для кожного дня і групи
# Спочатку, створимо заголовки днів та груп окремо, а потім петлі для даних.

# Заголовки днів та груп будуть частиною HTML, щоб вони могли використовувати grid-row-span.
# Далі ми будемо генерувати рядки з полями вводу.

# Важливо: st.columns створює новий горизонтальний блок. Нам потрібно імітувати сітку.

# Віджет Streamlit створюється послідовно. Щоб створити сітку,
# ми повинні використовувати st.columns для кожного "ряду" даних
# і потім вкладати input-поля в ці колонки.

# Це дещо відрізняється від повної HTML-сітки, де всі елементи в div.
# Через обмеження Streamlit, ми будемо будувати це по рядах.

# Для більш точної сітки зі Streamlit віджетами, потрібно створювати columns для кожного рядка даних
# (день + група + 5 пар).

for i_day, day_name in enumerate(DAYS):
    # Заголовок дня
    st.markdown(f'<div class="grid-cell day-header-cell"><span class="day-header-text">{day_name}</span></div>', unsafe_allow_html=True)

    for i_group in range(NUM_GROUPS_PER_DAY):
        # Заголовок групи
        st.markdown(f'<div class="grid-cell group-header-cell">{GROUP_NAMES[i_group]}</div>', unsafe_allow_html=True)

        # Створення колонок для пар (предметів/викладачів)
        # Кожен ряд пар буде окремим блоком Streamlit.
        cols_for_pairs = st.columns(len(PAIRS)) # Створюємо 5 колонок для 5 пар

        for i_pair in range(len(PAIRS)):
            # Отримання поточних даних для клітинки
            current_item = st.session_state.schedule_display_data.get((i_day, i_group, i_pair), {
                "teacher": "", "subject": "", "id": str(uuid.uuid4()) # Якщо немає, даємо пусті значення
            })

            with cols_for_pairs[i_pair]:
                # Вбудовуємо стілі для відступів для компактності
                st.markdown(
                    """
                    <style>
                    .stTextInput {
                        margin-bottom: 0px !important;
                        padding-bottom: 0px !important;
                    }
                    .stTextInput > div {
                        margin-bottom: 0px !important;
                    }
                    </style>
                    """, unsafe_allow_html=True
                )

                # Текстове поле для предмету
                st.session_state.schedule_display_data[(i_day, i_group, i_pair)]['subject'] = st.text_input(
                    label="Предмет", # Лейбл буде прихований CSS
                    value=current_item["subject"],
                    key=f"subject_{st.session_state.start_date.isoformat()}_{i_day}_{i_group}_{i_pair}",
                    placeholder="Предмет"
                )
                # Текстове поле для викладача
                st.session_state.schedule_display_data[(i_day, i_group, i_pair)]['teacher'] = st.text_input(
                    label="Викладач", # Лейбл буде прихований CSS
                    value=current_item["teacher"],
                    key=f"teacher_{st.session_state.start_date.isoformat()}_{i_day}_{i_group}_{i_pair}",
                    placeholder="Викладач"
                )

# Закриття основного div контейнера для сітки
st.markdown("</div>", unsafe_allow_html=True) # Закриваємо grid-container

# --- Кнопки збереження та завантаження (вже налаштовані вище) ---
# ... (решта коду з кнопками Зберегти/Завантажити PDF та функцією generate_pdf)
# --- Кнопки збереження та завантаження ---
# Ці кнопки вже були вище, але додаємо функціонал
with col_save_btn:
    if st.button("💾 Зберегти", key="save_button_action"):
        save_schedule(st.session_state.start_date, st.session_state.schedule_display_data)

# Назва файлу PDF з вибраним тижнем
pdf_file_name = f"розклад_{st.session_state.start_date.strftime('%d.%m')}–{end_date.strftime('%d.%m')}.pdf"

# Кнопка "Завантажити PDF"
with col_download_btn:
    pdf_bytes = generate_pdf(st.session_state.schedule_display_data, st.session_state.start_date, end_date, PAIRS, DAYS, GROUP_NAMES, NUM_GROUPS_PER_DAY)

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

# PDF Generation Function (unchanged, just ensure it uses correct data)
# Ця функція має бути поза основним потоком коду, що викликає віджети.
# Якщо вона була в кінці, як у попередній відповіді, то це не проблема.
# Я перемістив її на кінець файлу, щоб зберегти структуру.
def generate_pdf(schedule_data_for_pdf, start_date_pdf, end_date_pdf, pairs_pdf, days_pdf, group_names_pdf, num_groups_per_day_pdf):
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
                item = schedule_data_for_pdf.get((i_day, i_group, i_pair), {"subject": "", "teacher": ""})
                text = f"{item['subject']}\n{item['teacher']}"

                cell_start_x = pdf.get_x()
                cell_start_y = pdf.get_y()

                pdf.multi_cell(pair_col_width, content_cell_height / 2, txt=text, border=1, align="C")

                pdf.set_xy(cell_start_x + pair_col_width, cell_start_y)

        pdf.set_xy(initial_x, day_block_start_y + required_height_for_day_block)

    return pdf.output(dest='S').encode('latin1')
