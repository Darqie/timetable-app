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
NUM_GROUPS_PER_DAY = 6 

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
                "group": GROUP_NAMES[row['group_index']], 
                "subject": row['subject'],
                "id": row['item_id']
            }
        st.info(f"Розклад для тижня {week_start_date.strftime('%d.%m.%Y')} завантажено.")
    else:
        st.warning(f"Розклад для тижня {week_start_date.strftime('%d.%m.%Y')} не знайдено в базі даних. Створюється шаблонний розклад.")
        for i_day in range(len(DAYS)):
            for i_group in range(NUM_GROUPS_PER_DAY): 
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
    st.session_state.start_date = MONDAY_INITIAL_DATE 

if 'schedule_display_data' not in st.session_state:
    st.session_state.schedule_display_data = load_schedule(st.session_state.start_date)

# --- Функції для навігації по тижнях ---
def get_monday_of_week(target_date):
    days_since_monday = target_date.weekday()
    return target_date - timedelta(days=days_since_monday)

def set_week_and_rerun(new_start_date):
    st.session_state.start_date = new_start_date
    st.session_state.schedule_display_data = load_schedule(new_start_date) 
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
    saved_weeks_formatted = {wk.strftime('%d.%m.%Y'): wk for wk in saved_weeks}
    
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

