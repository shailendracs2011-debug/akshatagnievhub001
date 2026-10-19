import base64
import io

from django import forms

from .images import bytes_to_data_url, thumbnail_data_url, HERO_BYTES, HERO_EDGE, THUMBNAIL_BYTES
from .models import (
    Enquiry,
    GalleryImage,
    Order,
    Product,
    ProductGallery,
    ServiceQuery,
    SiteSetting,
    SupportQuery,
    ProductEMIPlan,
    Testimonial,
)

MAX_IMAGE_BYTES = 150 * 1024
MAX_IMAGE_EDGE = 1600


def image_to_data_url(uploaded):
    """Convert an uploaded image into a compressed WebP data URL.

    Photos are stored inside the database as data URLs so the site stays
    portable between local SQLite and hosted PostgreSQL. Every upload is
    re-encoded to WebP and capped at roughly 150 KB so pages stay fast on
    a 4G connection.
    """
    if not uploaded:
        return ''
    uploaded.seek(0)
    raw = uploaded.read()
    uploaded.seek(0)
    optimized = bytes_to_data_url(raw)
    if optimized:
        return optimized
    encoded = base64.b64encode(raw).decode('ascii')
    content_type = getattr(uploaded, 'content_type', 'image/jpeg') or 'image/jpeg'
    return f'data:{content_type};base64,{encoded}'


