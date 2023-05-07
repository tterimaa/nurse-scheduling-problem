from flask import Flask, request, jsonify
from shift_scheduling import solve_shift_scheduling

app = Flask(__name__)

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
    customer_bookings = [(0,0,3)]
    success, res = solve_shift_scheduling(num_employees, num_days, num_hours, customer_bookings)

    return jsonify({'status': 200, 'message': 'OK', 'res': res})

if __name__ == '__main__':
    app.run()
