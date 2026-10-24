import base64
import io
from datetime import date

from django import forms
from django.urls import reverse_lazy

from .images import bytes_to_data_url, thumbnail_data_url, HERO_BYTES, HERO_EDGE, THUMBNAIL_BYTES
from .models import (
    Customer,
    Enquiry,
    GalleryImage,
    Order,
    Product,
    ProductGallery,
    Sale,
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
        uploaded = self.cleaned_data.get('image')
        if uploaded:
            raw = uploaded.read()
            uploaded.seek(0)
            obj.image_data = bytes_to_data_url(raw)
            obj.thumb_data = thumbnail_data_url(raw)
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


class StoredImagePreview(forms.Widget):
    """Show the picture that is currently stored for a settings column.

    The stored pictures are base64 data URLs. Putting them back into the form
    as textareas would post about a megabyte of text on every save, and the
    hosting platform rejects a request body that large before the request
    even reaches the app. The picture is therefore shown as a link to the
    image endpoint instead of being carried inside the form.
    """

    def __init__(self, source='', caption='', **kwargs):
        # The source stays lazy: resolving it while the module is imported
        # would load the URLconf before it is ready.
        self.source = source
        self.caption = caption
        super().__init__(**kwargs)

    def render(self, name, value, attrs=None, renderer=None):
        source = str(self.source)
        if not value:
            return f'<p style="margin:0 0 6px;color:#666">{self.caption}: not set</p>'
        preview = f'{source}?w=360'
        return (
            f'<p style="margin:0 0 6px">{self.caption}: '
            f'<a href="{source}" target="_blank">'
            f'<img src="{preview}" alt="" style="max-width:360px;max-height:160px;'
            f'object-fit:contain;vertical-align:middle"></a></p>'
        )


class SiteSettingAdminForm(forms.ModelForm):
    """Admin form for business settings and replaceable homepage/logo images."""

    # The upload fields deliberately use their own names. A form field that
    # shares a name with a model column overwrites that column with None
    # whenever the owner saves the page without picking a new file, which
    # silently cleared the hero photos and the offer banner.
    hero_upload = forms.ImageField(
        required=False,
        label='Homepage Hero Image / होमपेज फोटो',
        help_text='Upload a new image to replace the current homepage hero photo.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_web_upload = forms.ImageField(
        required=False,
        label='Hero Photo — Web (wide) / हीरो फोटो — वेब',
        help_text='Wide photo for desktop screens. Landscape, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_mobile_upload = forms.ImageField(
        required=False,
        label='Hero Photo — Mobile (tall) / हीरो फोटो — मोबाइल',
        help_text='Tall photo for phones. Portrait, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    banner_upload = forms.ImageField(
        required=False,
        label='Offer Banner Image / ऑफर बैनर फोटो',
        help_text='Optional small image shown beside the offer banner text.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    logo_upload = forms.ImageField(
        required=False,
        label='Logo / लोगो',
        help_text='Upload a new logo to replace the current logo.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    signature_upload = forms.ImageField(
        required=False,
        label='Authorized Signatory Signature / प्राधिकरण हस्ताक्षर',
        help_text='Upload a new signature image to replace the current signature.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png,image/jpeg,image/webp'}),
    )
    hero_preview = forms.CharField(
        required=False,
        label='Current hero photo',
        widget=StoredImagePreview(
            source=reverse_lazy('media_site_image', args=['hero']),
            caption='Current hero photo',
        ),
    )
    logo_preview = forms.CharField(
        required=False,
        label='Current logo',
        widget=StoredImagePreview(
            source=reverse_lazy('media_site_image', args=['logo']),
            caption='Current logo',
        ),
    )

    class Meta:
        model = SiteSetting
        # The base64 columns stay out of the form. They are replaced through
        # the upload fields above, and keeping them out stops every save from
        # posting megabytes of image data back to the server.
        exclude = [
            'hero_image_data', 'hero_image_web', 'hero_image_mobile',
            'logo_data', 'signature_data', 'offer_banner_image',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = self.instance
        self.initial['hero_preview'] = '1' if (site.hero_image_web or site.hero_image_data) else ''
        self.initial['logo_preview'] = '1' if site.logo_data else ''

    def save(self, commit=True):
        obj = super().save(commit=False)
        hero = self.cleaned_data.get('hero_upload')
        logo = self.cleaned_data.get('logo_upload')
        hero_web = self.cleaned_data.get('hero_web_upload')
        hero_mobile = self.cleaned_data.get('hero_mobile_upload')
        banner_image = self.cleaned_data.get('banner_upload')
        signature = self.cleaned_data.get('signature_upload')

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
        if signature:
            obj.signature_data = image_to_data_url(signature)
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
    """ERP settings form.

    The picture fields carry their own names on purpose. A form field that
    shares a name with a model column overwrites that column with None when
    the page is saved without a new file, which cleared the hero photos and
    the offer banner.
    """

    signature_image = forms.ImageField(
        required=False,
        label='Authorized Signatory Signature / प्राधिकरण हस्ताक्षर',
        help_text='Upload a new signature image to replace the current signature.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/png'}),
    )
    hero_web_upload = forms.ImageField(
        required=False,
        label='Hero Photo — Web (wide) / हीरो फोटो — वेब',
        help_text='Wide photo for desktop screens. Landscape, under 150 KB.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_mobile_upload = forms.ImageField(
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
    banner_upload = forms.ImageField(
        required=False,
        label='Offer Banner Image / ऑफर बैनर फोटो',
        help_text='Optional small image shown beside the offer banner text.',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/jpeg,image/png,image/webp'}),
    )
    hero_preview = forms.CharField(
        required=False,
        label='Current hero photo',
        widget=StoredImagePreview(
            source=reverse_lazy('media_site_image', args=['hero']),
            caption='Current hero photo',
        ),
    )
    logo_preview = forms.CharField(
        required=False,
        label='Current logo',
        widget=StoredImagePreview(
            source=reverse_lazy('media_site_image', args=['logo']),
            caption='Current logo',
        ),
    )

    class Meta:
        model = SiteSetting
        fields = [
            'business_name', 'authorized_person', 'gst_number', 'website',
            'email',
            'instagram_url',
            'facebook_url',
            'youtube_url',
            'twitter_url',
            'phone_primary', 'phone_secondary', 'address', 'whatsapp',
            'signatory_name', 'signature_image',
            'tagline', 'tagline_hi', 'about', 'about_hi',
            'hero_title', 'hero_title_hi', 'hero_subtitle', 'hero_subtitle_hi',
            'logo_image',
            'landmark', 'landmark_hi', 'opening_hours', 'opening_hours_hi',
            'google_maps_url', 'map_embed_url',
            'offer_banner_text', 'offer_banner_text_hi', 'offer_banner_link',
            'why_brand_authorised', 'why_brand_authorised_hi',
            'why_warranty', 'why_warranty_hi',
            'why_free_service', 'why_free_service_hi',
            'why_local_centre', 'why_local_centre_hi',
            'default_daily_km', 'default_petrol_price', 'default_petrol_mileage',
            'default_electricity_rate', 'default_ev_km_per_unit',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        site = self.instance
        self.initial['hero_preview'] = '1' if (site.hero_image_web or site.hero_image_data) else ''
        self.initial['logo_preview'] = '1' if site.logo_data else ''

    def save(self, commit=True):
        obj = super().save(commit=False)
        sig = self.cleaned_data.get('signature_image')
        if sig:
            obj.signature_data = image_to_data_url(sig)
        hero_web = self.cleaned_data.get('hero_web_upload')
        if hero_web:
            raw = hero_web.read(); hero_web.seek(0)
            obj.hero_image_web = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        hero_mobile = self.cleaned_data.get('hero_mobile_upload')
        if hero_mobile:
            raw = hero_mobile.read(); hero_mobile.seek(0)
            obj.hero_image_mobile = bytes_to_data_url(raw, HERO_BYTES, HERO_EDGE)
        logo = self.cleaned_data.get('logo_image')
        if logo:
            raw = logo.read(); logo.seek(0)
            obj.logo_data = bytes_to_data_url(raw, THUMBNAIL_BYTES, 240)
        banner = self.cleaned_data.get('banner_upload')
        if banner:
            raw = banner.read(); banner.seek(0)
            obj.offer_banner_image = thumbnail_data_url(raw)
        if commit:
            obj.save()
        return obj


class SaleForm(forms.ModelForm):
    """Admin-facing form to record a walk-in sale.

    The customer and order dropdowns are hooked up to JSON endpoints so
    picking a customer (or an existing order) auto-fills the name, phone
    and order details instead of re-typing them on every page.
    """

    class Meta:
        model = Sale
        fields = [
            'customer', 'order', 'customer_name', 'email', 'phone', 'billing_address', 'shipping_address',
            'product', 'quantity', 'amount', 'mrp_amount', 'discount_amount',
            'processing_fee', 'gst_amount', 'other_charges',
            'other_charges_description', 'paid_amount', 'payment_mode',
            'sale_date', 'notes',
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'select', 'data-autofill': 'customer'}),
            'order': forms.Select(attrs={'class': 'select', 'data-autofill': 'order'}),
            'customer_name': forms.TextInput(attrs={'class': 'input', 'autocomplete': 'off'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'autocomplete': 'off'}),
            'phone': forms.TextInput(attrs={'class': 'input', 'autocomplete': 'off', 'inputmode': 'tel'}),
            'billing_address': forms.Textarea(attrs={'class': 'input', 'rows': 2}),
            'shipping_address': forms.Textarea(attrs={'class': 'input', 'rows': 2}),
            'product': forms.Select(attrs={'class': 'select'}),
            'amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'mrp_amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'processing_fee': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'gst_amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'other_charges': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'paid_amount': forms.NumberInput(attrs={'class': 'input', 'step': '0.01'}),
            'payment_mode': forms.Select(attrs={'class': 'select'}),
            'sale_date': forms.DateInput(attrs={'class': 'input', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'input', 'rows': 3}),
            'other_charges_description': forms.TextInput(attrs={'class': 'input'}),
        }
        labels = {
            'customer': 'Customer / ग्राहक',
            'order': 'Existing Order / बुकिंग',
            'customer_name': 'Customer Name / ग्राहक का नाम',
            'phone': 'Phone / फ़ोन',
            'product': 'Product / उत्पाद',
            'quantity': 'Qty / मात्रा',
            'amount': 'Amount / राशि',
            'mrp_amount': 'MRP / अंकित मूल्य',
            'discount_amount': 'Discount / छूट',
            'processing_fee': 'Processing Fee / प्रोसेसिंग शुल्क',
            'gst_amount': 'GST / जीएसटी',
            'other_charges': 'Other Charges / अन्य शुल्क',
            'other_charges_description': 'Other Charges Note / टिप्पणी',
            'paid_amount': 'Paid Amount / भुगतान राशि',
            'payment_mode': 'Payment Mode / भुगतान का तरीका',
            'sale_date': 'Sale Date / बिक्री तिथि',
            'notes': 'Notes / नोट्स',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['customer'].queryset = Customer.objects.all().order_by('name')
        self.fields['customer'].empty_label = '-- Select customer --'
        self.fields['order'].queryset = Order.objects.select_related('product').order_by('-created_at')
        self.fields['order'].empty_label = '-- Select order --'
        self.fields['product'].queryset = Product.objects.all().order_by('name')
        self.fields['product'].empty_label = '-- Select product --'
        if not self.initial.get('sale_date'):
            self.initial['sale_date'] = date.today()
