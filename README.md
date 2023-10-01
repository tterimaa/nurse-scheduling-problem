# Nurse scheduling problem

# TODO LIST

- Debug the model by printing unsatisfied constraints
- Design new API interface
- If "weekly" constraint setting exist for employee, use that and assume all values exist to simplify constraints
- Offset constraint for starting the day later 

# How to run (macos)

### Install dependencies

```
python3 -m pip install -r requirements.txt
```

### Run API
```
python3 -m api.routes
```

### Run tests

python3 -m unittest **tests**/test.py

# Resources
or-tools docs: https://developers.google.com/optimization
or-tools examples: https://github.com/google/or-tools/tree/master/examples/python

