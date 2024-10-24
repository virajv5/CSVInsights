# Generated by Django 4.1.13 on 2024-09-20 06:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("project", "0007_customer"),
    ]

    operations = [
        migrations.CreateModel(
            name="Sales",
            fields=[
                ("sales_id", models.AutoField(primary_key=True, serialize=False)),
                ("quantity", models.PositiveIntegerField()),
                ("total_price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("sales_date", models.DateField()),
                (
                    "customer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="project.customer",
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="project.purchase",
                    ),
                ),
            ],
        ),
    ]
