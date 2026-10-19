from django.core.management.base import BaseCommand

from showroom.faq_content import FAQ_CONTENT
from showroom.models import FAQItem


class Command(BaseCommand):
    help = 'Create the starter FAQ questions for first-time EV buyers. Existing answers are kept.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--refresh',
            action='store_true',
            help='Overwrite answers the owner has already edited with the shipped ones.',
        )

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for index, item in enumerate(FAQ_CONTENT):
            defaults = {
                'question_hi': item['question_hi'],
                'answer': item['answer'],
                'answer_hi': item['answer_hi'],
                'needs_confirmation': False,
                'published': True,
                'sort_order': index + 1,
            }
            existing = FAQItem.objects.filter(question=item['question']).first()
            if existing is None:
                FAQItem.objects.create(question=item['question'], **defaults)
                created += 1
                continue
            if not options['refresh']:
                continue
            changed = [field for field, value in defaults.items() if getattr(existing, field) != value]
            if changed:
                for field in changed:
                    setattr(existing, field, defaults[field])
                existing.save(update_fields=changed)
                updated += 1
        self.stdout.write(self.style.SUCCESS(f'FAQ ready. {created} new, {updated} refreshed, {FAQItem.objects.count()} total.'))
        self.stdout.write('Edit the answers in Admin, FAQ items. Nothing is overwritten unless --refresh is used.')
