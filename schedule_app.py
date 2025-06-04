import streamlit as st
import uuid

st.set_page_config(page_title="Розклад уроків", layout="wide")

st.markdown("<h2 style='text-align: center;'>Розклад уроків</h2>", unsafe_allow_html=True)

days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
lessons = [f"Урок {i}" for i in range(1, 6)]

# Початкові дані
schedule_data = {
    (i, j): {
        "teacher": f"Викладач {i+1}-{j+1}",
        "group": f"Група {chr(65 + j)}",
        "subject": f"Предмет {i+1}",
        "id": str(uuid.uuid4())
    }
    for i in range(5) for j in range(5)
}

# CSS стилі
st.markdown("""
<style>
    .timetable {
        display: grid;
        grid-template-columns: 100px repeat(5, 1fr);
        grid-auto-rows: 100px;
        gap: 2px;
        margin-top: 20px;
    }
    .cell {
        border: 1px solid #ccc;
        background: #f9f9f9;
        position: relative;
    }
    .cell-header {
        background: #efefef;
        font-weight: bold;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .draggable {
        background: #d4e0ff;
        padding: 4px;
        margin: 4px;
        border-radius: 5px;
        cursor: move;
        user-select: none;
    }
</style>
""", unsafe_allow_html=True)

# HTML + JavaScript для drag-and-drop
html_code = '<div class="timetable">'
html_code += '<div class="cell cell-header"></div>'  # верхній лівий кут

# Заголовки днів
for day in days:
    html_code += f'<div class="cell cell-header">{day}</div>'

# Створення таблиці з drag-and-drop
for i, lesson in enumerate(lessons):
    html_code += f'<div class="cell cell-header">{lesson}</div>'
    for j, day in enumerate(days):
        item = schedule_data[(i, j)]
        item_id = item["id"]
        html_code += f'''
        <div class="cell" ondrop="drop(event)" ondragover="allowDrop(event)">
            <div id="{item_id}" class="draggable" draggable="true" ondragstart="drag(event)">
                <strong>{item["subject"]}</strong><br>
                {item["teacher"]}<br>
                {item["group"]}
            </div>
        </div>
        '''

html_code += '</div>'

# JavaScript логіка
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
  var draggedElement = document.getElementById(data);
  if (ev.target.classList.contains('cell')) {
      ev.target.appendChild(draggedElement);
  } else if (ev.target.classList.contains('draggable')) {
      ev.target.parentNode.appendChild(draggedElement);
  }
}
</script>
"""

st.components.v1.html(html_code, height=700, scrolling=True)

