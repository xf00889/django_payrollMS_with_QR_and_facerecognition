# Given Information
from decimal import Decimal
# Given Information
daily_rate = 100
duty_hours = 8
number_of_days = 15
incentive_pay = 0
meal_allowance = 0
house_rent_allowance = 0

# Calculate Gross Pay
daily_gross_pay = daily_rate * duty_hours
total_gross_pay = daily_gross_pay * number_of_days

# Tax Thresholds and Rates
tax_thresholds = {
    0: Decimal('20833.33'),
    1: (Decimal('20833.34'), Decimal('33333.33')),
    2: (Decimal('33333.34'), Decimal('66666.67')),
    3: (Decimal('66666.68'), Decimal('166666.67')),
    4: (Decimal('166666.68'), Decimal('666666.67')),
    5: Decimal('666666.68')
}

tax_rates = {
    0: Decimal('0.00'),
    1: Decimal('0.15'),
    2: Decimal('0.20'),
    3: Decimal('0.25'),
    4: Decimal('0.30'),
    5: Decimal('0.35')
}

# Calculate Professional Tax
current_tax_bracket = 0
for index, bounds in tax_thresholds.items():
    if isinstance(bounds, Decimal):
        if total_gross_pay <= bounds:
            current_tax_bracket = index
            break
    else:
        lower_bound, upper_bound = bounds
        if lower_bound <= total_gross_pay <= upper_bound:
            current_tax_bracket = index
            break

lower_bound = tax_thresholds[current_tax_bracket][0] if isinstance(tax_thresholds[current_tax_bracket], tuple) else Decimal('0.00')
tax_rate = tax_rates[current_tax_bracket]
professional_tax = (total_gross_pay - lower_bound) * tax_rate

# Calculate Net Pay
net_pay = total_gross_pay - professional_tax

# Print the corrected calculated values
print(f"Total Gross Pay: {total_gross_pay}")
print(f"Professional Tax: {professional_tax}")
print(f"Net Pay: {net_pay}")