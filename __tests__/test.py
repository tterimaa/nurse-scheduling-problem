import unittest
from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, bool_vars, helpers, helpers_2):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solutions = 0
        self.bool_vars = bool_vars
        self.helpers = helpers
        self.helpers_2 = helpers_2

    def on_solution_callback(self):
        self.solutions += 1
        print(f"Solution {self.solutions}:")
        for x_var in self.bool_vars:
            print(self.Value(x_var), end=" ")
        print()
        for x_var in self.helpers:
            print(self.Value(x_var), end=" ")
        print()
        for x_var in self.helpers_2:
            print(self.Value(x_var), end=" ")
        print()


class TestNoGapsConstraint(unittest.TestCase):
    def test_gap_constraint(self):
        model = cp_model.CpModel()

        # Initialize the model
        vars = []
        for i in range(10):
            vars.append(model.NewBoolVar("test_var%i" % i))

        model.Add(vars[1] == 1)
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

        model.Add(sum(vars) == 6)

        solver = cp_model.CpSolver()
        solution_callback = SolutionPrinter(vars, true_to_false, false_to_true)
        solver.parameters.max_time_in_seconds = 5
        status = solver.SearchForAllSolutions(model, solution_callback)

        print(status)
        assert status == cp_model.FEASIBLE

    def test_gap_constraint_infeasible(self):
        model = cp_model.CpModel()

        # Initialize the model
        vars = []
        for i in range(10):
            vars.append(model.NewBoolVar("test_var%i" % i))

        model.Add(vars[1] == 1)
        model.Add(vars[9] == 1)

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

        model.Add(sum(vars) == 6)

        solver = cp_model.CpSolver()
        solution_callback = SolutionPrinter(vars, true_to_false, false_to_true)
        solver.parameters.max_time_in_seconds = 5
        status = solver.SearchForAllSolutions(model, solution_callback)

        assert status == cp_model.INFEASIBLE


if __name__ == "__main__":
    unittest.main()
