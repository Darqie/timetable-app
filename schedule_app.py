import streamlit as st
import streamlit.components.v1 as components
import uuid

st.set_page_config(page_title="Розклад пар", layout="wide")
st.markdown("<h2 style='text-align: center;'>Розклад пар</h2>", unsafe_allow_html=True)

days = ["Понеділок", "Вівторок", "Середа", "Четвер", "П’ятниця"]
pairs = [f"Пара {i}" for i in range(1, 6)]

schedule_data = {}
for i in range(5):
    for j in range(5):
        schedule_data[(i, j)] = {
            "teacher": f"Викладач {i+1}",
            "group": f"Група {chr(65 + j)}",
            "subject": f"Предмет {j+1}",
            "id": str(uuid.uuid4())
        }

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

# Пари
for i, pair in enumerate(pairs):
    html_code += f'<div class="cell cell-header">{pair}</div>'
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

html_code += """
</div>

<script>
function allowDrop(ev) {
  ev.preventDefault();
}

function drag(ev) {
  ev.dataTransfer.setData("text/plain", ev.target.id);
}

function drop(ev) {
  ev.preventDefault();
  var draggedId = ev.dataTransfer.getData("text");
  var draggedElem = document.getElementById(draggedId);

  var dropTarget = ev.target;

  // Знайти найближчий .cell, якщо клікнули не на саму клітинку
  while (!dropTarget.classList.contains("cell")) {
    dropTarget = dropTarget.parentNode;
    if (!dropTarget) return;
  }

  // Якщо в цільовій клітинці вже є елемент — поміняти місцями
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

components.html(html_code, height=800, scrolling=True)
