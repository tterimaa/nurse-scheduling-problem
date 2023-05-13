from flask import Flask, request, jsonify
from shift_scheduling import solve_shift_scheduling
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/echo', methods=['POST'])
def echo():
    data = request.data
    return data

@app.route('/endpoint', methods=['POST'])
def endpoint():
    data = request.json
    num_employees = data['num_employees']
    num_days = data['num_days']
    num_hours = data['num_hours']
    customer_bookings_input = data['customer_bookings']
    print(customer_bookings_input)
    customer_bookings = list(map(map_function, customer_bookings_input))
    print(customer_bookings)
    success, res = solve_shift_scheduling(num_employees, num_days, num_hours, customer_bookings)

    if success == False:
        return jsonify({'status': 400, 'message': 'Processing the request took too long: check parameters'})

    return jsonify({'status': 200, 'message': 'OK', 'res': res})

def map_function(obj):
    day = obj['day']
    hour = obj['hour']
    bookings = int(obj['bookings'])
    return (day, hour, bookings)

if __name__ == '__main__':
    app.run()
