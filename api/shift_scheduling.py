from absl import app
from typing import List, Literal, Dict
import sys
import json
import pdb

from ortools.sat.python import cp_model


def negated_bounded_span(works, start, length):
    """Filters an isolated sub-sequence of variables assined to True.
    Extract the span of Boolean variables [start, start + length), negate them,
    and if there is variables to the left/right of this span, surround the span by
    them in non negated form.
    Args:
      works: a list of variables to extract the span from.
      start: the start to the span.
      length: the length of the span.
    Returns:
      a list of variables which conjunction will be false if the sub-list is
      assigned to True, and correctly bounded by variables assigned to False,
      or by the start or end of works.
    """
    sequence = []
    # Left border (start of works, or works[start - 1])
    if start > 0:
        sequence.append(works[start - 1])
    for i in range(length):
        sequence.append(works[start + i].Not())
    # Right border (end of works or works[start + length])
    if start + length < len(works):
        sequence.append(works[start + length])
    return sequence


def add_soft_sequence_constraint(
    model, works, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost, prefix
):
    """Sequence constraint on true variables with soft and hard bounds.
    This constraint look at every maximal contiguous sequence of variables
    assigned to true. If forbids sequence of length < hard_min or > hard_max.
    Then it creates penalty terms if the length is < soft_min or > soft_max.
    Args:
      model: the sequence constraint is built on this model.
      works: a list of Boolean variables.
      hard_min: any sequence of true variables must have a length of at least
        hard_min.
      hard_max: any sequence of true variables must have a length of at most
        hard_max.
    Returns:
      a tuple (variables_list, coefficient_list) containing the different
      penalties created by the sequence constraint.
    """
    cost_literals = []
    cost_coefficients = []

    # Forbid sequences that are too short.
    for length in range(1, hard_min):
        for start in range(len(works) - length + 1):
            model.AddBoolOr(negated_bounded_span(works, start, length))

    # Penalize sequences that are below the soft limit.
    if min_cost > 0:
        for length in range(hard_min, soft_min):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ": under_span(start=%i, length=%i)" % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # We filter exactly the sequence with a short length.
                # The penalty is proportional to the delta with soft_min.
                cost_coefficients.append(min_cost * (soft_min - length))

    # Penalize sequences that are above the soft limit.
    if max_cost > 0:
        for length in range(soft_max + 1, hard_max + 1):
            for start in range(len(works) - length + 1):
                span = negated_bounded_span(works, start, length)
                name = ": over_span(start=%i, length=%i)" % (start, length)
                lit = model.NewBoolVar(prefix + name)
                span.append(lit)
                model.AddBoolOr(span)
                cost_literals.append(lit)
                # Cost paid is max_cost * excess length.
                cost_coefficients.append(max_cost * (length - soft_max))

    # Just forbid any sequence of true variables with length hard_max + 1
    for start in range(len(works) - hard_max):
        model.AddBoolOr([works[i].Not() for i in range(start, start + hard_max + 1)])

    return cost_literals, cost_coefficients


def add_soft_sum_constraint(
    model, works, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost, prefix
):
    """Sum constraint with soft and hard bounds.
    This constraint counts the variables assigned to true from works.
    If forbids sum < hard_min or > hard_max.
    Then it creates penalty terms if the sum is < soft_min or > soft_max.
    Args:
      model: the sequence constraint is built on this model.
      works: a list of Boolean variables.
      hard_min: any sequence of true variables must have a sum of at least
        hard_min.
      soft_min: any sequence should have a sum of at least soft_min, or a linear
        penalty on the delta will be added to the objective.
      min_cost: the coefficient of the linear penalty if the sum is less than
        soft_min.
      soft_max: any sequence should have a sum of at most soft_max, or a linear
        penalty on the delta will be added to the objective.
      hard_max: any sequence of true variables must have a sum of at most
        hard_max.
      max_cost: the coefficient of the linear penalty if the sum is more than
        soft_max.
      prefix: a base name for penalty variables.
    Returns:
      a tuple (variables_list, coefficient_list) containing the different
      penalties created by the sequence constraint.
    """
    cost_variables = []
    cost_coefficients = []
    sum_var = model.NewIntVar(hard_min, hard_max, "")
    # This adds the hard constraints on the sum.
    model.Add(sum_var == sum(works))

    # Penalize sums below the soft_min target.
    if soft_min > hard_min and min_cost > 0:
        delta = model.NewIntVar(-len(works), len(works), "")
        model.Add(delta == soft_min - sum_var)
        # TODO(user): Compare efficiency with only excess >= soft_min - sum_var.
        excess = model.NewIntVar(0, 7, prefix + ": under_sum")
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(min_cost)

    #  # Penalize sums above the soft_max target.
    if soft_max < hard_max and max_cost > 0:
        delta = model.NewIntVar(-len(works), len(works), "")
        model.Add(delta == sum_var - soft_max)
        excess = model.NewIntVar(0, 7, prefix + ": over_sum")
        model.AddMaxEquality(excess, [delta, 0])
        cost_variables.append(excess)
        cost_coefficients.append(max_cost)

    return cost_variables, cost_coefficients


