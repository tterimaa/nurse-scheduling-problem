from absl import app
from absl import flags

from google.protobuf import text_format
from ortools.sat.python import cp_model

FLAGS = flags.FLAGS
flags.DEFINE_string('output_proto', '',
                    'Output file to write the cp_model proto to.')
flags.DEFINE_string('params', 'max_time_in_seconds:10.0',
                    'Sat solver parameters.')

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


def add_soft_sequence_constraint(model, works, hard_min, hard_max):
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

    # Just forbid any sequence of true variables with length hard_max + 1
    for start in range(len(works) - hard_max):
        model.AddBoolOr(
            [works[i].Not() for i in range(start, start + hard_max + 1)])
    return cost_literals, cost_coefficients



def solve_shift_scheduling(params, output_proto):
    """Solves the shift scheduling problem."""
    # Data
    num_employees = 4

    # Shift constraints on continuous sequence :
    #     (shift, hard_min, hard_max)
    shift_constraints = [
        # Shift lenght is 6-8h
        (6, 8),
    ]

    customer_bookings = [
        # (d, h, b) == Day d, Hour h+1 (hours go from 0 to 11) has b bookings
        (0, 0, 3), # Day 0, Hour 1 has 3 bookings
        (1, 4, 2), # Day 1 Hour 5 has 2 bookings
        (3, 1, 2), # Day 3 Hour 2 has 2 bookings
    ]

    model = cp_model.CpModel()

    num_days = 5
    num_hours = 12

    work = {}
    for e in range(num_employees):
        for d in range(num_days):
            for h in range(num_hours):
                work[e, d, h] = model.NewBoolVar('work%i_%i_%i' % (e, d, h))

    # Shift constraints
    for ct in shift_constraints:
        hard_min, hard_max = ct
        for e in range(num_employees):
            for d in range(num_days):
                works = [work[e, d, h] for h in range(num_hours)]
                variables, coeffs = add_soft_sequence_constraint(model, works, hard_min, hard_max)
    
    # Booking constraints
    for booking in customer_bookings:
        d, h, bookings = booking
        workingEmployees = []
        for e in range(num_employees):
            workingEmployees.append(work[(e, d, h)])
        model.Add(sum(workingEmployees) >= bookings)

    # At least one employee works any given hour any given day
    for d in range(num_days):
        for h in range(num_hours):
            assignments = []
            for e in range(num_employees):
                assignments.append(work[(e, d, h)])
            model.AddAtLeastOne(assignments)

    # Solve the model.
    solver = cp_model.CpSolver()
    if params:
        text_format.Parse(params, solver.parameters)
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    status = solver.Solve(model, solution_printer)

    # Print solution.
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        for d in range(num_days):
            print('\nDAY %i' % d)                 
            header = '          '   
            header += '1  2  3  4  5  6  7  8  9  10 11 12'
            print(header)           
            for e in range(num_employees):
                schedule = ''       
                for h in range(num_hours):
                    if solver.BooleanValue(work[(e, d, h)]):
                        schedule += 'X' + '  '
                    else:           
                        schedule += '.' + '  '
                print('worker %i: %s' % (e, schedule))

def main(_=None):
    solve_shift_scheduling(FLAGS.params, FLAGS.output_proto)

if __name__ == '__main__':
    app.run(main)