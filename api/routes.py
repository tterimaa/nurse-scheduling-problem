from flask import Flask, request, jsonify
from model.solver import solve_shift_scheduling
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/echo", methods=["POST"])
def echo():
    data = request.data
    return data


@app.route("/endpoint", methods=["POST"])
def endpoint():
    data = request.json

    if not data:
        return jsonify({"error": "No JSON data received"})

    num_employees = data.get("num_employees")
    days = data.get("days")
    constraints = data.get("employee_constraints")
    customer_bookings_input = data.get("bookings")

    print(customer_bookings_input)
    customer_bookings = list(map(map_function, customer_bookings_input))
    print(customer_bookings)
    success, res = solve_shift_scheduling(
        num_employees, days, constraints, customer_bookings
    )

    if success is False:
        return jsonify(
            {
                "status": 400,
                "message": "Processing the request took too long: check parameters",
            }
        )

    return jsonify({"status": 200, "message": "OK", "res": res})


def map_function(obj):
    day = obj["day"]
    hour = obj["hour"]
    bookings = obj["bookings"]
    return (day, hour, bookings)


if __name__ == "__main__":
    app.run()
