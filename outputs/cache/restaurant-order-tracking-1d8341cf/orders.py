"""Single Order Tracking for a Restaurant."""

import time

class RestaurantOrder:

    def __init__(self, item_name, customer_id):
        self.item = item_name
        self.customer_id = customer_id
        self.status = "PLACED"
        self.history = [("PLACED", time.time())]

    def update_status(self, new_status):
        valid_statuses = ["PLACED", "PREPARING", "READY", "DELIVERED"]
        if new_status not in valid_statuses:
            print(f"Error: Invalid status '{new_status}'")
            return False

        self.status = new_status
        self.history.append((new_status, time.time()))
        print(f"Order for {self.item} updated to: {self.status}")
        return True

    def get_status(self):
        return self.status

    def display_history(self):
        print(f"\n--- Order History for Customer {self.customer_id} ({self.item}) ---")
        for status, timestamp in self.history:
            print(f"[{time.strftime('%H:%M:%S', time.localtime(timestamp))}] - {status}")
        print("-" * 40)


if __name__ == "__main__":
    order1 = RestaurantOrder("Pilau", 101)

    order1.display_history()

    
    order1.update_status("PREPARING")
    time.sleep(5)
    order1.update_status("READY")
    time.sleep(5)
    order1.update_status("DELIVERED")

    # order1.update_status("BOGUS") 

    order1.display_history()