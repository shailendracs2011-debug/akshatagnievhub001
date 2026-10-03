import base64

from django import forms

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
)


def image_to_data_url(uploaded):
    if not uploaded:
        return ''
    raw = uploaded.read()
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
        ]

    def save(self, commit=True):
        obj = super().save(commit=False)
        uploaded = self.cleaned_data.get('image')
        if uploaded:
            obj.image_data = image_to_data_url(uploaded)
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
            obj.image_data = image_to_data_url(uploaded)
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
            obj.image_data = image_to_data_url(uploaded)
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
        if hero:
            obj.hero_image_data = image_to_data_url(hero)
        if logo:
            obj.logo_data = image_to_data_url(logo)
        if commit:
            obj.save()
        return obj


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry
        fields = ['name', 'phone', 'email', 'product', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 4})}


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

    class Meta:
        model = SiteSetting
        fields = [
            'business_name', 'authorized_person', 'gst_number', 'website',
            'phone_primary', 'phone_secondary', 'address', 'whatsapp',
            'signatory_name', 'signature_image',
            'tagline', 'tagline_hi', 'about', 'about_hi',
            'hero_title', 'hero_title_hi', 'hero_subtitle', 'hero_subtitle_hi',
        ]

    def save(self, commit=True):
        obj = super().save(commit=False)
        sig = self.cleaned_data.get('signature_image')
        if sig:
            obj.signature_data = image_to_data_url(sig)
        if commit:
            obj.save()
        return obj
