
const form = document.querySelector('form');
form.addEventListener('submit', handleSubmit);

async function handleSubmit(event) {
  event.preventDefault();

  // Clear previous results
  const resultsDiv = document.querySelector('#results');
  resultsDiv.innerHTML = '';

  resultsDiv.innerHTML += '<p>Loading...</p>';

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

    // Remove Juha Mieto's image and favorite food after the response is received
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

