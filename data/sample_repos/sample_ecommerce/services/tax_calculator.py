"""Tax calculation engine for ecommerce orders."""

def calculate_tax(amount: float, tax_rate: float = 0.08) -> float:
    """
    Calculates sales tax for a given transaction amount.
    Returns the computed tax amount rounded to 2 decimal places.
    """
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    return round(amount * tax_rate, 2)

def calculate_discount(amount: float, discount_percent: float) -> float:
    """Calculates discount to be subtracted from total."""
    return round(amount * (discount_percent / 100.0), 2)
