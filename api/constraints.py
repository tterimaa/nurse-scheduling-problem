from typing import Dict, List

from api.utils import get_hours

# Default week constraints
WEEK_HARD_MAX = 51
WEEK_HARD_MIN = 37
WEEK_SOFT_MIN = 0
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

def get_weekly_constraints_for_employee(employee: int, weekly_constraints):
    constraint = weekly_constraints[employee]
    hard_max = constraint.get("hard_max")
    hard_min = constraint.get("hard_min")
    hard_max = WEEK_HARD_MAX if hard_max is None else min(WEEK_HARD_MAX, hard_max)
    hard_min = WEEK_HARD_MIN if hard_min is None else max(WEEK_HARD_MIN, hard_min)
    hard_min = hard_max if hard_min > hard_max else hard_min
    hard_max = hard_min if hard_max < hard_min else hard_max
    print(hard_max)
    print(hard_min)
    # (hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
    weekly_hour_constraints = (hard_min, WEEK_SOFT_MIN, WEEK_MIN_COST, WEEK_SOFT_MAX, hard_max, WEEK_MAX_COST)
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
