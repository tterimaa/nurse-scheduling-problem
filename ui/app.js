const form = document.querySelector("form");
form.addEventListener("submit", handleSubmit);
const tableContainerId = "table-container";

window.onload = function () {
  addEmployeeInfoInputs();
  addCustomerBookingInputs();
};

function addEmployeeInfoInputs() {
  var num_employees = parseInt(document.getElementById("num-employees").value);
  var employees_info_list = document.getElementById("employees-info-list");
  if (num_employees > 0) {
    employees_info_list.classList.remove("hidden");
    var currentList = employees_info_list.querySelectorAll("input").length;
    var diff = num_employees - currentList;
    if (diff > 0) {
      for (var i = currentList; i < num_employees; i++) {
        var li = document.createElement("li");
        var fieldset = document.createElement("fieldset");
        var legend = document.createElement("legend");
        legend.textContent = "Employee " + (i + 1) + " information";
        var label = document.createElement("label");
        var input = document.createElement("input");
        label.setAttribute("for", "employee-name" + i);
        label.textContent = "Name";
        input.setAttribute("type", "string");
        input.setAttribute("id", "employee-name" + i);
        fieldset.appendChild(legend);
        fieldset.appendChild(label);
        fieldset.appendChild(input);
        li.appendChild(fieldset);
        employees_info_list.appendChild(li);
      }
    } else {
      var currentList = employees_info_list.querySelectorAll("li");
      for (var i = currentList.length; i > num_employees; i--) {
        var last = currentList[i - 1];
        employees_info_list.removeChild(last);
      }
    }
  } else {
    employees_info_list.classList.add("hidden");
  }
}

function addCustomerBookingInputs() {
  var num_bookings = parseInt(document.getElementById("num-bookings").value);
  var customer_bookings_list = document.getElementById(
    "customer-bookings-list",
  );
  if (num_bookings > 0) {
    customer_bookings_list.classList.remove("hidden");
    var currentList =
      customer_bookings_list.querySelectorAll("fieldset").length;
    var diff = num_bookings - currentList;
    if (diff > 0) {
      for (var i = currentList; i < num_bookings; i++) {
        var li = document.createElement("li");
        var fieldset = document.createElement("fieldset");
        var legend = document.createElement("legend");
        legend.textContent = "Booking " + (i + 1);
        var labelDay = document.createElement("label");
        var inputDay = document.createElement("input");
        labelDay.setAttribute("for", "day-of-booking" + i);
        labelDay.textContent = "Day";
        inputDay.setAttribute("type", "number");
        inputDay.setAttribute("id", "day-of-booking" + i);
        var labelHour = document.createElement("label");
        var inputHour = document.createElement("input");
        labelHour.setAttribute("for", "booking-hour" + i);
        labelHour.textContent = "Start hour";
        inputHour.setAttribute("type", "number");
        inputHour.setAttribute("id", "booking-hour" + i);
        var labelBookings = document.createElement("label");
        var inputBookings = document.createElement("input");
        labelBookings.setAttribute("for", "number-of-bookings" + i);
        labelBookings.textContent = "Number of bookings on the hour";
        inputBookings.setAttribute("type", "number");
        inputBookings.setAttribute("id", "number-of-bookings" + i);
        fieldset.appendChild(legend);
        fieldset.appendChild(labelDay);
        fieldset.appendChild(inputDay);
        fieldset.appendChild(labelHour);
        fieldset.appendChild(inputHour);
        fieldset.appendChild(labelBookings);
        fieldset.appendChild(inputBookings);
        li.appendChild(fieldset);
        customer_bookings_list.appendChild(li);
      }
    } else {
      var currentList = customer_bookings_list.querySelectorAll("li");
      for (var i = currentList.length; i > num_bookings; i--) {
        var last = currentList[i - 1];
        customer_bookings_list.removeChild(last);
      }
    }
  } else {
    customer_bookings_list.classList.add("hidden");
  }
}

