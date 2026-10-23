from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('showroom', '0009_seed_faq_items'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='showroom.customer'),
        ),
    ]