class ProductAdminForm(forms.ModelForm):
    """Django Admin form for Product with a real multipart image upload field."""

    image = forms.ImageField(
        required=False,
        label='Product Image / मुख्य उत्पाद फोटो',
        help_text='Upload JPG, JPEG, PNG or WEBP. Uploading a new image replaces the current product image.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = Product
        fields = [
            'name', 'name_hi', 'slug', 'category', 'segment',
            'short_description', 'short_description_hi',
            'description', 'description_hi', 'price', 'offer_price',
            'cost_price', 'stock', 'featured', 'published', 'coming_soon',
            'image', 'sku', 'battery', 'range_text', 'warranty', 'motor_power',
            'top_speed', 'charging_time', 'seating_capacity', 'gst_percent',
            'booking_amount', 'emi_enabled',
            'range_km', 'top_speed_kmph', 'battery_type', 'battery_warranty_years',
            'load_capacity_kg', 'licence_required', 'colours',
            'who_is_this_for', 'who_is_this_for_hi', 'price_label',
        ]

    def save(self, commit=True):
        obj = super().save(commit=False)
        uploaded = self.cleaned_data.get('image')
        if uploaded:
            raw = uploaded.read()
            uploaded.seek(0)
            obj.image_data = bytes_to_data_url(raw)
            obj.thumb_data = thumbnail_data_url(raw)
        if commit:
            obj.save()
        return obj


class ProductGalleryForm(forms.ModelForm):
    """Admin form for additional product gallery photos."""

    image = forms.ImageField(
        required=False,
        label='Gallery Image / गैलरी फोटो',
        help_text='Upload JPG, JPEG, PNG or WEBP.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = ProductGallery
        fields = ['product', 'caption', 'sort_order', 'published', 'image']

    def save(self, commit=True):
        obj = super().save(commit=False)
        uploaded = self.cleaned_data.get('image')
        if uploaded:
            raw = uploaded.read()
            uploaded.seek(0)
            obj.image_data = bytes_to_data_url(raw)
            obj.thumb_data = thumbnail_data_url(raw)
        if commit:
            obj.save()
        return obj


class GalleryImageAdminForm(forms.ModelForm):
    """Admin form for the public real-photo gallery."""

    image = forms.ImageField(
        required=False,
        label='Gallery Photo / गैलरी फोटो',
        help_text='Upload JPG, JPEG, PNG or WEBP.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = GalleryImage
        fields = [
            'title', 'title_hi', 'description', 'description_hi',
            'category', 'image', 'published', 'featured', 'sort_order',
        ]

    def save(self, commit=True):
        obj = super().save(commit=False)
        uploaded = self.cleaned_data.get('photo')
        if uploaded:
            raw = uploaded.read()
            uploaded.seek(0)
            obj.photo_data = bytes_to_data_url(raw, THUMBNAIL_BYTES, 320)
            obj.thumb_data = thumbnail_data_url(raw, 160, 12 * 1024)
        if commit:
            obj.save()
        return obj


class TestimonialAdminForm(forms.ModelForm):
    """Admin form for customer testimonials, including the customer photo."""

    photo = forms.ImageField(
        required=False,
        label='Customer Photo / ग्राहक फोटो',
        help_text='Optional. A real photo builds trust. Keep it small, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = Testimonial
        fields = ['name', 'town', 'vehicle', 'quote', 'photo', 'published', 'sort_order']

    def save(self, commit=True):
        obj = super().save(commit=False)
        uploaded = self.cleaned_data.get('image')
        if uploaded:
            raw = uploaded.read()
            uploaded.seek(0)
            obj.image_data = bytes_to_data_url(raw)
            obj.thumb_data = thumbnail_data_url(raw)
        if commit:
            obj.save()
        return obj


class SiteSettingAdminForm(forms.ModelForm):
    """Admin form for business settings and replaceable homepage/logo images."""

    hero_image = forms.ImageField(
        required=False,
        label='Homepage Hero Image / होमपेज फोटो',
        help_text='Upload a new image to replace the current homepage hero photo.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_image_web = forms.ImageField(
        required=False,
        label='Hero Photo — Web (wide) / हीरो फोटो — वेब',
        help_text='Wide photo for desktop screens. Landscape, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_image_mobile = forms.ImageField(
        required=False,
        label='Hero Photo — Mobile (tall) / हीरो फोटो — मोबाइल',
        help_text='Tall photo for phones. Portrait, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    offer_banner_image = forms.ImageField(
        required=False,
        label='Offer Banner Image / ऑफर बैनर फोटो',
        help_text='Optional small image shown beside the offer banner text.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    logo_image = forms.ImageField(
        required=False,
        label='Logo / लोगो',
        help_text='Upload a new logo to replace the current logo.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = SiteSetting
        fields = '__all__'

    def save(self, commit=True):
        obj = super().save(commit=False)
        hero = self.cleaned_data.get('hero_image')
        logo = self.cleaned_data.get('logo_image')
        hero_web = self.cleaned_data.get('hero_image_web')
        hero_mobile = self.cleaned_data.get('hero_image_mobile')
        banner_image = self.cleaned_data.get('offer_banner_image')

        if hero:
            obj.hero_image_data = image_to_data_url(hero)
        if hero_web:
            raw = hero_web.read(); hero_web.seek(0)
            obj.hero_image_web = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        if hero_mobile:
            raw = hero_mobile.read(); hero_mobile.seek(0)
            obj.hero_image_mobile = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        if banner_image:
            raw = banner_image.read(); banner_image.seek(0)
            obj.offer_banner_image = thumbnail_data_url(raw)
        if logo:
            raw = logo.read(); logo.seek(0)
            obj.logo_data = bytes_to_data_url(raw, THUMBNAIL_BYTES, 240)
        if commit:
            obj.save()
        return obj


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'email', 'product', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 4})}


class TestRideForm(forms.ModelForm):
    """Book a test ride for a specific model."""

    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'preferred_day', 'product']
        widgets = {
            'preferred_day': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Your name / आपका नाम',
            'phone': 'Mobile number / मोबाइल नंबर',
            'preferred_day': 'Preferred day / पसंदीदा दिन',
            'product': 'Model / मॉडल',
        }

    def clean_name(self):
        value = (self.cleaned_data.get('name') or '').strip()
        if not value:
            raise forms.ValidationError('Name is required. / नाम ज़रूरी है।')
        return value

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError('Enter a valid mobile number. / सही मोबाइल नंबर डालें।')
        return value


class PartRequestForm(forms.ModelForm):
    """Ask the showroom for a spare part."""

    vehicle_model = forms.CharField(
        max_length=150,
        required=False,
        label='Vehicle model / वाहन मॉडल',
        help_text='For example: SPORTS SL, E-Auto L5.',
    )

    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'vehicle_model', 'product', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Which part do you need?'})}
        labels = {
            'name': 'Your name / आपका नाम',
            'phone': 'Mobile number / मोबाइल नंबर',
            'product': 'Model / मॉडल',
            'message': 'Part needed / कौन सा पार्ट',
        }

    def clean_name(self):
        value = (self.cleaned_data.get('name') or '').strip()
        if not value:
            raise forms.ValidationError('Name is required. / नाम ज़रूरी है।')
        return value

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError('Enter a valid mobile number. / सही मोबाइल नंबर डालें।')
        return value

    def clean_message(self):
        value = (self.cleaned_data.get('message') or '').strip()
        if not value:
            raise forms.ValidationError('Tell us which part you need. / बताएँ कौन सा पार्ट चाहिए।')
        return value


class TrackRequestForm(forms.Form):
    """Look up a customer's own requests by mobile number."""

    phone = forms.CharField(
        max_length=30,
        label='Mobile number / मोबाइल नंबर',
        widget=forms.TextInput(attrs={'inputmode': 'tel', 'autocomplete': 'tel', 'placeholder': '10-digit mobile number'}),
    )

    def clean_phone(self):
        value = (self.cleaned_data.get('phone') or '').strip()
        digits = ''.join(ch for ch in value if ch.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError('Enter a valid mobile number. / सही मोबाइल नंबर डालें।')
        return digits


class OrderForm(forms.ModelForm):
    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        if product is not None:
            self.fields['emi_plan'].queryset = product.emi_plans.filter(active=True)
        else:
            self.fields['emi_plan'].queryset = ProductEMIPlan.objects.none()

    class Meta:
        model = Order
        fields = ['name', 'phone', 'email', 'address', 'payment_mode', 'emi_plan', 'payment_status', 'paid_amount', 'notes']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('payment_mode') == 'EMI' and not cleaned.get('emi_plan'):
            self.add_error('emi_plan', 'Please select an EMI plan.')
        if cleaned.get('payment_mode') != 'EMI':
            cleaned['emi_plan'] = None
        paid = cleaned.get('paid_amount') or 0
        # The final order amount is calculated from product price × quantity in the view.
        if paid < 0:
            self.add_error('paid_amount', 'Paid amount cannot be negative.')
        return cleaned


class ServiceQueryForm(forms.ModelForm):
    class Meta:
        model = ServiceQuery
        fields = ['name', 'mobile', 'query', 'category', 'vehicle_model', 'preferred_date']
        widgets = {
            'query': forms.Textarea(attrs={'rows': 5}),
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'name': 'Customer Name / ग्राहक का नाम *',
            'mobile': 'Mobile Number / मोबाइल नंबर *',
            'query': 'Query / Problem / समस्या या पूछताछ',
            'category': 'Service Category / सर्विस श्रेणी',
            'vehicle_model': 'Vehicle / Model / वाहन / मॉडल',
            'preferred_date': 'Preferred Date / पसंदीदा तारीख',
        }

    def clean_name(self):
        value = self.cleaned_data.get('name', '').strip()
        if not value:
            raise forms.ValidationError('Customer Name is mandatory.')
        return value

    def clean_mobile(self):
        value = self.cleaned_data.get('mobile', '').strip()
        if not value:
            raise forms.ValidationError('Mobile Number is mandatory.')
        return value


class SupportQueryForm(forms.ModelForm):
    class Meta:
        model = SupportQuery
        fields = ['name', 'mobile', 'query', 'category', 'order_number']
        widgets = {'query': forms.Textarea(attrs={'rows': 5})}
        labels = {
            'name': 'Customer Name / ग्राहक का नाम *',
            'mobile': 'Mobile Number / मोबाइल नंबर *',
            'query': 'Query / Problem / समस्या या पूछताछ',
            'category': 'Support Category / सहायता श्रेणी',
            'order_number': 'Order / Booking Number / ऑर्डर नंबर',
        }

    def clean_name(self):
        value = self.cleaned_data.get('name', '').strip()
        if not value:
            raise forms.ValidationError('Customer Name is mandatory.')
        return value

    def clean_mobile(self):
        value = self.cleaned_data.get('mobile', '').strip()
        if not value:
            raise forms.ValidationError('Mobile Number is mandatory.')
        return value


class SiteSettingForm(forms.ModelForm):
    signature_image = forms.ImageField(
        required=False,
        label='Authorized Signatory Signature / प्राधिकरण हस्ताक्षर',
        help_text='Upload a new signature image to replace the current signature.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png'}),
    )
    hero_image_web = forms.ImageField(
        required=False,
        label='Hero Photo — Web (wide) / हीरो फोटो — वेब',
        help_text='Wide photo for desktop screens. Landscape, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_image_mobile = forms.ImageField(
        required=False,
        label='Hero Photo — Mobile (tall) / हीरो फोटो — मोबाइल',
        help_text='Tall photo for phones. Portrait, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    logo_image = forms.ImageField(
        required=False,
        label='Logo / लोगो',
        help_text='Upload a new logo to replace the current logo.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    offer_banner_image = forms.ImageField(
        required=False,
        label='Offer Banner Image / ऑफर बैनर फोटो',
        help_text='Optional small image shown beside the offer banner text.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )

    class Meta:
        model = SiteSetting
        fields = [
            'business_name', 'authorized_person', 'gst_number', 'website',
            'phone_primary', 'phone_secondary', 'address', 'whatsapp',
            'signatory_name', 'signature_image',
            'tagline', 'tagline_hi', 'about', 'about_hi',
            'hero_title', 'hero_title_hi', 'hero_subtitle', 'hero_subtitle_hi',
            'hero_image_web', 'hero_image_mobile', 'logo_image',
            'landmark', 'landmark_hi', 'opening_hours', 'opening_hours_hi',
            'google_maps_url', 'map_embed_url',
            'offer_banner_text', 'offer_banner_text_hi', 'offer_banner_link',
            'offer_banner_image',
            'why_brand_authorised', 'why_brand_authorised_hi',
            'why_warranty', 'why_warranty_hi',
            'why_free_service', 'why_free_service_hi',
            'why_local_centre', 'why_local_centre_hi',
            'default_daily_km', 'default_petrol_price', 'default_petrol_mileage',
            'default_electricity_rate', 'default_ev_km_per_unit',
        ]

    def save(self, commit=True):
        obj = super().save(commit=False)
        sig = self.cleaned_data.get('signature_image')
        if sig:
            obj.signature_data = image_to_data_url(sig)
        hero_web = self.cleaned_data.get('hero_image_web')
        if hero_web:
            raw = hero_web.read(); hero_web.seek(0)
            obj.hero_image_web = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        hero_mobile = self.cleaned_data.get('hero_image_mobile')
        if hero_mobile:
            raw = hero_mobile.read(); hero_mobile.seek(0)
            obj.hero_image_mobile = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        logo = self.cleaned_data.get('logo_image')
        if logo:
            raw = logo.read(); logo.seek(0)
            obj.logo_data = bytes_to_data_url(raw, THUMBNAIL_BYTES, 240)
        banner = self.cleaned_data.get('offer_banner_image')
        if banner:
            raw = banner.read(); banner.seek(0)
            obj.offer_banner_image = thumbnail_data_url(raw)
        if commit:
            obj.save()
        return obj
