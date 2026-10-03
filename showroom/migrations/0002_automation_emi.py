from django.db import migrations, models


def mark_existing_transactions_as_applied(apps, schema_editor):
    Sale = apps.get_model('showroom', 'Sale')
    Purchase = apps.get_model('showroom', 'Purchase')
    Sale.objects.update(paid_amount=models.F('amount'))
    Purchase.objects.update(paid_amount=models.F('amount'))
    for obj in Sale.objects.exclude(product_id=None):
        Sale.objects.filter(pk=obj.pk).update(stock_applied_quantity=obj.quantity, stock_applied_product_id=obj.product_id)
    for obj in Purchase.objects.exclude(product_id=None):
        Purchase.objects.filter(pk=obj.pk).update(stock_applied_quantity=obj.quantity, stock_applied_product_id=obj.product_id)
    LedgerEntry = apps.get_model('showroom', 'LedgerEntry')
    Expense = apps.get_model('showroom', 'Expense')
    for obj in Sale.objects.all():
        LedgerEntry.objects.get_or_create(reference=f'SALE:{obj.pk}:REVENUE', entry_type='CREDIT', defaults={'account':'Sales Revenue','amount':obj.amount,'date':obj.sale_date,'narration':f'Sale {obj.invoice_no}'})
        payment_account = 'Accounts Receivable' if obj.payment_mode == 'Credit' else obj.payment_mode
        LedgerEntry.objects.get_or_create(reference=f'SALE:{obj.pk}:PAYMENT', entry_type='DEBIT', defaults={'account':payment_account,'amount':obj.amount,'date':obj.sale_date,'narration':f'Payment against {obj.invoice_no}'})
    for obj in Purchase.objects.all():
        LedgerEntry.objects.get_or_create(reference=f'PURCHASE:{obj.pk}:COST', entry_type='DEBIT', defaults={'account':'Purchases / Inventory','amount':obj.amount,'date':obj.purchase_date,'narration':f'Purchase {obj.bill_no}'})
        payment_account = 'Accounts Payable' if obj.payment_mode == 'Credit' else obj.payment_mode
        LedgerEntry.objects.get_or_create(reference=f'PURCHASE:{obj.pk}:PAYMENT', entry_type='CREDIT', defaults={'account':payment_account,'amount':obj.amount,'date':obj.purchase_date,'narration':f'Payment against {obj.bill_no}'})
    for obj in Expense.objects.all():
        LedgerEntry.objects.get_or_create(reference=f'EXPENSE:{obj.pk}:COST', entry_type='DEBIT', defaults={'account':obj.category,'amount':obj.amount,'date':obj.date,'narration':obj.description})
        LedgerEntry.objects.get_or_create(reference=f'EXPENSE:{obj.pk}:PAYMENT', entry_type='CREDIT', defaults={'account':obj.payment_mode,'amount':obj.amount,'date':obj.date,'narration':f'Payment for {obj.description}'})

import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('showroom', '0001_initial')]

    operations = [
        migrations.AddField(model_name='product', name='motor_power', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='product', name='top_speed', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='product', name='charging_time', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='product', name='seating_capacity', field=models.CharField(blank=True, max_length=80)),
        migrations.AddField(model_name='product', name='gst_percent', field=models.DecimalField(decimal_places=2, default=0, max_digits=5)),
        migrations.AddField(model_name='product', name='booking_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='product', name='emi_enabled', field=models.BooleanField(default=False)),
        migrations.CreateModel(
            name='ProductEMIPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('tenure_months', models.PositiveIntegerField(default=12)),
                ('interest_rate', models.DecimalField(decimal_places=2, default=0, help_text='Annual interest rate in percent', max_digits=6)),
                ('down_payment', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('processing_fee', models.DecimalField(decimal_places=2, default=0, max_digits=12)),
                ('active', models.BooleanField(default=True)),
                ('sort_order', models.PositiveIntegerField(default=0)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emi_plans', to='showroom.product')),
            ],
            options={'ordering': ['sort_order', 'tenure_months']},
        ),
        migrations.AddField(model_name='order', name='emi_plan', field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='showroom.productemiplan')),
        migrations.AddField(model_name='order', name='payment_mode', field=models.CharField(choices=[('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit'),('EMI','EMI')], default='Cash', max_length=30)),
        migrations.AddField(model_name='order', name='payment_status', field=models.CharField(choices=[('PENDING','Pending'),('PARTIAL','Partially Paid'),('PAID','Paid')], default='PENDING', max_length=20)),
        migrations.AddField(model_name='order', name='paid_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='sale', name='order', field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sale', to='showroom.order')),
        migrations.AddField(model_name='sale', name='auto_generated_from_order', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='sale', name='stock_applied_quantity', field=models.PositiveIntegerField(default=0, editable=False)),
        migrations.AddField(model_name='sale', name='stock_applied_product_id', field=models.PositiveBigIntegerField(blank=True, editable=False, null=True)),
        migrations.AddField(model_name='sale', name='payment_mode', field=models.CharField(choices=[('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit'),('EMI','EMI')], default='Cash', max_length=30)),
        migrations.AddField(model_name='sale', name='paid_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='purchase', name='payment_mode', field=models.CharField(choices=[('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit')], default='Cash', max_length=30)),
        migrations.AddField(model_name='purchase', name='paid_amount', field=models.DecimalField(decimal_places=2, default=0, max_digits=12)),
        migrations.AddField(model_name='purchase', name='stock_applied_quantity', field=models.PositiveIntegerField(default=0, editable=False)),
        migrations.AddField(model_name='purchase', name='stock_applied_product_id', field=models.PositiveBigIntegerField(blank=True, editable=False, null=True)),
        migrations.RunPython(mark_existing_transactions_as_applied, migrations.RunPython.noop),
    ]
