from django.contrib import admin
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

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form=ProductAdminForm
    list_display=('name','category','segment','display_price','cost_price','stock','coming_soon','published','featured')
    list_filter=('category','coming_soon','published','featured')
    search_fields=('name','name_hi','sku','segment')
    prepopulated_fields={'slug':('name',)}

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
    list_display=('id','name','phone','product','quantity','amount','status','created_at')
    list_filter=('status',)
    search_fields=('name','phone')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display=('invoice_no','customer_name','product','quantity','amount','payment_mode','sale_date','profit_amount')
    list_filter=('payment_mode','sale_date')
    search_fields=('invoice_no','customer_name','phone')

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display=('bill_no','supplier_name','product','quantity','amount','purchase_date')
    search_fields=('bill_no','supplier_name')

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
