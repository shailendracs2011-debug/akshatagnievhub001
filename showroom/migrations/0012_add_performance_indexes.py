from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('showroom', '0011_sale_invoice_fields'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['published'], name='showroom_ca_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='enquiry',
            index=models.Index(fields=['created_at'], name='showroom_en_created_idx'),
        ),
        migrations.AddIndex(
            model_name='faqitem',
            index=models.Index(fields=['published'], name='showroom_fa_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='galleryimage',
            index=models.Index(fields=['published'], name='showroom_ga_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='offer',
            index=models.Index(fields=['published'], name='showroom_of_publish_idx'),
        ),
        migrations.AddIndex(
            model_name='order',
            index=models.Index(fields=['created_at'], name='showroom_or_created_idx'),
        ),
        migrations.AddIndex(
            model_name='sale',
            index=models.Index(fields=['sale_date'], name='showroom_sa_sale_date_idx'),
        ),
        migrations.AddIndex(
            model_name='testimonial',
            index=models.Index(fields=['published'], name='showroom_te_publish_idx'),
        ),
    ]
