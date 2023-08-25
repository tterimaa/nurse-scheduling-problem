# Nurse scheduling problem

# TODO LIST

- If "weekly" constraint setting exist for employee, use that and assume all values exist to simplify constraints
- Offset constraint for starting the day later 
- More granular scheduling

# How to run (macos)

### Install dependencies

```
python3 -m pip install -r requirements.txt
```

### Run shift_scheduling.py from command line

```
python3 api/shift_scheduling.py 3 "[{\"hours\": 12, \"minutes\": 30, \"shift_constraints\": [{\"max_hours\": 6, \"employee\": 1}]},{\"hours\": 12, \"minutes\": 30},{\"hours\": 12, \"minutes\": 30},{\"hours\": 12, \"minutes\": 30},{\"hours\": 12, \"minutes\": 30},{\"hours\": 6, \"minutes\": 0}]" "{\"weekly\": [{},{\"hard_max\": 18},{\"hard_max\": 18}]}" 0,0,1
```

### Run API and use UI

```
python3 routes.py
```

Open ui/index.html

# CLI parameters

shift_scheduling.py takes three parameters

1. num_employees (int) - the number of employees
2. days (List[dict[str, int]]) - list of days and how many hours each day has e.g. [{"hours": 20, minutes: 30},{"hours": 15, minutes: 30}]
3. num_hours (int) - the number of hours per day
4. customer_bookings (list of tuples) - the customer bookings

- Customer bookings is a list of integers. List must be divisable by three: booking entry consist of three numbers: day, hour and number of bookings on a given hour

### Run tests

python3 -m unittest **tests**/test.py