# --- CSS для імітації таблиці за допомогою Streamlit columns ---
# Цей CSS буде застосовуватися до st.markdown елементів, що є "клітинками"
st.markdown("""
<style>
/* Загальний контейнер для таблиці */
.table-container {
    border: 1px solid #C0D0E0;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    background-color: #F8F8F8;
    margin-top: 20px;
}
/* Стилі для всіх "клітинок" заголовків та даних */
.cell-style {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 4px;
    box-sizing: border-box;
    min-height: 60px; /* Стандартна висота для комірок */
    border-right: 1px solid #E0E0E0;
    border-bottom: 1px solid #E0E0E0;
    text-align: center;
    overflow: hidden; /* Обрізати вміст, якщо він занадто великий */
}
/* Заголовки верхнього ряду */
.header-cell-top {
    background: rgba(220, 230, 240, 0.8);
    font-weight: bold;
}
/* Заголовки пар */
.pair-header-cell {
    background: rgba(180, 210, 230, 0.8);
    font-size: 16px;
}
/* Заголовки днів */
.day-header-cell {
    background: rgba(240, 200, 100, 0.9);
    font-size: 16px;
    writing-mode: vertical-rl;
    text-orientation: mixed;
    font-weight: bold;
    min-width: 120px; /* Фіксована ширина для колонки дня */
}
/* Заголовки груп */
.group-header-cell {
    background: rgba(200, 220, 240, 0.8);
    font-size: 12px;
    min-width: 80px; /* Фіксована ширина для колонки групи */
}

/* Прибираємо праву межу для останньої колонки в кожному логічному рядку */
.no-right-border {
    border-right: none !important;
}
/* Прибираємо нижню межу для останнього логічного дня (всіх його клітинок) */
.no-bottom-border {
    border-bottom: none !important;
}

/* Налаштування Streamlit TextInput для компактності */
.stTextInput > div > div > input {
    text-align: center !important;
    font-size: 9px !important;
    padding: 2px !important;
    margin: 0 !important;
    border: 1px solid #ddd !important;
    border-radius: 4px !important;
    width: 95% !important;
    line-height: 1.2 !important; /* Для кращого відображення двох рядків тексту */
}
.stTextInput > label {
    display: none !important; /* Hide default Streamlit labels for compactness */
}
/* Щоб прибрати стандартні відступи Streamlit навколо колонок */
div[data-testid="column"] {
    padding: 0px !important;
    margin: 0px !important;
    display: flex; /* Важливо для вирівнювання вмісту всередині колонки */
    flex-direction: column;
    justify-content: flex-start;
    align-items: stretch;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='table-container'>", unsafe_allow_html=True)

# --- Верхній ряд заголовків: Порожній кут, Заголовок "Група", Заголовки Пар ---
# Розраховуємо ширини колонок для верхнього ряду
# 120px для порожньої комірки, 80px для "Групи", і решта порівну для пар
# Ваги колонок: [фіксована ширина, фіксована ширина] + [відносна вага для кожної пари]
# Загальна ширина вікна Streamlit є гнучкою, тому ми використовуємо комбінацію фіксованих пікселів і відносних ваг.
# Streamlit буде намагатися пропорційно розподілити решту простору.
col_weights_header = [120, 80] + [1 for _ in PAIRS] # 120px, 80px, а потім 5 рівних частин
header_cols = st.columns(col_weights_header)

with header_cols[0]:
    # Верхній лівий кут таблиці
    st.markdown("<div class='cell-style header-cell-top' style='border-top-left-radius: 12px;'></div>", unsafe_allow_html=True)
with header_cols[1]:
    # Заголовок "Група"
    st.markdown("<div class='cell-style header-cell-top group-header-cell'>Група</div>", unsafe_allow_html=True)
for i, (roman, time_range) in enumerate(PAIRS):
    with header_cols[i + 2]: # +2 тому що перші дві колонки вже зайняті
        right_border_class = "no-right-border" if i == len(PAIRS) - 1 else ""
        border_radius_style = "border-top-right-radius: 12px;" if i == len(PAIRS) - 1 else ""
        st.markdown(f'''
            <div class="cell-style header-cell-top pair-header-cell {right_border_class}" style="{border_radius_style}">
                <div><strong>{roman} ПАРА</strong></div>
                <div style="font-size: 13px; color: #333333; line-height: 1.2;">({time_range})</div>
            </div>
        ''', unsafe_allow_html=True)

# --- Основний вміст таблиці: Дні, Групи, Поля вводу ---
# Для кожного дня створюємо один "головний ряд" Streamlit
# Цей ряд буде складатися з двох колонок:
# 1. Заголовок дня (розтягується вертикально)
# 2. Контейнер для всіх груп та їхніх полів вводу для цього дня
for i_day, day_name in enumerate(DAYS):
    is_last_day = (i_day == len(DAYS) - 1)

    # Розраховуємо загальну висоту для заголовка дня, щоб він розтягувався на всі групи
    # Кожна клітинка має min-height 60px
    day_header_height = NUM_GROUPS_PER_DAY * 60

    # Створюємо головні колонки для дня
    # 120 - це ширина для заголовка дня.
    # Їхня сума повинна відповідати загальній кількості колонок, які будуть вкладені.
    # [120, 80 + 5* (відносна ширина)] = [120, 80 + 5]
    day_main_cols = st.columns([120, 80 + len(PAIRS)]) # 120px для дня, решта - сума ваг груп та пар

    with day_main_cols[0]: # Колонка для заголовка дня
        bottom_border_class = "no-bottom-border" if is_last_day else ""
        border_radius_style = "border-bottom-left-radius: 12px;" if is_last_day else ""
        st.markdown(f"""
            <div class="cell-style day-header-cell {bottom_border_class}" style="min-height: {day_header_height}px; {border_radius_style}">
                {day_name}
            </div>
        """, unsafe_allow_html=True)

    with day_main_cols[1]: # Колонка для всіх груп і їхніх пар
        # Всередині цієї колонки ми створюємо рядки для кожної групи
        for i_group in range(NUM_GROUPS_PER_DAY):
            # Перевіряємо, чи це остання група в останньому дні, щоб прибрати нижню рамку
            is_last_row_overall = is_last_day and (i_group == NUM_GROUPS_PER_DAY - 1)
            bottom_border_class_for_data = "no-bottom-border" if is_last_row_overall else ""

            # Створюємо колонки для заголовка групи та 5 пар для цього конкретного ряду
            # [80] для групи, і [1 for _ in PAIRS] для 5 пар
            group_and_pairs_cols = st.columns([80] + [1 for _ in PAIRS])

            with group_and_pairs_cols[0]: # Колонка для заголовка групи
                # Тут вже є рамка справа і знизу
                st.markdown(f"<div class='cell-style group-header-cell {bottom_border_class_for_data}'>{GROUP_NAMES[i_group]}</div>", unsafe_allow_html=True)
            
            for i_pair in range(len(PAIRS)):
                with group_and_pairs_cols[i_pair + 1]: # Колонка для полів вводу пари
                    right_border_class = "no-right-border" if i_pair == len(PAIRS) - 1 else ""
                    
                    current_item = st.session_state.schedule_display_data.get((i_day, i_group, i_pair), {
                        "teacher": "", "subject": "", "id": str(uuid.uuid4())
                    })
                    
                    st.markdown(f"<div class='cell-style {right_border_class} {bottom_border_class_for_data}'>", unsafe_allow_html=True)
                    st.session_state.schedule_display_data[(i_day, i_group, i_pair)]['subject'] = st.text_input(
                        label="Предмет", 
                        value=current_item["subject"],
                        key=f"subject_{st.session_state.start_date.isoformat()}_{i_day}_{i_group}_{i_pair}", 
                        placeholder="Предмет"
                    )
                    st.session_state.schedule_display_data[(i_day, i_group, i_pair)]['teacher'] = st.text_input(
                        label="Викладач", 
                        value=current_item["teacher"],
                        key=f"teacher_{st.session_state.start_date.isoformat()}_{i_day}_{i_group}_{i_pair}", 
                        placeholder="Викладач"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True) # Закриття table-container


# --- Кнопки збереження та завантаження ---
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
