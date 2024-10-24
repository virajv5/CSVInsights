from sqlite3 import IntegrityError

from pydantic import ValidationError
from rest_framework import serializers
from .models import Purchase, Customer, Sales
# Customer


# product serializers
class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['item_id', 'purchase_date', 'name', 'quantity', 'price']


class QueryInputSerializer(serializers.Serializer):
    query = serializers.CharField()

class QuerySerializer(serializers.Serializer):
        text = serializers.CharField(required=True)


class QuerySerializer(serializers.Serializer):
    text = serializers.CharField()

# customer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customer_name', 'email', 'phone_number']

# sales
class SalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sales
        fields = ['customer', 'item', 'quantity', 'total_price', 'sales_date']