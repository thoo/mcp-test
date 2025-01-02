from mcp.server.fastmcp import FastMCP
from typing import Optional, List, Dict, Any, Union

# Initialize the FastMCP server
mcp = FastMCP("CustomerDB")

# Database class definition (your existing FakeDatabase implementation)
class FakeDatabase:
    def __init__(self):
        self.customers = [
            {"id": "1213210", "name": "John Doe", "email": "john@gmail.com", "phone": "123-456-7890", "username": "johndoe"},
            {"id": "2837622", "name": "Priya Patel", "email": "priya@candy.com", "phone": "987-654-3210", "username": "priya123"},
            {"id": "3924156", "name": "Liam Nguyen", "email": "lnguyen@yahoo.com", "phone": "555-123-4567", "username": "liamn"},
            {"id": "4782901", "name": "Aaliyah Davis", "email": "aaliyahd@hotmail.com", "phone": "111-222-3333", "username": "adavis"},
            {"id": "5190753", "name": "Hiroshi Nakamura", "email": "hiroshi@gmail.com", "phone": "444-555-6666", "username": "hiroshin"},
            {"id": "6824095", "name": "Fatima Ahmed", "email": "fatimaa@outlook.com", "phone": "777-888-9999", "username": "fatimaahmed"},
            {"id": "7135680", "name": "Alejandro Rodriguez", "email": "arodriguez@protonmail.com", "phone": "222-333-4444", "username": "alexr"},
            {"id": "8259147", "name": "Megan Anderson", "email": "megana@gmail.com", "phone": "666-777-8888", "username": "manderson"},
            {"id": "9603481", "name": "Kwame Osei", "email": "kwameo@yahoo.com", "phone": "999-000-1111", "username": "kwameo"},
            {"id": "1057426", "name": "Mei Lin", "email": "meilin@gmail.com", "phone": "333-444-5555", "username": "mlin"}
        ]

        self.orders = [
            {"id": "24601", "customer_id": "1213210", "product": "Wireless Headphones", "quantity": 1, "price": 79.99, "status": "Shipped"},
            {"id": "13579", "customer_id": "1213210", "product": "Smartphone Case", "quantity": 2, "price": 19.99, "status": "Processing"},
            {"id": "97531", "customer_id": "2837622", "product": "Bluetooth Speaker", "quantity": 1, "price": 49.99, "status": "Shipped"},
            {"id": "86420", "customer_id": "3924156", "product": "Fitness Tracker", "quantity": 1, "price": 129.99, "status": "Delivered"},
            {"id": "54321", "customer_id": "4782901", "product": "Laptop Sleeve", "quantity": 3, "price": 24.99, "status": "Shipped"},
            {"id": "19283", "customer_id": "5190753", "product": "Wireless Mouse", "quantity": 1, "price": 34.99, "status": "Processing"},
            {"id": "74651", "customer_id": "6824095", "product": "Gaming Keyboard", "quantity": 1, "price": 89.99, "status": "Delivered"},
            {"id": "30298", "customer_id": "7135680", "product": "Portable Charger", "quantity": 2, "price": 29.99, "status": "Shipped"},
            {"id": "47652", "customer_id": "8259147", "product": "Smartwatch", "quantity": 1, "price": 199.99, "status": "Processing"},
            {"id": "61984", "customer_id": "9603481", "product": "Noise-Cancelling Headphones", "quantity": 1, "price": 149.99, "status": "Shipped"},
            {"id": "58243", "customer_id": "1057426", "product": "Wireless Earbuds", "quantity": 2, "price": 99.99, "status": "Delivered"},
            {"id": "90357", "customer_id": "1213210", "product": "Smartphone Case", "quantity": 1, "price": 19.99, "status": "Shipped"},
            {"id": "28164", "customer_id": "2837622", "product": "Wireless Headphones", "quantity": 2, "price": 79.99, "status": "Processing"}
        ]

    def get_user(self, key: str, value: str) -> Dict[str, str]:
        if key in {"email", "phone", "username"}:
            for customer in self.customers:
                if customer[key] == value:
                    return customer
            return f"Couldn't find a user with {key} of {value}"
        else:
            raise ValueError(f"Invalid key: {key}")

    def get_order_by_id(self, order_id: Union[str,int]) -> Optional[Dict[str, Any]]:
        for order in self.orders:
            if order["id"] == str(order_id):
                return order
        return None

    def get_customer_orders(self, customer_id: str) -> List[Dict[str, Any]]:
        return [order for order in self.orders if order["customer_id"] == customer_id]

    def cancel_order(self, order_id: str) -> str:
        order = self.get_order_by_id(order_id)
        if order:
            if order["status"] == "Processing":
                order["status"] = "Cancelled"
                return "Successfully cancelled the order"
            else:
                return "Order has already shipped. Cannot cancel it."
        return "Order not found"

