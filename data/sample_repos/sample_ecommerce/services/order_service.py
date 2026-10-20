from services.tax_calculator import calculate_tax

class OrderService:
    """Manages order creation, pricing calculation, and checkout workflows."""
    
    def __init__(self, currency: str = "USD"):
        self.currency = currency
        self.orders = {}

    def process_order(self, order_id: str, items_total: float) -> dict:
        """
        Processes order total by calculating tax and preparing payment invoice.
        """
        tax_amount = calculate_tax(items_total)
        total_due = items_total + tax_amount
        order_record = {
            "order_id": order_id,
            "subtotal": items_total,
            "tax": tax_amount,
            "total": total_due,
            "status": "pending_payment"
        }
        self.orders[order_id] = order_record
        return order_record
