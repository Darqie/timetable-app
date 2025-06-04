import streamlit as st
import streamlit.components.v1 as components
import uuid

st.set_page_config(page_title="Розклад уроків", layout="wide")

st.markdown("<h2 style='text-align: center;'>Розклад уроків</h2>", unsafe_allow_html=True)

days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
lessons = [f"Урок {i}" for i in range(1, 6)]

# Статичні приклади даних (для заповнення таблиці)
schedule_data = {}
for i in range(5):
    for j in range(5):
        schedule_data[(i, j)] = {
            "teacher": f"Викладач {i+1}",
            "group": f"Група {chr(65 + j)}",
            "subject": f"Предмет {j+1}",
            "id": str(uuid.uuid4())
        }

# HTML з CSS і JavaScript
html_code = """
<style>
.timetable {
    display: grid;
    grid-template-columns: 100px repeat(5, 1fr);
    grid-auto-rows: 100px;
    gap: 2px;
    font-family: Arial, sans-serif;
}
.cell {
    border: 1px solid #ccc;
    background: #fff;
    position: relative;
    padding: 5px;
}
.cell-header {
    background: #f0f0f0;
    font-weight: bold;
    display: flex;
    justify-content: center;
    align-items: center;
}
.draggable {
