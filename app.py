from flask import Flask, render_template, request, jsonify
from datetime import datetime
import json
import math

app = Flask(__name__)

# Loan types
LOAN_TYPES = ["Home", "Car", "Business", "Education", "Agriculture", "Dairy"]

def validate_cnic(cnic):
    """Validate CNIC format: XXXXX-XXXXXXX-X"""
    import re
    return bool(re.match(r'^\d{5}-\d{7}-\d{1}$', cnic))

def validate_loan(data):
    """Validate loan application based on type and rules"""
    errors = []
    
    # CNIC validation
    if not validate_cnic(data.get('cnic', '')):
        errors.append("Invalid CNIC format. Use: XXXXX-XXXXXXX-X")
    
    # Age validation for regular loans
    loan_type = data.get('loanType', 'Home')
    age = int(data.get('age', 0))
    
    if loan_type in ['Home', 'Car']:
        if age < 22 or age > 60:
            errors.append(f"Age must be 22-60 years for {loan_type} loans")
    
    elif loan_type == 'Business':
        if age < 22 or age > 70:
            errors.append("Age must be 22-70 years for Business loans")
    
    elif loan_type == 'Education':
        student_age = int(data.get('studentAge', 0))
        if student_age < 18 or student_age > 50:
            errors.append("Student age must be 18-50 years")
    
    elif loan_type in ['Agriculture', 'Dairy']:
        land_acres = float(data.get('landAcres', 0))
        if land_acres <= 13:
            errors.append(f"{loan_type} loans require more than 13 acres")
    
    return errors

def calculate_emi(principal, annual_rate, tenure_months):
    """Calculate EMI using standard formula: EMI = [P × r × (1 + r)^n] / [(1 + r)^n – 1]"""
    monthly_rate = annual_rate / 12 / 100
    
    if monthly_rate == 0:
        monthly_emi = principal / tenure_months
    else:
        numerator = principal * monthly_rate * math.pow(1 + monthly_rate, tenure_months)
        denominator = math.pow(1 + monthly_rate, tenure_months) - 1
        monthly_emi = numerator / denominator
    
    total_payable = monthly_emi * tenure_months
    total_interest = total_payable - principal
    
    # Generate amortization schedule
    schedule = []
    remaining_balance = principal
    
    for month in range(1, min(tenure_months + 1, 13)):  # Show first 12 months
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_emi - interest_payment
        remaining_balance -= principal_payment
        
        schedule.append({
            'month': month,
            'emi': round(monthly_emi, 2),
            'principal': round(principal_payment, 2),
            'interest': round(interest_payment, 2),
            'balance': round(max(0, remaining_balance), 2)
        })
    
    return {
        'monthlyEMI': round(monthly_emi, 2),
        'totalInterest': round(total_interest, 2),
        'totalPayable': round(total_payable, 2),
        'schedule': schedule,
        'tenure': tenure_months
    }

@app.route('/')
def index():
    return render_template('index.html', loan_types=LOAN_TYPES)

@app.route('/api/validate', methods=['POST'])
def validate():
    """Validate loan application"""
    try:
        data = request.json
        errors = validate_loan(data)
        
        return jsonify({
            'isValid': len(errors) == 0,
            'errors': errors
        })
    except Exception as e:
        return jsonify({'isValid': False, 'errors': [str(e)]}), 400

@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculate EMI"""
    try:
        data = request.json
        
        # Validate inputs
        principal = float(data.get('loanAmount', 0))
        annual_rate = float(data.get('interestRate', 0))
        tenure = int(data.get('loanTenure', 0))
        
        if principal <= 0:
            return jsonify({'error': 'Loan amount must be greater than 0'}), 400
        if annual_rate < 0 or annual_rate > 100:
            return jsonify({'error': 'Interest rate must be between 0 and 100'}), 400
        if tenure <= 0:
            return jsonify({'error': 'Loan tenure must be greater than 0'}), 400
        
        # Calculate EMI
        result = calculate_emi(principal, annual_rate, tenure)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Server error'}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
