from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('showroom', '0002_automation_emi')]

    operations = [
        migrations.AlterField(
            model_name='order', name='status',
            field=models.CharField(
                choices=[('BOOKED','Booked'),('CONFIRMED','Confirmed'),('READY','Ready'),('DELIVERED','Delivered'),('COMPLETED','Completed'),('CANCELLED','Cancelled')],
                default='BOOKED', max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='sale', name='payment_mode',
            field=models.CharField(
                choices=[('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit'),('EMI','EMI')],
                default='Cash', max_length=30,
            ),
        ),
    ]
