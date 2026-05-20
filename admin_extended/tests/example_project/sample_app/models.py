from django.db import models


class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

    class Meta:
        app_label = "sample_app"

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("active", "Active"), ("archived", "Archived")]
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    notes = models.TextField(blank=True, default="")

    class Meta:
        app_label = "sample_app"

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="orders")
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    region = models.CharField(max_length=50, blank=True, default="")

    class Meta:
        app_label = "sample_app"
