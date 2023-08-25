from typing import Dict, List

from api.utils import get_hours

# WEEK CONSTRAINTS

# Default week constraints
WEEK_HARD_MAX = 51
WEEK_HARD_MIN = 30
WEEK_SOFT_MIN = 33
WEEK_MIN_COST = 1
WEEK_SOFT_MAX = 38
WEEK_MAX_COST = 1
DEFAULT_WEEK_CONSTRAINTS = (WEEK_HARD_MIN, WEEK_SOFT_MIN, WEEK_MIN_COST, WEEK_SOFT_MAX, WEEK_HARD_MAX, WEEK_MAX_COST)

Day = Dict[str, int]
Constraint = Dict[str, int]

def add_weekly_constraint(model, ct, totalHours, employee: int):
  hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
  variables, coeffs = add_soft_sum_constraint(
  model,
  totalHours,
  hard_min,
  soft_min,
  min_cost,
  soft_max,
  hard_max,
  max_cost,
  "weekly_sum_constraint(employee %i)" % employee,
  )
  return variables, coeffs

def get_weekly_constraints_for_employee(employee_constraints):
    weekly = employee_constraints.get("weekly")
    if weekly is None:
        return DEFAULT_WEEK_CONSTRAINTS
    hard_max = weekly.get("hard_max")
    hard_min = weekly.get("hard_min")
    hard_max = WEEK_HARD_MAX if hard_max is None else hard_max
    hard_min = WEEK_HARD_MIN if hard_min is None else hard_min
    hard_min = hard_max if hard_min > hard_max else hard_min
    hard_max = hard_min if hard_max < hard_min else hard_max
    soft_min = weekly.get("soft_min")
    soft_min = WEEK_SOFT_MIN if soft_min is None else soft_min
    soft_max = weekly.get("soft_max")
    soft_max = WEEK_SOFT_MAX if soft_max is None else soft_max
    # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
    weekly_hour_constraints = (hard_min, soft_min, WEEK_MIN_COST, soft_max, hard_max, WEEK_MAX_COST)
    return weekly_hour_constraints


def get_weekly_hour_variables_for_employee(employee: int, days: List[Day], work: Dict):
    totalHours = []
    for i, d in enumerate(days):
        hours = get_hours(d)
        for h in range(hours):
            totalHours.append(work[employee, i, h])
    return totalHours


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

# DAILY CONSTRAINTS

# Default daily constraints
DAY_HARD_MAX = 9
DAY_HARD_MIN = 6
DAY_SOFT_MIN = 7
DAY_MIN_COST = 1
DAY_SOFT_MAX = 8
DAY_MAX_COST = 1
DEFAULT_DAY_CONSTRAINTS = (DAY_HARD_MIN, DAY_SOFT_MIN, DAY_MIN_COST, DAY_SOFT_MAX, DAY_HARD_MAX, DAY_MAX_COST)

def get_daily_hour_constraints(daily_constraints, days):
  cts = []
  for d, day in enumerate(days):
    ct = daily_constraints.get(str(d)) # Day specific hour constraints
    if ct is None:
      ct = daily_constraints.get("defaults") # Personal defaults
    if ct is None:
      cts.append((d, day, DEFAULT_DAY_CONSTRAINTS)) # Global defaults as last resort
    else:
      dayMaxHours = get_hours(day)
      hard_max = ct.get("hard_max")
      hard_max = DAY_HARD_MAX if hard_max is None else hard_max
      # hard_max can't be greater than the number of hours in a day
      hard_max = dayMaxHours if hard_max > dayMaxHours else hard_max
      hard_min = ct.get("hard_min")
      hard_min = DAY_HARD_MIN if hard_min is None else hard_min
      hard_min = hard_max if hard_min > hard_max else hard_min # hard min can't be greater than hard max
      hard_max = hard_min if hard_max < hard_min else hard_max # hard max can't be smaller than hard min
      # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
      daily_hour_constraints = (hard_min, DAY_SOFT_MIN, DAY_MIN_COST, DAY_SOFT_MAX, hard_max, DAY_MAX_COST)
      cts.append((d, day, daily_hour_constraints))
  return cts

def add_daily_hour_constraints(model, works, ct, employee, d):
  hard_min, soft_min, min_cost, soft_max, hard_max, max_cost = ct
  variables, coeffs = add_soft_sequence_constraint(
                model,
                works,
                hard_min,
                soft_min,
                min_cost,
                soft_max,
                hard_max,
                max_cost,
                "shift_constraint(employee %i, day %i)" % (employee, d)
            )
  return variables, coeffs


def get_daily_hour_variables_for_employee(work, employee, dayIndex, hours):
    return [work[employee, dayIndex, h] for h in range(hours)]


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
