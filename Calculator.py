"""Interactive Calculator & Unit Converter (CLI)

Menu-driven program: arithmetic + unit conversions.
Keeps asking until the user chooses Quit.
"""

import math

# All conversion factors live in ONE place - change them here only.
FACTORS = {
    "km_to_miles": 0.621371,
    "kg_to_pounds": 2.20462,
    "c_to_f_multiplier": 9 / 5,
    "c_to_f_offset": 32,
}


# ---------- Input helpers ----------

def read_number(prompt):
    """Keep asking until the user types a valid number (never crashes)."""
    while True:
        try:
            value = float(input(prompt))
            if not math.isfinite(value):  # rejects 'nan' and 'inf'
                raise ValueError
            return value
        except ValueError:
            print("Please enter a number, for example 12 or 3.5.")


def read_choice(prompt, valid_options):
    """Keep asking until the user picks one of the valid options."""
    while True:
        choice = input(prompt).strip()
        if choice in valid_options:
            return choice
        print(f"Please pick one of: {', '.join(valid_options)}.")


def format_number(value):
    """Show 5.0 as 5 and long decimals rounded to 4 places."""
    if isinstance(value, str):
        return value
    if value == int(value):
        return str(int(value))
    return str(round(value, 4))


# ---------- Arithmetic (one function per operation) ----------

def add(a, b):
    """Return a + b."""
    return a + b


def subtract(a, b):
    """Return a - b."""
    return a - b


def multiply(a, b):
    """Return a * b."""
    return a * b


def divide(a, b):
    """Return a / b, or a clear message if b is zero."""
    if b == 0:
        return "Cannot divide by zero."
    return a / b


# ---------- Unit conversions (one function per conversion) ----------

def km_to_miles(km):
    """Convert kilometres to miles."""
    return km * FACTORS["km_to_miles"]


def celsius_to_fahrenheit(c):
    """Convert Celsius to Fahrenheit."""
    return c * FACTORS["c_to_f_multiplier"] + FACTORS["c_to_f_offset"]


def kg_to_pounds(kg):
    """Convert kilograms to pounds."""
    return kg * FACTORS["kg_to_pounds"]


# ---------- Menus ----------

def do_arithmetic(choice):
    """Ask for two numbers and run the chosen operation."""
    operations = {"1": add, "2": subtract, "3": multiply, "4": divide}
    a = read_number("First number: ")
    b = read_number("Second number: ")
    result = operations[choice](a, b)
    print("Result:", format_number(result))


def do_conversion():
    """Show the conversion sub-menu and run the chosen conversion."""
    print("\n  a) km to miles   b) Celsius to Fahrenheit   c) kg to pounds")
    choice = read_choice("  Choose conversion: ", ("a", "b", "c")).lower()

    if choice == "a":
        value = read_number("Kilometres: ")
        print("Result:", format_number(km_to_miles(value)), "miles")
    elif choice == "b":
        value = read_number("Celsius: ")
        print("Result:", format_number(celsius_to_fahrenheit(value)), "F")
    else:
        value = read_number("Kilograms: ")
        print("Result:", format_number(kg_to_pounds(value)), "pounds")


def main():
    """Main menu loop - repeats until the user picks Quit."""
    while True:
        print("\n===== Calculator & Unit Converter =====")
        print("1) Add   2) Subtract   3) Multiply   4) Divide")
        print("5) Convert units       6) Quit")
        choice = read_choice("Choose an option: ", ("1", "2", "3", "4", "5", "6"))

        if choice == "6":
            print("Goodbye!")
            break
        elif choice == "5":
            do_conversion()
        else:
            do_arithmetic(choice)


if __name__ == "__main__":
    main()