# Generated by Django 4.1.13 on 2024-09-22 18:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0011_sales"),
    ]

    operations = [
        migrations.RenameField(
            model_name="customer",
            old_name="email",
            new_name="customer_email",
        ),
    ]