# Create database instance
db = FakeDatabase()

# Define resources
@mcp.resource("customers://all")
def list_customers() -> str:
    """Return a list of all customers"""
    return "\n".join([
        f"Customer {c['id']}: {c['name']} ({c['email']})"
        for c in db.customers
    ])

@mcp.resource("orders://all")
def list_orders() -> str:
    """Return a list of all orders"""
    return "\n".join([
        f"Order {o['id']}: {o['product']} (Status: {o['status']})"
        for o in db.orders
    ])

# Define tools
@mcp.tool()
def get_user(key: str, value: str) -> str:
    """
    Look up a user by email, phone, or username.
    
    Args:
        key: The attribute to search by (email, phone, or username)
        value: The value to search for
    """
    try:
        result = db.get_user(key, value)
        if isinstance(result, dict):
            return (
                f"Found user:\n"
                f"Name: {result['name']}\n"
                f"Email: {result['email']}\n"
                f"Phone: {result['phone']}\n"
                f"Username: {result['username']}\n"
                f"Customer ID: {result['id']}"
            )
        return str(result)
    except ValueError as e:
        return str(e)

@mcp.tool()
def get_order_by_id(order_id: Union[int,str]) -> str:
    """
    Retrieve details of a specific order.
    
    Args:
        order_id: The unique identifier for the order
    """
    order = db.get_order_by_id(order_id)
    if order:
        return (
            f"Order details:\n"
            f"ID: {order['id']}\n"
            f"Product: {order['product']}\n"
            f"Quantity: {order['quantity']}\n"
            f"Price: ${order['price']}\n"
            f"Status: {order['status']}\n"
            f"Customer ID: {order['customer_id']}"
        )
    return "Order not found"

@mcp.tool()
def get_customer_orders(customer_id: Union[int,str]) -> str:
    """
    List all orders for a specific customer.
    
    Args:
        customer_id: The customer's unique identifier
    """
    customer_id = str(customer_id)
    orders = db.get_customer_orders(customer_id)
    if not orders:
        return f"No orders found for customer {customer_id}"
    
    order_list = "\n\n".join([
        f"Order ID: {order['id']}\n"
        f"Product: {order['product']}\n"
        f"Quantity: {order['quantity']}\n"
        f"Price: ${order['price']}\n"
        f"Status: {order['status']}"
        for order in orders
    ])
    
    return f"Orders for customer {customer_id}:\n\n{order_list}"

@mcp.tool()
def cancel_order(order_id: Union[int,str]) -> str:
    """
    Cancel a processing order.
    
    Args:
        order_id: The unique identifier for the order to cancel
    """
    return db.cancel_order(order_id)

# Add some helpful prompts
@mcp.prompt()
def search_customer(search_type: str, value: str) -> str:
    """Create a prompt for searching customers"""
    return f"Please find the customer with {search_type} matching '{value}'"

@mcp.prompt()
def track_order(order_id: Union[int,str]) -> str:
    """Create a prompt for tracking an order"""
    return f"What's the status of order {order_id}?"

if __name__ == "__main__":
    mcp.run()