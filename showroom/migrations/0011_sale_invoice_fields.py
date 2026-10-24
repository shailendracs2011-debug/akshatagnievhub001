from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('showroom', '0010_order_customer'),
    ]

    operations = [
        migrations.AddField(
            model_name='sale',
            name='billing_address',
            field=models.TextField(blank=True, help_text='Billing address shown on the invoice.'),
        ),
        migrations.AddField(
            model_name='sale',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='sale',
            name='invoice_code',
            field=models.CharField(blank=True, help_text='System-generated short code used for public invoice verification / QR link.', max_length=20, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='sale',
            name='shipping_address',
            field=models.TextField(blank=True, help_text='Shipping/delivery address shown on the invoice.'),
        ),
    ]
