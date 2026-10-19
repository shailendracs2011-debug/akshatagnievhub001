from django.core.management.base import BaseCommand

from showroom.models import FAQItem

# The eight questions a first-time EV buyer asks most often. The answers are
# deliberately left empty and flagged for confirmation: the showroom owner
# fills them in from Admin so nothing is published that has not been checked.
QUESTIONS = [
    {
        'question': 'Do I need a driving licence to ride an electric scooter?',
        'question_hi': 'क्या इलेक्ट्रिक स्कूटर चलाने के लिए ड्राइविंग लाइसेंस चाहिए?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'What is the real range I will get on one charge?',
        'question_hi': 'एक चार्ज पर असली रेंज कितनी मिलेगी?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'How long does charging take, and what does it cost?',
        'question_hi': 'चार्जिंग में कितना समय लगता है और खर्चा कितना आता है?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'What happens during power cuts?',
        'question_hi': 'बिजली कटने पर क्या होता है?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'How long does the battery last, and when is it replaced?',
        'question_hi': 'बैटरी कितने साल चलती है और कब बदलनी पड़ती है?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'What does servicing involve, and how often is it needed?',
        'question_hi': 'सर्विस में क्या होता है और कितनी बार करवानी पड़ती है?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'Can I buy on EMI or finance?',
        'question_hi': 'क्या EMI या फ़ाइनेंस पर खरीद सकते हैं?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
    {
        'question': 'Can I exchange my old vehicle for an EV?',
        'question_hi': 'क्या पुराना वाहन बदलकर EV ले सकते हैं?',
        'answer': '[ANSWER_NEEDS_SHOWROOM_CONFIRMATION]',
        'answer_hi': '[उत्तर की पुष्टि शोरूम से करानी है]',
    },
]


class Command(BaseCommand):
    help = 'Create the starter FAQ questions for first-time EV buyers. Answers stay marked for confirmation.'

    def handle(self, *args, **kwargs):
        created = 0
        for index, item in enumerate(QUESTIONS):
            _, was_created = FAQItem.objects.update_or_create(
                question=item['question'],
                defaults={
                    'question_hi': item['question_hi'],
                    'answer': item['answer'],
                    'answer_hi': item['answer_hi'],
                    'needs_confirmation': True,
                    'published': True,
                    'sort_order': index + 1,
                },
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f'FAQ ready. {created} new, {len(QUESTIONS)} total.'))
        self.stdout.write('Answers are placeholders. Edit them in Admin, FAQ items, then untick Needs confirmation.')
