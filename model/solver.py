import json
import sys
from absl import app
from typing import List, Dict
from ortools.sat.python import cp_model

from .constraints import (
    add_daily_hour_constraints,
    add_weekly_constraint,
    get_daily_hour_constraints,
    get_daily_hour_variables_for_employee,
    get_weekly_constraints_for_employee,
    get_weekly_hour_variables_for_employee,
)
from .utils import get_hours

SHIFT_HARD_MIN = 6
SHIFT_HARD_MAX = 9


def solve_shift_scheduling(
    employees: int,
    days: List[Dict],
    constraints: List[Dict],
    customer_bookings: List[tuple[int, int, int]],
):
    """Solves the shift scheduling problem."""
    model = cp_model.CpModel()

    # Linear terms of the objective in a minimization context.
    obj_int_vars = []
    obj_int_coeffs = []
    obj_bool_vars = []
    obj_bool_coeffs = []

    # Build model
    work = {}
    for e in range(employees):
        for i, d in enumerate(days):
            hours = get_hours(d)
            for h in range(hours):
                work[e, i, h] = model.NewBoolVar("work%i_%i_%i" % (e, i, h))

    # Shift constraints
    for e in range(employees):
        employee_constraints = constraints[e]
        daily_constraints = employee_constraints.get("daily")
        cts = get_daily_hour_constraints(daily_constraints, days)
        for d, day, ct in cts:
            hours = get_hours(day)
            works = get_daily_hour_variables_for_employee(work, e, d, hours)
            variables, coeffs = add_daily_hour_constraints(model, works, ct, e, d)
            obj_bool_vars.extend(variables)
            obj_bool_coeffs.extend(coeffs)

    # Booking constraints
    for booking in customer_bookings:
        d, h, bookings = booking
        workingEmployees = []
        for e in range(employees):
            workingEmployees.append(work[(e, d, h)])
        model.Add(sum(workingEmployees) >= bookings)

    # Weekly hour constraints
    for e in range(employees):
        employee_constraints = constraints[e]
        ct = get_weekly_constraints_for_employee(employee_constraints)
        totalHours = get_weekly_hour_variables_for_employee(e, days, work)
        variables, coeffs = add_weekly_constraint(model, ct, totalHours, e)
        obj_int_vars.extend(variables)
        obj_int_coeffs.extend(coeffs)

    # At least one employee works any given hour any given day
    for i, d in enumerate(days):
        hours = get_hours(d)
        for h in range(hours):
            assignments = []
            for e in range(employees):
                assignments.append(work[(e, i, h)])
            model.AddAtLeastOne(assignments)

    # No gaps in the middle of a shift
    for e in range(employees):
        for i, d in enumerate(days):
            hours = get_hours(d)
            dailyHours = []
            for h in range(hours):
                dailyHours.append(work[(e, i, h)])
            add_no_gaps_constraint(model, dailyHours)

    # Objective
    model.Minimize(
        sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars)))
        + sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars)))
    )

    # Solve the model.
    solver = cp_model.CpSolver()
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    solver.parameters.max_time_in_seconds = 5
    status = solver.Solve(model, solution_printer)

    res = dict()
    res["employees"] = []
    res["days"] = []
    solution_found = False

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        solution_found = True
        for i, d in enumerate(days):
            print("\nDAY %i" % (i + 1))
            header = "          "
            header += "8  9  10 11 12 13 14 15 16 17 18 19"
            print(header)
            workers = []
            for e in range(employees):
                schedule = ""
                hours = []
                hoursOfTheDay = get_hours(d)
                for h in range(hoursOfTheDay):
                    if solver.BooleanValue(work[(e, i, h)]):
                        schedule += "X" + "  "
                        hours.append(h)
                    else:
                        schedule += "." + "  "
                print("worker %i: %s" % (e, schedule))
                workers.append({"id": e, "hours": hours})
            res["days"].append({"id": d, "workers": workers})

        print("\n")
        for e in range(employees):
            hours = 0
            for i, d in enumerate(days):
                hoursOfTheDay = get_hours(d)
                for h in range(hoursOfTheDay):
                    if solver.BooleanValue(work[((e, i, h))]):
                        hours += 1
            print("Employee %i worked %i hours" % (e, hours))
            res["employees"].append({e: hours})

    print(solution_found)
    return (solution_found, res)


def add_no_gaps_constraint(model, vars):
    # Channeling constraints
    true_to_false = []
    for i in range(len(vars) - 1):
        true_to_false.append(model.NewBoolVar("helper%i" % i))

    model.Add(sum(true_to_false) <= 1)
    for i in range(len(vars) - 1):
        # (a and not b) => c
        model.AddBoolOr([vars[i].Not(), vars[i + 1], true_to_false[i]])
        # c => (a and not b)
        model.AddImplication(true_to_false[i], vars[i])
        model.AddImplication(true_to_false[i], vars[i + 1].Not())

    false_to_true = []
    for i in range(len(vars) - 1):
        false_to_true.append(model.NewBoolVar("helper_2%i" % i))
        model.Add(sum(false_to_true) <= 1)

    for i in range(len(vars) - 1):
        model.AddBoolOr([vars[i], vars[i + 1].Not(), false_to_true[i]])
        model.AddImplication(false_to_true[i], vars[i].Not())
        model.AddImplication(false_to_true[i], vars[i + 1])

    for i in range(len(vars) - 1):
        for j in range(i, len(vars) - 1):
            model.AddBoolAnd(
                false_to_true[i].Not(), false_to_true[j].Not()
            ).OnlyEnforceIf(true_to_false[i])

    return true_to_false, false_to_true


def main(_=None):
    employees = json.loads(sys.argv[1])
    days = json.loads(sys.argv[2])
    constraints = json.loads(sys.argv[3])
    customer_bookings = sys.argv[4]

    print("Days: " + str(days))
    customer_bookings_array = list(map(int, customer_bookings.split(",")))
    print("Bookings: " + str(customer_bookings_array))

    customer_bookings_tuple_array = [
        tuple(customer_bookings_array[i : i + 3])
        for i in range(0, len(customer_bookings_array), 3)
    ]
    print(customer_bookings_tuple_array)

    solve_shift_scheduling(employees, days, constraints, customer_bookings_tuple_array)


if __name__ == "__main__":
    app.run(main)