DaysKey = Literal["hours", "minutes"]
Days = List[Dict[DaysKey, int]]


def solve_shift_scheduling(
    num_employees: int,
    days: Days,
    customer_bookings: List[tuple[int, int, int]],
):
    """Solves the shift scheduling problem."""
    model = cp_model.CpModel()

    # Hour constraints on continuous hours
    shift_constraints = [
        # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
        (3, 6, 1, 0, 10, 8),
    ]

    # Total weekly hours per employee constraints
    weekly_hour_constraints = [
        # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
        (20, 30, 1, 40, 45, 1)
    ]

    # Linear terms of the objective in a minimization context.
    obj_int_vars = []
    obj_int_coeffs = []
    obj_bool_vars = []
    obj_bool_coeffs = []

    work = {}
    for e in range(num_employees):
        for i, d in enumerate(days):
            hours = getHoursFromDict(d)
            for h in range(hours):
                work[e, i, h] = model.NewBoolVar("work%i_%i_%i" % (e, i, h))

    # Shift constraints
    for ct in shift_constraints:
        hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for e in range(num_employees):
            for i, d in enumerate(days):
                hours = getHoursFromDict(d)
                works = [work[e, i, h] for h in range(hours)]
                variables, coeffs = add_soft_sequence_constraint(
                    model,
                    works,
                    hard_min,
                    soft_min,
                    min_cost,
                    soft_max,
                    hard_max,
                    max_cost,
                    "shift_constraint(employee %i)" % e,
                )
                obj_bool_vars.extend(variables)
                obj_bool_coeffs.extend(coeffs)

    # Booking constraints
    for booking in customer_bookings:
        d, h, bookings = booking
        workingEmployees = []
        for e in range(num_employees):
            workingEmployees.append(work[(e, d, h)])
        model.Add(sum(workingEmployees) >= bookings)

    # Weekly hour constraints
    for ct in weekly_hour_constraints:
        hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
        for e in range(num_employees):
            totalHours = []
            for i, d in enumerate(days):
                hours = getHoursFromDict(d)
                for h in range(hours):
                    totalHours.append(work[(e, i, h)])
            variables, coeffs = add_soft_sum_constraint(
                model,
                totalHours,
                hard_min,
                soft_min,
                min_cost,
                soft_max,
                hard_max,
                max_cost,
                "weekly_sum_constraint(employee %i, day %i, hour %i)" % (e, i, h),
            )
            obj_int_vars.extend(variables)
            obj_int_coeffs.extend(coeffs)

    # At least one employee works any given hour any given day
    for i, d in enumerate(days):
        hours = getHoursFromDict(d)
        for h in range(hours):
            assignments = []
            for e in range(num_employees):
                assignments.append(work[(e, i, h)])
            model.AddAtLeastOne(assignments)

    # No gaps in the middle of a shift
    for e in range(num_employees):
        for i, d in enumerate(days):
            hours = getHoursFromDict(d)
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
            for e in range(num_employees):
                schedule = ""
                hours = []
                hoursOfTheDay = getHoursFromDict(d)
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
        for e in range(num_employees):
            hours = 0
            for i, d in enumerate(days):
                hoursOfTheDay = getHoursFromDict(d)
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


def getHoursFromDict(day: Dict[DaysKey, int]):
    hours = day.get("hours")
    if not isinstance(hours, int):
        raise Exception("An hour has a None value " + str(day))
    return hours


def main(_=None):
    num_employees = int(sys.argv[1])
    days = json.loads(sys.argv[2])
    customer_bookings = sys.argv[3]

    print("Days: " + str(days))
    customer_bookings_array = list(map(int, customer_bookings.split(",")))
    print("Bookings: " + str(customer_bookings_array))

    customer_bookings_tuple_array = [
        tuple(customer_bookings_array[i : i + 3])
        for i in range(0, len(customer_bookings_array), 3)
    ]
    print(customer_bookings_tuple_array)

    solve_shift_scheduling(num_employees, days, customer_bookings_tuple_array)


if __name__ == "__main__":
    app.run(main)
