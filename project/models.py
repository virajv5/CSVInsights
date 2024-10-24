from django.db import models

# Create your models here.
from django.db import models


# purchasing stocks

class Purchase(models.Model):
    item_id = models.AutoField(primary_key=True)
    purchase_date = models.DateField()
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name}"


# customers
class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)  # AutoField without AUTOINCREMENT
    customer_name = models.CharField(max_length=255)
    customer_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)


    def __str__(self):
         return f"{self.customer_name}"


# sales
class Sales(models.Model):
    sales_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)  # Foreign key from Customer model
    item = models.ForeignKey(Purchase, on_delete=models.CASCADE)  # Foreign key from Purchase model
    quantity = models.PositiveIntegerField()  # Sales quantity
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Total price for the sale
    sales_date = models.DateField()  # Date of the sale

    def __str__(self):
        return f"Sale {self.sales_id} - {self.customer.customer_name} - {self.item.name}"
