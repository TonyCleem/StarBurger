from django.db import migrations


def replace_null_with_empty(apps, schema_editor):
    Order = apps.get_model("foodcartapp", "Order")
    Order.objects.filter(comment__isnull=True).update(comment="")


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("foodcartapp", "0046_alter_order_phonenumber"),
    ]
    operations = [
        migrations.RunPython(replace_null_with_empty, reverse_func),
    ]
