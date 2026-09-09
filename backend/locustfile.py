import random
from locust import HttpUser, task, between

class StoreUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def view_products(self):
        self.client.get("/api/products/public?limit=20&page=1")

    @task(2)
    def view_categories(self):
        self.client.get("/api/categories")

    @task(1)
    def view_single_product(self):
        # We'll just hit a random search
        self.client.get(f"/api/products/public?search=pen")