// Handle form submit
async function handleSubmit(event) {
  event.preventDefault();

  // Clear previous results
  const resultsDiv = document.querySelector("#results");
  resultsDiv.innerHTML = "";

  // Get form values
  const numEmployees = parseInt(document.querySelector("#num-employees").value);
  const numDays = getNumDays();
  const numHours = getNumHours();

  if (!numDays || !numHours) {
    return;
  }

  // Get customer bookings
  var customer_bookings_list = document.getElementById(
    "customer-bookings-list",
  );
  var customer_bookings_inputs =
    customer_bookings_list.querySelectorAll("input");
  var customer_booking_input_values = Array.from(customer_bookings_inputs).map(
    (b) => parseInt(b.value),
  );
  const isSomeBookingInvalid = customer_booking_input_values.some((b) => b < 0);
  if (isSomeBookingInvalid) {
    alert("Bookings values must be positive integers");
    return;
  }
  if (customer_booking_input_values.length % 3 !== 0) {
    alert("Number of bookings must be divisable by three");
    return;
  }
  var customerBookings = [];
  var i = 0;
  while (i < customer_booking_input_values.length) {
    const booking = {
      day: customer_booking_input_values[i],
      hour: customer_booking_input_values[i + 1],
      bookings: customer_booking_input_values[i + 2],
    };
    customerBookings.push(booking);
    i = i + 3;
  }

  // Validate form values
  if (!Number.isInteger(numEmployees) || numEmployees <= 0) {
    alert("Number of employees must be a positive integer");
    return;
  }
  if (!Number.isInteger(numHours) || numHours <= 0) {
    alert("Number of hours must be a positive integer");
    return;
  }

  // Show loader animation
  const juhaMietoImg = document.createElement("img");
  juhaMietoImg.classList.add("mietaa");
  juhaMietoImg.src = "../mietaa.jpg";
  juhaMietoImg.alt = "Juha Mieto";
  juhaMietoImg.classList.add("loadingImage");
  resultsDiv.appendChild(juhaMietoImg);

  // Fetch data
  try {
    const response = await fetch("http://localhost:5000/endpoint", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        num_employees: numEmployees,
        num_days: numDays,
        num_hours: numHours,
        customer_bookings: customerBookings,
      }),
    });
    const data = await response.json();

    resultsDiv.innerHTML = "";

    // Display days and grids
    const gridColors = ["gray", "red", "blue", "green", "yellow", "purple"];
    data.res.days.forEach((day) => {
      const dayHeader = document.createElement("h2");
      dayHeader.textContent = `Day ${day.id}`;
      resultsDiv.appendChild(dayHeader);

      const dayGrid = document.createElement("table");
      dayGrid.classList.add("grid");
      const headerRow = document.createElement("tr");
      const idHeaderCell = document.createElement("th");
      idHeaderCell.textContent = "ID";
      headerRow.appendChild(idHeaderCell);
      for (let h = 0; h < numHours; h++) {
        const headerCell = document.createElement("th");
        headerCell.textContent = getHour(h);
        headerRow.appendChild(headerCell);
      }
      dayGrid.appendChild(headerRow);

      day.workers.forEach((worker) => {
        const workerRow = document.createElement("tr");
        const idCell = document.createElement("td");
        idCell.textContent = getEmployeeName(worker.id);
        workerRow.appendChild(idCell);
        for (let h = 0; h < numHours; h++) {
          const cell = document.createElement("td");
          if (worker.hours.includes(h)) {
            cell.style.backgroundColor =
              gridColors[worker.id % gridColors.length];
          } else {
            cell.style.backgroundColor = "white";
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

function getEmployeeName(id) {
  const name = document.getElementById("employee-name" + id).value;
  if (!name) {
    console.error("name not found");
    return "";
  }
  return name;
}

function getHour(id) {
  const hour = document.getElementById("from-hour").querySelectorAll("option");
  const startHour = document
    .getElementById("from-hour")
    .querySelector("[selected]");
  if (!startHour || !startHour.value) {
    console.error("start hour not found");
    return "";
  }
  if (!hour || !hour[id]) {
    console.error("hour not found");
    return "";
  }
  const index = parseInt(hour[id].value) + parseInt(startHour.value);
  if (!hour[index] || !hour[index].textContent) {
    console.error("problem fetching text for the correct hour");
    return "";
  }
  return hour[index].textContent;
}

function getNumDays() {
  const from = parseInt(document.getElementById("from-day").value);
  const to = parseInt(document.getElementById("to-day").value);
  const num = to - from;
  if (!num || num <= 0) {
    alert("Error in opening hours: from date must be before to date");
    return false;
  }
  return num;
}

function getNumHours() {
  const from = parseInt(document.getElementById("from-hour").value);
  const to = parseInt(document.getElementById("to-hour").value);
  const num = to - from;
  if (!num || num <= 0) {
    alert("Error in opening hours: from hour must be less than to hour");
    return false;
  }
  return num;
}
