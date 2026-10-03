from django.contrib import admin
from django.utils.html import format_html
from .forms import ProductAdminForm, ProductGalleryForm, GalleryImageAdminForm, SiteSettingAdminForm
from .models import *

admin.site.site_header = 'Akshat Agni EV Motors — Admin'
admin.site.site_title = 'Akshat Agni Admin'
admin.site.index_title = 'Business & Website Management'

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=('name','name_hi','parent','sort_order','published')
    list_filter=('published','parent')
    search_fields=('name','name_hi')
    prepopulated_fields={'slug':('name',)}

class ProductEMIInline(admin.TabularInline):
    model = ProductEMIPlan
    extra = 1
    fields = ('tenure_months', 'interest_rate', 'down_payment', 'processing_fee', 'active', 'sort_order')


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    form = ProductGalleryForm
    extra = 1
    fields = ('caption', 'image', 'sort_order', 'published')
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [ProductEMIInline, ProductGalleryInline]
    list_display = ('image_thumb', 'name', 'category', 'segment', 'display_price', 'cost_price', 'stock', 'coming_soon', 'published', 'featured')
    list_filter = ('category', 'coming_soon', 'published', 'featured')
    search_fields = ('name', 'name_hi', 'sku', 'segment')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('image_preview',)
    fieldsets = (
        ('Basic Product Information', {
            'fields': ('name', 'name_hi', 'slug', 'category', 'segment', 'sku')
        }),
        ('Description & Pricing', {
            'fields': (
                'short_description', 'short_description_hi',
                'description', 'description_hi',
                'price', 'offer_price', 'cost_price', 'stock', 'gst_percent', 'booking_amount', 'emi_enabled'
            )
        }),
        ('Product Image', {
            'fields': ('image', 'image_preview'),
            'description': 'Upload or replace the main product photo here. The photo is stored with the product record and immediately appears on the website.'
        }),
        ('Vehicle Details', {
            'fields': ('battery', 'range_text', 'warranty', 'motor_power', 'top_speed', 'charging_time', 'seating_capacity')
        }),
        ('Publishing', {
            'fields': ('featured', 'published', 'coming_soon')
        }),
    )

    @admin.display(description='Image')
    def image_thumb(self, obj):
        if not obj or not obj.image_data:
            return '—'
        return format_html('<a href="{}" target="_blank" rel="noopener"><img src="{}" style="width:70px;height:50px;object-fit:contain;border-radius:8px;border:1px solid #ddd"></a>', obj.image_data, obj.image_data)

    @admin.display(description='Current Product Image')
    def image_preview(self, obj):
        if not obj or not obj.image_data:
            return 'No product image uploaded yet.'
        return format_html(
            '<div style="margin:8px 0"><a href="{}" target="_blank" rel="noopener"><img src="{}" style="max-width:360px;max-height:240px;border-radius:12px;border:1px solid #ddd;object-fit:contain;background:#f7f7f7;padding:6px;cursor:zoom-in"></a><div style="margin-top:4px;color:#666">Click image to open full size</div></div>',
            obj.image_data, obj.image_data,
        )

@admin.register(ProductGallery)
class ProductGalleryAdmin(admin.ModelAdmin):
    form=ProductGalleryForm
    list_display=('product','caption','sort_order','published','created_at')
    list_filter=('published',)
    search_fields=('product__name','caption')

@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    form=GalleryImageAdminForm
    list_display=('title','category','featured','published','sort_order','created_at')
    list_filter=('category','featured','published')
    search_fields=('title','title_hi','description')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display=('name','mobile','email','created_at')
    search_fields=('name','mobile','email')

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display=('name','mobile','gstin','created_at')
    search_fields=('name','mobile','gstin')

@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display=('name','phone','product','status','created_at')
    list_filter=('status',)
    search_fields=('name','phone','email')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=('id','name','phone','product','quantity','amount','paid_amount','payment_mode','payment_status','status','sale_link','created_at')
    list_filter=('status',)
    search_fields=('name','phone')
    list_editable=('payment_status', 'status')

    @admin.display(description='Sale')
    def sale_link(self, obj):
        return obj.sale.invoice_no if hasattr(obj, 'sale') and obj.sale else '-'

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display=('invoice_no','customer_name','product','quantity','amount','paid_amount','payment_mode','auto_generated_from_order','sale_date','profit_amount','invoice_action')
    list_filter=('payment_mode','sale_date')
    search_fields=('invoice_no','customer_name','phone')
    readonly_fields=('stock_applied_quantity','stock_applied_product_id','invoice_link')

    @admin.display(description='Invoice')
    def invoice_action(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        url = reverse('invoice_pdf', args=[obj.pk])
        return format_html('<a class="button" href="{}" target="_blank">PDF</a>', url)

    @admin.display(description='Invoice')
    def invoice_link(self, obj):
        from django.utils.html import format_html
        from django.urls import reverse
        if not obj.pk:
            return '-'
        url = reverse('invoice_pdf', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">Download Invoice PDF</a>', url)

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display=('bill_no','supplier_name','product','quantity','amount','paid_amount','payment_mode','purchase_date')
    search_fields=('bill_no','supplier_name')
    readonly_fields=('stock_applied_quantity','stock_applied_product_id')

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display=('date','category','description','amount','payment_mode')
    list_filter=('category','payment_mode','date')
    search_fields=('description',)

@admin.register(LedgerEntry)
class LedgerAdmin(admin.ModelAdmin):
    list_display=('date','entry_type','account','amount','reference')
    list_filter=('entry_type','date')
    search_fields=('account','reference','narration')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display=('title','product','discount_text','valid_until','published')
    list_filter=('published',)
    search_fields=('title','title_hi')

@admin.register(ServiceQuery)
class ServiceQueryAdmin(admin.ModelAdmin):
    list_display=('ticket_no','name','mobile','category','priority','status','created_at')
    list_filter=('status','priority','category')
    search_fields=('ticket_no','name','mobile','query')
    readonly_fields=('ticket_no','created_at','updated_at')

@admin.register(SupportQuery)
class SupportQueryAdmin(admin.ModelAdmin):
    list_display=('ticket_no','name','mobile','category','priority','status','created_at')
    list_filter=('status','priority','category')
    search_fields=('ticket_no','name','mobile','query')
    readonly_fields=('ticket_no','created_at','updated_at')

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    form=SiteSettingAdminForm
    list_display=('business_name','phone_primary','phone_secondary')


@admin.register(ProductEMIPlan)
class ProductEMIPlanAdmin(admin.ModelAdmin):
    list_display=('product','tenure_months','interest_rate','down_payment','processing_fee','monthly_emi','active','sort_order')
    list_filter=('active','tenure_months')
    search_fields=('product__name',)

    @admin.display(description='Monthly EMI')
    def monthly_emi(self, obj):
        return f'₹{obj.monthly_emi:,.2f}'
