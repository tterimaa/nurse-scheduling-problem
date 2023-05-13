# Nurse scheduling problem starter template

Copied from: https://developers.google.com/optimization/scheduling/employee_scheduling

# TODO LIST
- Assigning a nurse to a booking
- Vacation days
- Availability
- Part-time employees

# BUGS
- customer_bookings = [(0,0,3)] currently leaves empty hour for for worker 2 on day 1. (emplyoees: 3, days: 5, hours: 12)
  - Not actually bug but a 'feature'. Having first 3 hours work, one hour break and then rest of the day work does not violate the model if minimum number of
  continous hours is 3
  - We need a rule that prevents splitted days?

# How to run (macos)
```
python3 -m pip install ortools
python3 -m pip install absl-py
python3 shift_scheduling.py 4 5 12 0,0,3,1,4,2,3,1,2
```

# CLI parameters
shift_scheduling.py takes three parameters
1. num_employees (int) - the number of employees
2. num_days (int) - the number of days
3. num_hours (int) - the number of hours per day
4. customer_bookings (list of tuples) - the customer bookings
  - Customer bookings is a list of integers. List must be divisable by three: booking entry consist of three numbers: day, hour and number of bookings on a given hour 

