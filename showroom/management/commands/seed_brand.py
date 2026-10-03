from pathlib import Path
from django.core.management.base import BaseCommand
from showroom.models import Activity, SiteSetting
import base64

class Command(BaseCommand):
    help = "Create starter Akshat Agni website settings and showroom activity."

    def handle(self, *args, **kwargs):
        SiteSetting.objects.update_or_create(
            pk=1,
            defaults={
                "business_name": "Akshat Agni EV Motors",
                "tagline": "Shubh Shuruaat, Agni ki Raftaar",
                "tagline_hi": "शुभ शुरुआत, अग्नि की रफ्तार",
                "phone_primary": "9425969464",
                "phone_secondary": "7974281559",
                "address": "Maihar, Madhya Pradesh",
                "address_hi": "मैहर, मध्य प्रदेश",
                "whatsapp": "9425969464",
            },
        )
        base = Path(__file__).resolve().parents[4]
        image = base / "static" / "images" / "showroom-banner.jpg"
        if image.exists():
            data = "data:image/jpeg;base64," + base64.b64encode(image.read_bytes()).decode("ascii")
            Activity.objects.update_or_create(
                title="Akshat Agni EV Motors — Showroom",
                defaults={
                    "title_hi": "अक्षत अग्नि ईवी मोटर्स — शोरूम",
                    "category": "Showroom",
                    "description": "Our Maihar showroom — EV sales, service, spares, batteries and accessories.",
                    "description_hi": "हमारा मैहर शोरूम — ईवी बिक्री, सर्विस, स्पेयर पार्ट्स, बैटरी और एक्सेसरीज़।",
                    "image_data": data,
                    "published": True,
                    "featured": True,
                    "sort_order": 1,
                },
            )
        self.stdout.write(self.style.SUCCESS("Starter brand settings and showroom image are ready."))
