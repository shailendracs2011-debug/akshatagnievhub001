import base64

from django.core.management.base import BaseCommand

from showroom.images import avatar_from_data_url, optimize_data_url, thumbnail_from_data_url
from showroom.models import (
    GalleryImage,
    Product,
    ProductGallery,
    SiteSetting,
    Testimonial,
)

# model class -> list of field names holding a data URL
TARGETS = [
    (Product, ['image_data']),
    (ProductGallery, ['image_data']),
    (GalleryImage, ['image_data']),
    (Testimonial, ['photo_data']),
    (SiteSetting, [
        'logo_data', 'hero_image_data', 'hero_image_web', 'hero_image_mobile',
        'offer_banner_image', 'signature_data',
    ]),
]

# model class -> field holding the small version
THUMB_TARGETS = [
    (Product, 'thumb_data'),
    (ProductGallery, 'thumb_data'),
    (GalleryImage, 'thumb_data'),
    (Testimonial, 'thumb_data'),
]


class Command(BaseCommand):
    help = 'Re-compress every stored image to WebP under 150 KB and build grid thumbnails. Safe to run more than once.'

    def handle(self, *args, **kwargs):
        before = 0
        after = 0
        changed = 0

        for model, fields in TARGETS:
            for obj in model.objects.all():
                for field in fields:
                    value = getattr(obj, field, '') or ''
                    if not value.startswith('data:'):
                        continue
                    before += len(value)
                    optimized = optimize_data_url(value)
                    after += len(optimized)
                    if optimized != value:
                        setattr(obj, field, optimized)
                        obj.save(update_fields=[field])
                        changed += 1

        thumbs = 0
        for model, field in THUMB_TARGETS:
            source = 'photo_data' if model is Testimonial else 'image_data'
            for obj in model.objects.all():
                raw = getattr(obj, source, '') or ''
                if not raw.startswith('data:'):
                    continue
                # Testimonial photos are round avatars, so they get a much
                # smaller crop than the grid thumbnails used elsewhere.
                if model is Testimonial:
                    thumb = avatar_from_data_url(raw)
                else:
                    thumb = thumbnail_from_data_url(raw)
                if thumb and thumb != (getattr(obj, field, '') or ''):
                    setattr(obj, field, thumb)
                    obj.save(update_fields=[field])
                    thumbs += 1

        saved_mb = (before - after) / (1024 * 1024)
        self.stdout.write(self.style.SUCCESS(
            f'Images optimised: {changed} full image(s) updated, {thumbs} thumbnail(s) built, '
            f'{before / (1024 * 1024):.1f} MB -> {after / (1024 * 1024):.1f} MB (saved {saved_mb:.1f} MB).'
        ))
