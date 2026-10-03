import base64
from django import forms
from .models import Enquiry, Order, Product, ProductGallery, GalleryImage, ServiceQuery, SupportQuery


def image_to_data_url(uploaded):
    if not uploaded:
        return ''
    raw = uploaded.read()
    encoded = base64.b64encode(raw).decode('ascii')
    content_type = getattr(uploaded, 'content_type', 'image/jpeg')
    return f'data:{content_type};base64,{encoded}'


class ImageUploadMixin:
    image = forms.ImageField(required=False, label='Upload / Replace Image')
    def save_image(self, obj, uploaded):
        if uploaded:
            obj.image_data = image_to_data_url(uploaded)
        return obj


class ProductAdminForm(ImageUploadMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
    def save(self, commit=True):
        obj = super().save(commit=False); self.save_image(obj, self.cleaned_data.get('image'))
        if commit: obj.save()
        return obj


class ProductGalleryForm(ImageUploadMixin, forms.ModelForm):
    image = forms.ImageField(required=False)
    class Meta:
        model = ProductGallery
        fields = ['product','caption','sort_order','published','image']
    def save(self, commit=True):
        obj = super().save(commit=False); self.save_image(obj, self.cleaned_data.get('image'))
        if commit: obj.save()
        return obj


class GalleryImageAdminForm(ImageUploadMixin, forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = '__all__'
    def save(self, commit=True):
        obj = super().save(commit=False); self.save_image(obj, self.cleaned_data.get('image'))
        if commit: obj.save()
        return obj


class SiteSettingAdminForm(ImageUploadMixin, forms.ModelForm):
    hero_image = forms.ImageField(required=False)
    logo_image = forms.ImageField(required=False)
    class Meta:
        model = __import__('showroom.models', fromlist=['SiteSetting']).SiteSetting
        fields = '__all__'
    def save(self, commit=True):
        obj = super().save(commit=False)
        if self.cleaned_data.get('hero_image'): obj.hero_image_data = image_to_data_url(self.cleaned_data['hero_image'])
        if self.cleaned_data.get('logo_image'): obj.logo_data = image_to_data_url(self.cleaned_data['logo_image'])
        if commit: obj.save()
        return obj


class EnquiryForm(forms.ModelForm):
    class Meta:
        model = Enquiry; fields = ['name','phone','email','product','message']
        widgets = {'message': forms.Textarea(attrs={'rows':4})}


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order; fields = ['name','phone','email','address','notes']
        widgets = {'address': forms.Textarea(attrs={'rows':3}), 'notes': forms.Textarea(attrs={'rows':3})}


class ServiceQueryForm(forms.ModelForm):
    class Meta:
        model = ServiceQuery; fields = ['name','mobile','query','category','vehicle_model','preferred_date']
        widgets = {'query': forms.Textarea(attrs={'rows':5}), 'preferred_date': forms.DateInput(attrs={'type':'date'})}
        labels = {'name':'Customer Name / ग्राहक का नाम *','mobile':'Mobile Number / मोबाइल नंबर *','query':'Query / Problem / समस्या या पूछताछ','category':'Service Category / सर्विस श्रेणी','vehicle_model':'Vehicle / Model / वाहन / मॉडल','preferred_date':'Preferred Date / पसंदीदा तारीख'}
    def clean_name(self):
        v=self.cleaned_data.get('name','').strip()
        if not v: raise forms.ValidationError('Customer Name is mandatory.')
        return v
    def clean_mobile(self):
        v=self.cleaned_data.get('mobile','').strip()
        if not v: raise forms.ValidationError('Mobile Number is mandatory.')
        return v


class SupportQueryForm(forms.ModelForm):
    class Meta:
        model = SupportQuery; fields = ['name','mobile','query','category','order_number']
        widgets = {'query': forms.Textarea(attrs={'rows':5})}
        labels = {'name':'Customer Name / ग्राहक का नाम *','mobile':'Mobile Number / मोबाइल नंबर *','query':'Query / Problem / समस्या या पूछताछ','category':'Support Category / सहायता श्रेणी','order_number':'Order / Booking Number / ऑर्डर नंबर'}
    def clean_name(self):
        v=self.cleaned_data.get('name','').strip()
        if not v: raise forms.ValidationError('Customer Name is mandatory.')
        return v
    def clean_mobile(self):
        v=self.cleaned_data.get('mobile','').strip()
        if not v: raise forms.ValidationError('Mobile Number is mandatory.')
        return v
