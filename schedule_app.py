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
    background: #d0e7ff;
    border-radius: 5px;
    padding: 6px;
    margin-top: 5px;
    cursor: grab;
    box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
}
</style>

<div class="timetable">
    <div class="cell cell-header"></div>
"""

# Заголовки днів
for day in days:
    html_code += f'<div class="cell cell-header">{day}</div>'

# Рядки з уроками
for i, lesson in enumerate(lessons):
    html_code += f'<div class="cell cell-header">{lesson}</div>'
    for j, day in enumerate(days):
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

html_code += "</div>"

# JavaScript
html_code += """
<script>
function allowDrop(ev) {
  ev.preventDefault();
}
function drag(ev) {
  ev.dataTransfer.setData("text", ev.target.id);
}
function drop(ev) {
  ev.preventDefault();
  var data = ev.dataTransfer.getData("text");
  var element = document.getElementById(data);
  if (ev.target.classList.contains("cell")) {
    ev.target.appendChild(element);
  } else if (ev.target.classList.contains("draggable")) {
    ev.target.parentNode.appendChild(element);
  }
}
</script>
"""

# Вивід у Streamlit
components.html(html_code, height=800, scrolling=True)
