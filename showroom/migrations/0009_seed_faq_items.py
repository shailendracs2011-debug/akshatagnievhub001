from django.db import migrations

from showroom.faq_content import FAQ_CONTENT


def seed_faq_items(apps, schema_editor):
    """Create the starter FAQ questions when the table has none.

    Production databases are created by `migrate` on every deploy, so without
    this the home page renders no FAQ section at all on a fresh environment.
    Questions the owner has edited are matched by their question text and left
    untouched.
    """
    FAQItem = apps.get_model('showroom', 'FAQItem')
    for index, item in enumerate(FAQ_CONTENT):
        if FAQItem.objects.filter(question=item['question']).exists():
            continue
        FAQItem.objects.create(
            question=item['question'],
            question_hi=item['question_hi'],
            answer=item['answer'],
            answer_hi=item['answer_hi'],
            needs_confirmation=False,
            published=True,
            sort_order=index + 1,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('showroom', '0008_sitesetting_email_sitesetting_facebook_url_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_faq_items, migrations.RunPython.noop),
    ]
