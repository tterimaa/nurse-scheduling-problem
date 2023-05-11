const form = document.querySelector('form');
form.addEventListener('submit', handleSubmit);
const tableContainerId = "table-container"

window.onload = function() {
  checkCondition();
  generateTable();
}

function isFieldsFilled() {
  var num_employees = document.getElementById("num-employees");
  var num_days = document.getElementById("num-days");
  var num_hours = document.getElementById("num-hours");
  return num_employees.value !== "" && num_days.value !== "" && num_hours.value !== "";
}

// Check if forms basic fields have values first
function checkCondition() {
  var conditionalInput = document.querySelectorAll('.conditional');
  if (isFieldsFilled()) {
    conditionalInput.forEach(function (element) {
      element.classList.remove("hidden");
    });
    generateTable();
  } else {
    conditionalInput.forEach(function (element) {
      element.classList.add("hidden");
    });
    destroyTable();
  }
}

// When basic fields have values, the table input should be displayed
function generateTable() {
    if (!isFieldsFilled()) return;

    var numDays = parseInt(document.getElementById("num-days").value);
    var numHours = parseInt(document.getElementById("num-hours").value);
    var tableContainer = document.getElementById(tableContainerId);

    var tableHTML = '<table>';

    for (var i = 0; i < numDays + 1; i++) {
        tableHTML += '<tr>';

        for (var j = 0; j < numHours + 1; j++) {
            if (i === 0 && j === 0) {
                tableHTML += '<td></td>'; // Empty cell at the top-left corner
            } else if (i === 0) {
                tableHTML += '<td>' + j + '</td>'; // Column headers
            } else if (j === 0) {
                tableHTML += '<td>' + i + '</td>'; // Row headers
            } else {
                tableHTML += '<td><input type="number" data-row="' + i + '" data-col="' + j + '"></td>'; // Input fields
            }
        }

        tableHTML += '</tr>';
    }

    tableHTML += '</table>';

    tableContainer.innerHTML = tableHTML;
}

function destroyTable() {
  var tableContainer = document.getElementById(tableContainerId);
  tableContainer.innerHTML = "";
}

// Handle form submit
async function handleSubmit(event) {
  event.preventDefault();

  // Clear previous results
  const resultsDiv = document.querySelector('#results');
  resultsDiv.innerHTML = '';

  // Show loader animation
  const juhaMietoImg = document.createElement('img');
  juhaMietoImg.classList.add('mietaa');
  juhaMietoImg.src = '../mietaa.jpg';
  juhaMietoImg.alt = 'Juha Mieto';
  juhaMietoImg.classList.add('loadingImage');
  resultsDiv.appendChild(juhaMietoImg);

  // Get form values
  const numEmployeesInput = document.querySelector('#num-employees');
  const numDaysInput = document.querySelector('#num-days');
  const numHoursInput = document.querySelector('#num-hours');
  const numEmployees = parseInt(numEmployeesInput.value);
  const numDays = parseInt(numDaysInput.value);
  const numHours = parseInt(numHoursInput.value);

  // Validate form values
  if (!Number.isInteger(numEmployees) || numEmployees <= 0) {
    alert('Number of employees must be a positive integer');
    return;
  }
  if (!Number.isInteger(numDays) || numDays <= 0) {
    alert('Number of days must be a positive integer');
    return;
  }
  if (!Number.isInteger(numHours) || numHours <= 0) {
    alert('Number of hours must be a positive integer');
    return;
  }

  // Fetch data
  try {
    const response = await fetch('http://localhost:5000/endpoint', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ num_employees: numEmployees, num_days: numDays, num_hours: numHours }),
    });
    const data = await response.json();

    resultsDiv.innerHTML = '';

    // Display days and grids
    const gridColors = ['gray', 'red', 'blue', 'green', 'yellow', 'purple'];
    data.res.days.forEach(day => {
      const dayHeader = document.createElement('h2');
      dayHeader.textContent = `Day ${day.id}`;
      resultsDiv.appendChild(dayHeader);

      const dayGrid = document.createElement('table');
      dayGrid.classList.add('grid');
      const headerRow = document.createElement('tr');
      const idHeaderCell = document.createElement('th');
      idHeaderCell.textContent = 'ID';
      headerRow.appendChild(idHeaderCell);
      for (let h = 0; h < numHours; h++) {
        const headerCell = document.createElement('th');
        headerCell.textContent = `Hour ${h}`;
        headerRow.appendChild(headerCell);
      }
      dayGrid.appendChild(headerRow);

      day.workers.forEach(worker => {
        const workerRow = document.createElement('tr');
        const idCell = document.createElement('td');
        idCell.textContent = `Worker ${worker.id}`;
        workerRow.appendChild(idCell);
        for (let h = 0; h < numHours; h++) {
          const cell = document.createElement('td');
          if (worker.hours.includes(h)) {
            cell.style.backgroundColor = gridColors[worker.id % gridColors.length];
          } else {
            cell.style.backgroundColor = 'white';
          }
          workerRow.appendChild(cell);
        }
        dayGrid.appendChild(workerRow);
      });

      resultsDiv.appendChild(dayGrid);
    });
  } catch (error) {
    console.error(error);
  }
}

