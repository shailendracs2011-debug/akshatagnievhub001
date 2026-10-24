from datetime import date, timedelta
from decimal import Decimal
import io, os, base64, tempfile, json, urllib.parse, hashlib
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Sum, Count, F
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, HRFlowable
from .forms import (
    EnquiryForm,
    OrderForm,
    PartRequestForm,
    SaleForm,
    ServiceQueryForm,
    SupportQueryForm,
    SiteSettingForm,
    TestRideForm,
    TrackRequestForm,
)
from .i18n import PLACEHOLDER, ui
from .images import data_url_bytes, resize_data_url
from .models import Category, Product, ProductGallery, GalleryImage, Enquiry, Order, Sale, Purchase, Expense, LedgerEntry, SiteSetting, ServiceQuery, SupportQuery, VisitorCount, FAQItem, Testimonial

# Whitelist of models whose stored image may be served as a URL.
# Each entry is (model, full-size field, thumbnail field).
IMAGE_SOURCES = {
    'product': (Product, 'image_data', 'thumb_data'),
    'productgallery': (ProductGallery, 'image_data', 'thumb_data'),
    'galleryimage': (GalleryImage, 'image_data', 'thumb_data'),
    'testimonial': (Testimonial, 'photo_data', 'thumb_data'),
}

# Site-level images that live on the single settings row.
# Each entry is a list of fields tried in order until one holds an image.
SITE_IMAGE_SOURCES = {
    'hero': ['hero_image_web', 'hero_image_data'],
    'hero-mobile': ['hero_image_mobile', 'hero_image_data'],
    'logo': ['logo_data'],
}


def settings_obj():
    obj, _ = SiteSetting.objects.get_or_create(pk=1)
    return obj


def get_lang(request):
    lang = request.session.get('lang', 'en')
    return lang if lang in ('en', 'hi') else 'en'


def whatsapp_link(site, text):
    """Build a wa.me link with the showroom number and a prefilled message."""
    number = ''.join(ch for ch in (site.whatsapp or site.phone_primary or '') if ch.isdigit())
    if not number:
        return ''
    if number.startswith('91') and len(number) > 10:
        number = number[-10:]
    elif len(number) > 10:
        number = number[-10:]
    return f'https://wa.me/{number}?text={urllib.parse.quote(text)}'


def base_context(request):
    lang = get_lang(request)
    gallery = GalleryImage.objects.filter(published=True).order_by('sort_order', '-created_at')
    obj, _ = VisitorCount.objects.get_or_create(pk=1)
    VisitorCount.objects.filter(pk=obj.pk).update(count=F('count') + 1)
    obj.refresh_from_db()
    site = settings_obj()
    default_wa = 'Hello, I would like to know about electric scooters at Akshat Agni EV Motors.' if lang == 'en' else 'नमस्ते, मुझे अक्षत अग्नि ईवी मोटर्स के बारे में जानकारी चाहिए।'
    return {
        'site': site,
        'lang': lang,
        't': ui(lang),
        'ph': PLACEHOLDER,
        'gallery_items': gallery[:8],
        'visitor_count': obj.count,
        'wa_link': whatsapp_link(site, default_wa),
        'has_eauto': Product.objects.filter(published=True, category__slug='e-auto-7-seater').exists(),
    }


def language(request, code):
    if code in ('en','hi'): request.session['lang'] = code
    return redirect(request.META.get('HTTP_REFERER') or '/')


def home(request):
    q = request.GET.get('q','').strip()
    category_slug = request.GET.get('category','').strip()
    segment = request.GET.get('segment','').strip()
    products = Product.objects.filter(published=True).select_related('category')
    if q:
        products = products.filter(Q(name__icontains=q)|Q(name_hi__icontains=q)|Q(segment__icontains=q)|Q(category__name__icontains=q)|Q(category__name_hi__icontains=q)|Q(sku__icontains=q))
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if segment:
        products = products.filter(segment=segment)
    featured = products.filter(featured=True)[:8]
    if not featured: featured = products[:8]
    cats = Category.objects.filter(published=True, parent__isnull=True).prefetch_related('children')
    offers = __import__('showroom.models', fromlist=['Offer']).Offer.objects.filter(published=True).order_by('-created_at')[:4]
    ctx = base_context(request)
    ctx.update({'products':products[:24],'featured':featured,'categories':cats,'query':q,'selected_category':category_slug,'selected_segment':segment,'offers':offers})
    ctx['testimonials'] = Testimonial.objects.filter(published=True)[:6]
    ctx['faq_items'] = list(FAQItem.objects.filter(published=True))
    # Sensible starting values for the EMI calculator, taken from real stock.
    priced = Product.objects.filter(published=True).exclude(price=0).order_by('price').first()
    ctx['emi_default_price'] = int(priced.display_price) if priced else 90000
    ctx['emi_default_down'] = int(priced.display_price * Decimal('0.2')) if priced else 18000
    return render(request,'home.html',ctx)


def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug, published=True)
    products = Product.objects.filter(published=True, category=category).select_related('category')
    segment = request.GET.get('segment','').strip()
    # Dedupe segments case/whitespace-insensitively so admin-entered variants
    # such as "Heavy Duty" and "Heavy Duty " don't repeat in the UI.
    seen = set()
    segments = []
    for s in products.exclude(segment='').values_list('segment', flat=True).distinct():
        key = s.strip().lower()
        if key and key not in seen:
            seen.add(key)
            segments.append(s)
    if segment:
        products = products.filter(segment=segment)
    ctx = base_context(request)
    ctx.update({'category': category, 'products': products, 'segments': segments, 'selected_segment': segment})
    return render(request, 'category.html', ctx)


def product_detail(request, slug):
    product=get_object_or_404(Product.objects.select_related('category'),slug=slug,published=True)
    site=settings_obj()
    ctx=base_context(request)
    ctx.update({'product':product,'gallery':product.gallery.filter(published=True),'emi_plans':product.emi_plans.filter(active=True),'related':Product.objects.filter(published=True,category=product.category).exclude(pk=product.pk)[:4]})
    ctx['wa_link'] = whatsapp_link(site, f'Hello, I want to know about {product.name}.')
    ctx['spec_rows'] = product.spec_rows()
    ctx['tr_form'] = TestRideForm(initial={'product': product})
    return render(request,'product_detail.html',ctx)


def gallery(request):
    category=request.GET.get('category','').strip()
    items=GalleryImage.objects.filter(published=True)
    if category: items=items.filter(category=category)
    ctx=base_context(request); ctx.update({'gallery_items':items,'gallery_categories':GalleryImage.CATEGORY_CHOICES,'selected_gallery_category':category})
    return render(request,'gallery.html',ctx)


def enquire(request, slug=None):
    initial={}
    if slug: initial['product']=get_object_or_404(Product,slug=slug,published=True)
    form=EnquiryForm(request.POST or None,initial=initial)
    if request.method=='POST' and form.is_valid():
        form.save(); messages.success(request,'Thank you. Our team will contact you shortly. / धन्यवाद, हमारी टीम जल्द संपर्क करेगी।'); return redirect('enquiry')
    ctx=base_context(request); ctx['form']=form; return render(request,'enquiry.html',ctx)


def test_ride(request, slug=None):
    """Book a test ride for a model."""
    product = None
    if slug:
        product = get_object_or_404(Product, slug=slug, published=True)
    initial = {'product': product} if product else {}
    form = TestRideForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.request_type = 'TEST_RIDE'
        obj.message = f'Test ride request for {obj.product.name if obj.product else "scooter"}'
        obj.save()
        ctx = base_context(request)
        ctx['product'] = product
        ctx['booked'] = obj
        return render(request, 'test_ride_success.html', ctx)
    ctx = base_context(request)
    ctx.update({'form': form, 'product': product})
    return render(request, 'test_ride.html', ctx)


def ask_part(request):
    """Ask the showroom for a spare part."""
    form = PartRequestForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.request_type = 'PART'
        vehicle_model = form.cleaned_data.get('vehicle_model') or ''
        obj.message = f'Part request ({vehicle_model}): {obj.message}'
        obj.save()
        ctx = base_context(request)
        ctx['part_request'] = obj
        return render(request, 'ask_part_success.html', ctx)
    ctx = base_context(request)
    ctx['form'] = form
    return render(request, 'ask_part.html', ctx)


def track_request(request):
    """Let a customer look up their own requests using their mobile number."""
    form = TrackRequestForm(request.POST or None)
    results = []
    searched = False
    if request.method == 'POST' and form.is_valid():
        searched = True
        phone = form.cleaned_data['phone']
        digits = phone[-10:]
        for order in Order.objects.filter(phone__contains=digits).select_related('product')[:10]:
            results.append({'kind': 'order', 'ref': f'#{order.pk}', 'date': order.created_at, 'status': order.get_status_display(),
                            'title': order.product.name if order.product else 'Order', 'meta': order.product.name if order.product else ''})
        for ticket in ServiceQuery.objects.filter(mobile__contains=digits)[:10]:
            results.append({'kind': 'service', 'ref': ticket.ticket_no, 'date': ticket.created_at, 'status': ticket.get_status_display(),
                            'title': ticket.get_category_display(), 'meta': ticket.vehicle_model})
        for ticket in SupportQuery.objects.filter(mobile__contains=digits)[:10]:
            results.append({'kind': 'support', 'ref': ticket.ticket_no, 'date': ticket.created_at, 'status': ticket.get_status_display(),
                            'title': ticket.get_category_display(), 'meta': ticket.order_number})
        for enquiry in Enquiry.objects.filter(phone__contains=digits).select_related('product')[:10]:
            results.append({'kind': 'enquiry', 'ref': f'ENQ-{enquiry.pk}', 'date': enquiry.created_at, 'status': enquiry.get_status_display(),
                            'title': enquiry.get_request_type_display(), 'meta': enquiry.product.name if enquiry.product else ''})
        results.sort(key=lambda r: r['date'], reverse=True)
    ctx = base_context(request)
    ctx.update({'form': form, 'results': results, 'searched': searched})
    return render(request, 'track_request.html', ctx)


def _data_url_response(data, cache_days=7, max_edge=None):
    """Turn a stored ``data:`` URL into a cacheable binary image response.

    ``max_edge`` lets the caller ask for a smaller copy — the browser tells us
    how many pixels it will actually paint, so a 40px logo does not need the
    640px original.
    """
    if not data or not data.startswith('data:'):
        raise Http404('Image not found')
    if max_edge:
        data = resize_data_url(data, max_edge=max_edge)
    raw, content_type = data_url_bytes(data)
    if not raw:
        raise Http404('Image not readable')
    response = HttpResponse(raw, content_type=content_type)
    response['Content-Length'] = str(len(raw))
    response['Cache-Control'] = f'public, max-age={cache_days * 86400}'
    response['ETag'] = f'"{hashlib.md5(raw).hexdigest()}"'
    return response


def _requested_edge(request, default=None):
    """Read a sane ``?w=`` width hint from the query string."""
    try:
        edge = int(request.GET.get('w', ''))
    except (TypeError, ValueError):
        return default
    if edge < 32:
        return default
    return min(edge, 2000)


def media_image(request, model_name, pk):
    """Serve a stored image as a real URL.

    Images live in the database as data URLs, which means a page that inlines
    them carries the full payload in the HTML and cannot lazy-load it. Grids
    therefore point at this endpoint — ``?t=1`` for the stored thumbnail,
    ``?w=`` for a specific pixel width — so the browser fetches each picture
    separately, lazily, and can cache it.
    """
    entry = IMAGE_SOURCES.get((model_name or '').lower())
    if not entry:
        raise Http404('Unknown image source')
    model, field, thumb_field = entry
    obj = model.objects.filter(pk=pk).first()
    if not obj:
        raise Http404('Image not found')
    data = getattr(obj, field, '') or ''
    if request.GET.get('t') and thumb_field:
        data = getattr(obj, thumb_field, '') or data
    return _data_url_response(data, max_edge=_requested_edge(request))


def media_site_image(request, name):
    """Serve a settings-row image (hero, logo) as a cacheable URL."""
    fields = SITE_IMAGE_SOURCES.get((name or '').lower())
    if not fields:
        raise Http404('Unknown image source')
    site = settings_obj()
    for field in fields:
        data = getattr(site, field, '') or ''
        if data.startswith('data:'):
            return _data_url_response(data, max_edge=_requested_edge(request))
    raise Http404('Image not found')


def compare(request):
    """Side by side comparison of up to three products."""
    raw = request.GET.get('ids', '')
    slugs = [s for s in raw.split(',') if s][:3]
    products = list(Product.objects.filter(published=True, slug__in=slugs).select_related('category'))
    order = {s: i for i, s in enumerate(slugs)}
    products.sort(key=lambda p: order.get(p.slug, 99))
    ctx = base_context(request)
    ctx.update({'products': products, 'slugs': slugs})
    return render(request, 'compare.html', ctx)


def service_enquiry(request):
    form=ServiceQueryForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(); return redirect('ticket_success',ticket=obj.ticket_no)
    ctx=base_context(request); ctx.update({'form':form,'ticket_type':'service'}); return render(request,'ticket_form.html',ctx)


def support_query(request):
    form=SupportQueryForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        obj=form.save(); return redirect('ticket_success',ticket=obj.ticket_no)
    ctx=base_context(request); ctx.update({'form':form,'ticket_type':'support'}); return render(request,'ticket_form.html',ctx)


def ticket_success(request,ticket):
    obj=ServiceQuery.objects.filter(ticket_no=ticket).first() or SupportQuery.objects.filter(ticket_no=ticket).first()
    ctx=base_context(request); ctx['ticket']=obj; ctx['ticket_type']='service' if ticket.startswith('AA-SRV') else 'support'; return render(request,'ticket_success.html',ctx)


def book_order(request,slug):
    product=get_object_or_404(Product,slug=slug,published=True)
    form=OrderForm(request.POST or None, product=product)
    if request.method=='POST' and form.is_valid():
        order=form.save(commit=False); order.product=product
        try: order.quantity=max(1,int(request.POST.get('quantity','1')))
        except ValueError: order.quantity=1
        order.amount=product.display_price*order.quantity
        order.paid_amount=min(order.amount, max(Decimal('0'), order.paid_amount or Decimal('0')))
        if order.paid_amount >= order.amount and order.amount > 0:
            order.payment_status='PAID'
        elif order.paid_amount > 0:
            order.payment_status='PARTIAL'
        order.save()
        return redirect('order_success',pk=order.pk)
    ctx=base_context(request); ctx.update({'form':form,'product':product}); return render(request,'book_order.html',ctx)


def order_success(request,pk):
    order=get_object_or_404(Order,pk=pk); ctx=base_context(request); ctx['order']=order; return render(request,'order_success.html',ctx)


class ERPLoginView(LoginView):
    template_name='erp/login.html'; redirect_authenticated_user=True
class ERPLogoutView(LogoutView): pass


def _period(request):
    today=date.today(); start_s=request.GET.get('from',''); end_s=request.GET.get('to','')
    try: start=date.fromisoformat(start_s) if start_s else today.replace(day=1)
    except ValueError: start=today.replace(day=1)
    try: end=date.fromisoformat(end_s) if end_s else today
    except ValueError: end=today
    return start,end


@staff_member_required
def erp_dashboard(request):
    start,end=_period(request)
    sales=Sale.objects.filter(sale_date__range=(start,end)); purchases=Purchase.objects.filter(purchase_date__range=(start,end)); expenses=Expense.objects.filter(date__range=(start,end)); ledger=LedgerEntry.objects.filter(date__range=(start,end))
    sales_total=sales.aggregate(v=Sum('amount'))['v'] or Decimal('0'); purchase_total=purchases.aggregate(v=Sum('amount'))['v'] or Decimal('0'); expense_total=expenses.aggregate(v=Sum('amount'))['v'] or Decimal('0'); credit=ledger.filter(entry_type='CREDIT').aggregate(v=Sum('amount'))['v'] or Decimal('0'); debit=ledger.filter(entry_type='DEBIT').aggregate(v=Sum('amount'))['v'] or Decimal('0')
    cogs=Decimal('0')
    for s in sales.select_related('product'): cogs += Decimal(s.cost_amount)
    gross=sales_total-cogs; net=gross-expense_total
    cat_data=list(sales.values('product__category__name').annotate(total=Sum('amount')).order_by('-total')[:8])
    model_data=list(sales.values('product__name').annotate(total=Sum('amount')).order_by('-total')[:8])
    monthly=[]
    cursor=start.replace(day=1)
    while cursor<=end:
        if cursor.month==12: nxt=cursor.replace(year=cursor.year+1,month=1,day=1)
        else: nxt=cursor.replace(month=cursor.month+1,day=1)
        monthly.append({'label':cursor.strftime('%b %Y'),'sales':sales.filter(sale_date__gte=cursor,sale_date__lt=nxt).aggregate(v=Sum('amount'))['v'] or 0,'purchases':purchases.filter(purchase_date__gte=cursor,purchase_date__lt=nxt).aggregate(v=Sum('amount'))['v'] or 0})
        cursor=nxt
    ctx={'start':start,'end':end,'sales_total':sales_total,'purchase_total':purchase_total,'expense_total':expense_total,'gross_profit':gross,'net_profit':net,'credit':credit,'debit':debit,'stock_units':Product.objects.aggregate(v=Sum('stock'))['v'] or 0,'product_count':Product.objects.count(),'order_count':Order.objects.count(),'enquiry_count':Enquiry.objects.filter(created_at__date__range=(start,end)).count(),'service_count':ServiceQuery.objects.filter(created_at__date__range=(start,end)).count(),'support_count':SupportQuery.objects.filter(created_at__date__range=(start,end)).count(),'open_service':ServiceQuery.objects.exclude(status__in=['RESOLVED','CLOSED']).count(),'open_support':SupportQuery.objects.exclude(status__in=['RESOLVED','CLOSED']).count(),'cat_data':json.dumps(cat_data, default=str),'model_data':json.dumps(model_data, default=str),'monthly':json.dumps(monthly, default=str),'recent_orders':Order.objects.select_related('product')[:7],'recent_services':ServiceQuery.objects.all()[:5]}
    return render(request,'erp/dashboard.html',ctx)


@staff_member_required
def erp_table(request, title, rows, kind): return render(request,'erp/table.html',{'title':title,'rows':rows,'kind':kind})
@staff_member_required
def erp_sales(request): return erp_table(request,'Sales',Sale.objects.select_related('product','customer').all(),'sales')


@staff_member_required
def erp_add_sale(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            if not sale.invoice_no:
                sale.invoice_no = _next_invoice_no()
            sale.save()
            messages.success(request, f'Sale {sale.invoice_no} recorded.')
            return redirect('erp_sales')
    else:
        form = SaleForm()
    ctx = base_context(request); ctx.update({'form': form, 'title': 'Add Sale'})
    return render(request, 'erp/add_sell.html', ctx)


@staff_member_required
def erp_edit_sale(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, f'Sale {sale.invoice_no} updated.')
            return redirect('erp_sales')
    else:
        form = SaleForm(instance=sale)
    ctx = base_context(request); ctx.update({'form': form, 'title': 'Edit Sale', 'sale': sale})
    return render(request, 'erp/add_sell.html', ctx)


@staff_member_required
def erp_customer_json(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return JsonResponse({'name': customer.name, 'phone': customer.mobile, 'email': customer.email or '', 'address': customer.address or ''})


@staff_member_required
def erp_order_json(request, pk):
    order = get_object_or_404(Order.objects.select_related('product'), pk=pk)
    return JsonResponse({
        'name': order.name,
        'phone': order.phone,
        'email': order.email or '',
        'address': order.address or '',
        'product_id': order.product.pk if order.product else '',
        'product': order.product.name if order.product else '',
        'quantity': order.quantity,
        'amount': str(order.amount),
        'payment_mode': order.payment_mode,
    })


def _next_invoice_no():
    today = date.today()
    prefix = f'INV-{today:%y%m%d}-'
    n = Sale.objects.filter(invoice_no__startswith=prefix).count() + 1
    return f'{prefix}{n:04d}'


@staff_member_required
def erp_purchases(request): return erp_table(request,'Purchases',Purchase.objects.select_related('product','supplier').all(),'purchases')
@staff_member_required
def erp_inventory(request): return render(request,'erp/inventory.html',{'products':Product.objects.select_related('category').all()})
@staff_member_required
def erp_orders(request): return erp_table(request,'Online Bookings',Order.objects.select_related('product').all(),'orders')
@staff_member_required
def erp_enquiries(request): return erp_table(request,'Customer Enquiries',Enquiry.objects.select_related('product').all(),'enquiries')
@staff_member_required
def erp_activities(request): return erp_table(request,'Website Gallery',GalleryImage.objects.all(),'activities')
@staff_member_required
def erp_service(request): return erp_table(request,'Service Enquiries',ServiceQuery.objects.all(),'service')
@staff_member_required
def erp_support(request): return erp_table(request,'Support Queries',SupportQuery.objects.all(),'support')
@staff_member_required
def erp_ledger(request):
    entries=LedgerEntry.objects.all(); credit=entries.filter(entry_type='CREDIT').aggregate(v=Sum('amount'))['v'] or 0; debit=entries.filter(entry_type='DEBIT').aggregate(v=Sum('amount'))['v'] or 0
    return render(request,'erp/ledger.html',{'entries':entries,'credit':credit,'debit':debit,'balance':Decimal(str(credit))-Decimal(str(debit))})
@staff_member_required
def erp_reports(request):
    start,end=_period(request); sales=Sale.objects.filter(sale_date__range=(start,end)); purchases=Purchase.objects.filter(purchase_date__range=(start,end)); expenses=Expense.objects.filter(date__range=(start,end)); sales_total=sales.aggregate(v=Sum('amount'))['v'] or 0; purchase_total=purchases.aggregate(v=Sum('amount'))['v'] or 0; expense_total=expenses.aggregate(v=Sum('amount'))['v'] or 0
    return render(request,'erp/reports.html',{'start':start,'end':end,'sales':sales_total,'purchases':purchase_total,'expenses':expense_total,'net':Decimal(str(sales_total))-Decimal(str(purchase_total))-Decimal(str(expense_total)),'sales_count':sales.count(),'purchase_count':purchases.count()})


@staff_member_required
def erp_settings(request):
    obj = settings_obj()
    if request.method == 'POST':
        form = SiteSettingForm(request.POST, request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company settings saved successfully.')
            return redirect('erp_settings')
    else:
        form = SiteSettingForm(instance=obj)
    return render(request, 'erp/settings.html', {'form': form, 'title': 'Company Settings'})


def _load_data_url_image(site_data_url):
    """Convert a base64 data URL to a temp image file path (or None)."""
    if not site_data_url or not site_data_url.startswith('data:'):
        return None
    try:
        from PIL import Image
        import io as _io
        header, data = site_data_url.split(',', 1)
        raw = base64.b64decode(data)
        img = Image.open(_io.BytesIO(raw))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        fd, path = tempfile.mkstemp(suffix='.jpg', dir=tempfile.gettempdir())
        with os.fdopen(fd, 'wb') as f:
            img.save(f, 'JPEG', quality=90)
        return path
    except Exception:
        return None


def _cleanup_temp(path):
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def build_invoice_pdf(sale, request):
    """Build a full-page invoice PDF for a Sale as bytes."""
    site = settings_obj()
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm, topMargin=14*mm, bottomMargin=14*mm,
        title=f'Invoice {sale.invoice_no}',
        author=site.business_name or 'Akshat Agni EV Motors',
    )
    styles = getSampleStyleSheet()
    story = []

    def P(text, style='Normal', **kw):
        st = ParagraphStyle('tmp', parent=styles[style], **kw)
        return Paragraph(text, st)

    # ---------- Header: logo + company ----------
    logo_path = _load_data_url_image(site.logo_data)
    logo_cell = ''
    if logo_path:
        logo_cell = RLImage(logo_path, width=52*mm, height=26*mm, kind='proportional')

    company_lines = []
    if site.business_name:
        company_lines.append(f'<b>{site.business_name}</b>')
    if site.address:
        company_lines.append(site.address)
    contact_bits = []
    if site.phone_primary:
        contact_bits.append(f'Ph: {site.phone_primary}')
    if site.phone_secondary:
        contact_bits.append(f'/{site.phone_secondary}')
    if site.gst_number:
        contact_bits.append(f'GSTIN: {site.gst_number}')
    if site.website:
        contact_bits.append(site.website)
    if contact_bits:
        company_lines.append(' | '.join(contact_bits))
    if site.authorized_person:
        company_lines.append(f'Authorised Person: {site.authorized_person}')

    header_data = [[logo_cell, P('<br/>'.join(company_lines) if company_lines else 'Akshat Agni EV Motors', 'Normal', alignment=TA_RIGHT)]]
    header_t = Table(header_data, colWidths=[60*mm, 130*mm])
    header_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(header_t)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width='100%', thickness=1.4, color=colors.HexColor('#0b6b43')))
    story.append(Spacer(1, 10))

    # ---------- Invoice meta ----------
    payment_status = getattr(getattr(sale, 'order', None), 'payment_status', '') or ''
    meta_data = [
        [P('<b>Invoice No:</b>', 'Normal'), P(sale.invoice_no, 'Normal'),
         P('<b>Date:</b>', 'Normal'), P(sale.sale_date.strftime('%d %b %Y') if sale.sale_date else '', 'Normal')],
        [P('<b>Payment Mode:</b>', 'Normal'), P(sale.payment_mode, 'Normal'),
         P('<b>Payment Status:</b>', 'Normal'), P(payment_status.title() if payment_status else '', 'Normal')],
        [P('<b>Invoice Code:</b>', 'Normal'), P(sale.invoice_code or '-', 'Normal'),
         P('<b>Verify:</b>', 'Normal'), P('Online', 'Normal')],
    ]
    meta_t = Table(meta_data, colWidths=[32*mm, 50*mm, 32*mm, 76*mm])
    meta_t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce8e1')),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f7f5')),
        ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#f3f7f5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_t)
    story.append(Spacer(1, 10))

    # ---------- Bill To / Ship To ----------
    bill_lines = [f'<b>{sale.customer_name}</b>']
    if sale.billing_address:
        bill_lines.append(sale.billing_address.replace('\n', '<br/>'))
    elif sale.customer and sale.customer.address:
        bill_lines.append(sale.customer.address.replace('\n', '<br/>'))
    if sale.phone:
        bill_lines.append(f'Phone: {sale.phone}')
    if sale.email:
        bill_lines.append(f'Email: {sale.email}')

    ship_lines = [f'<b>{sale.customer_name}</b>']
    if sale.shipping_address:
        ship_lines.append(sale.shipping_address.replace('\n', '<br/>'))
    elif sale.customer and sale.customer.address:
        ship_lines.append(sale.customer.address.replace('\n', '<br/>'))
    if sale.phone:
        ship_lines.append(f'Phone: {sale.phone}')

    addr_data = [
        [P('<b>BILL TO</b>', 'Normal'), P('<b>SHIP TO</b>', 'Normal')],
        [P('<br/>'.join(bill_lines), 'Normal'), P('<br/>'.join(ship_lines), 'Normal')],
    ]
    addr_t = Table(addr_data, colWidths=[93*mm, 97*mm])
    addr_t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce8e1')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f7f5')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(addr_t)
    story.append(Spacer(1, 10))

    # ---------- Product table ----------
    product_name = sale.product.name if sale.product else '-'
    prod_data = [
        [P('<b>#</b>', 'Normal'), P('<b>Product</b>', 'Normal'), P('<b>Qty</b>', 'Normal'),
         P('<b>MRP</b>', 'Normal'), P('<b>Discount</b>', 'Normal'), P('<b>GST</b>', 'Normal'),
         P('<b>Amount</b>', 'Normal')],
        [P('1', 'Normal'), P(product_name, 'Normal'), P(str(sale.quantity), 'Normal'),
         P(f"₹{sale.mrp_amount:.2f}", 'Normal'), P(f"₹{sale.discount_amount:.2f}", 'Normal'),
         P(f"₹{sale.gst_amount:.2f}", 'Normal'), P(f"₹{sale.amount:.2f}", 'Normal')],
    ]
    prod_t = Table(prod_data, colWidths=[12*mm, 62*mm, 14*mm, 22*mm, 22*mm, 22*mm, 36*mm], repeatRows=1)
    prod_t.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dce8e1')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f7f5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(prod_t)
    story.append(Spacer(1, 10))

    # ---------- Totals ----------
    subtotal = sale.amount
    totals_data = [
        [P('<b>Subtotal</b>', 'Normal'), P(f"₹{subtotal:.2f}", 'Normal')],
        [P('<b>GST Amount</b>', 'Normal'), P(f"₹{sale.gst_amount:.2f}", 'Normal')],
        [P('<b>Paid Amount</b>', 'Normal'), P(f"₹{sale.paid_amount:.2f}", 'Normal')],
        [P('<b>Balance Due</b>', 'Normal'), P(f"₹{sale.balance_amount:.2f}", 'Normal')],
    ]
    totals_t = Table(totals_data, colWidths=[160*mm, 30*mm])
    totals_t.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
        ('LINEABOVE', (1, -1), (1, -1), 1, colors.HexColor('#0b6b43')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(totals_t)
    story.append(Spacer(1, 14))

    # ---------- Footer: QR + signature ----------
    verify_url = request.build_absolute_uri(reverse('invoice_verify', args=[sale.invoice_code])) if sale.invoice_code else ''
    qr_flowable = ''
    if verify_url:
        try:
            from reportlab.graphics.barcode.qr import QrCodeWidget
            from reportlab.graphics.shapes import Drawing
            qr_widget = QrCodeWidget(verify_url)
            qr_widget.barLevel = 'H'
            qr_size = 28*mm
            qr_drawing = Drawing(qr_size, qr_size)
            qr_widget.barWidth = qr_size / qr_widget.size
            qr_drawing.add(qr_widget)
            qr_flowable = qr_drawing
        except Exception:
            qr_flowable = P('Verify online', 'Normal')

    qr_note = P(f'Scan to verify invoice online<br/><font size="7">{verify_url}</font>', 'Normal', fontSize=7, leading=9) if verify_url else ''

    sig_path = _load_data_url_image(site.signature_data)
    sig_cell = ''
    if sig_path:
        sig_cell = RLImage(sig_path, width=42*mm, height=18*mm, kind='proportional')
    sig_lines = []
    if site.signatory_name:
        sig_lines.append(f'<b>{site.signatory_name}</b>')
    if site.authorized_person:
        sig_lines.append(f'Authorised Person: {site.authorized_person}')
    sig_text = P('<br/>'.join(sig_lines) if sig_lines else 'Authorized Signatory', 'Normal', fontSize=8)

    footer_data = [[qr_flowable, qr_note], [sig_cell, sig_text]]
    footer_t = Table(footer_data, colWidths=[85*mm, 105*mm])
    footer_t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(footer_t)
    story.append(Spacer(1, 8))
    story.append(P(f'<font size="6.5" color="#718078">Generated by {site.business_name or "Akshat Agni EV Motors"} | Invoice {sale.invoice_no}</font>', 'Normal'))

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf


@staff_member_required
def invoice_pdf(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('product', 'customer', 'order'), pk=pk)
    pdf = build_invoice_pdf(sale, request)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="invoice-{sale.invoice_no}.pdf"'
    return resp


def invoice_verify(request, code):
    """Public view: serve invoice PDF by system-generated invoice code (QR target)."""
    sale = get_object_or_404(Sale.objects.select_related('product', 'customer', 'order'), invoice_code=code)
    pdf = build_invoice_pdf(sale, request)
    resp = HttpResponse(pdf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="invoice-{sale.invoice_no}.pdf"'
    return resp


def _export_excel(filename, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Sheet1'
    ws.append(headers)
    for row in rows:
        ws.append(row)
    resp = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(resp)
    return resp


@staff_member_required
def export_sales_excel(request):
    rows = []
    for s in Sale.objects.select_related('product').order_by('-sale_date','-id'):
        rows.append([s.invoice_no, s.sale_date, s.customer_name, s.phone, s.product.name if s.product else '', s.quantity, float(s.amount), s.payment_mode])
    return _export_excel('akshat-agni-sales.xlsx', ['Invoice','Date','Customer','Phone','Product','Qty','Amount','Payment'], rows)


@staff_member_required
def export_purchases_excel(request):
    rows = []
    for p in Purchase.objects.select_related('product').order_by('-purchase_date','-id'):
        rows.append([p.bill_no, p.purchase_date, p.supplier_name, p.product.name if p.product else '', p.quantity, float(p.amount), p.payment_mode])
    return _export_excel('akshat-agni-purchases.xlsx', ['Bill','Date','Supplier','Product','Qty','Amount','Payment'], rows)


@staff_member_required
def export_orders_excel(request):
    rows = []
    for o in Order.objects.select_related('product').order_by('-created_at','-id'):
        rows.append([o.id, o.created_at.date(), o.name, o.phone, o.product.name if o.product else '', o.quantity, float(o.amount), o.payment_mode, o.payment_status, o.status])
    return _export_excel('akshat-agni-orders.xlsx', ['#','Date','Customer','Phone','Product','Qty','Amount','Payment','Payment Status','Status'], rows)


@staff_member_required
def export_enquiries_excel(request):
    rows = []
    for e in Enquiry.objects.select_related('product').order_by('-created_at','-id'):
        rows.append([e.created_at.date(), e.name, e.phone, e.product.name if e.product else '', e.status, e.message])
    return _export_excel('akshat-agni-enquiries.xlsx', ['Date','Name','Phone','Product','Status','Message'], rows)


@staff_member_required
def export_activities_excel(request):
    rows = []
    for a in GalleryImage.objects.all().order_by('-created_at','-id'):
        rows.append([a.title, a.get_category_display(), 'Yes' if a.featured else 'No', 'Yes' if a.published else 'No', a.sort_order])
    return _export_excel('akshat-agni-gallery.xlsx', ['Title','Category','Featured','Published','Sort Order'], rows)


@staff_member_required
def export_service_excel(request):
    rows = []
    for s in ServiceQuery.objects.all().order_by('-created_at','-id'):
        rows.append([s.ticket_no, s.created_at.date(), s.name, s.mobile, s.get_category_display(), s.get_priority_display(), s.get_status_display(), s.query])
    return _export_excel('akshat-agni-service.xlsx', ['Ticket','Date','Name','Mobile','Category','Priority','Status','Query'], rows)


@staff_member_required
def export_support_excel(request):
    rows = []
    for s in SupportQuery.objects.all().order_by('-created_at','-id'):
        rows.append([s.ticket_no, s.created_at.date(), s.name, s.mobile, s.get_category_display(), s.get_priority_display(), s.get_status_display(), s.query, s.order_number])
    return _export_excel('akshat-agni-support.xlsx', ['Ticket','Date','Name','Mobile','Category','Priority','Status','Query','Order Number'], rows)


@staff_member_required
def export_ledger_excel(request):
    rows = []
    for e in LedgerEntry.objects.all().order_by('-date','-id'):
        rows.append([e.date, e.get_entry_type_display(), e.account, e.reference, float(e.amount), e.narration])
    return _export_excel('akshat-agni-ledger.xlsx', ['Date','Type','Account','Reference','Amount','Narration'], rows)


@staff_member_required
def export_inventory_excel(request):
    rows = []
    for p in Product.objects.select_related('category').all().order_by('name'):
        rows.append([p.name, p.category.name if p.category else '', p.segment, p.sku, p.stock, float(p.price), float(p.display_price), 'Yes' if p.emi_enabled else 'No', 'Coming Soon' if p.coming_soon else ('Published' if p.published else 'Hidden')])
    return _export_excel('akshat-agni-inventory.xlsx', ['Model','Category','Segment','SKU','Stock','MRP','Offer Price','EMI','State'], rows)


@staff_member_required
def export_reports_excel(request):
    start, end = _period(request)
    sales = Sale.objects.filter(sale_date__range=(start, end))
    purchases = Purchase.objects.filter(purchase_date__range=(start, end))
    expenses = Expense.objects.filter(date__range=(start, end))
    sales_total = sales.aggregate(v=Sum('amount'))['v'] or 0
    purchase_total = purchases.aggregate(v=Sum('amount'))['v'] or 0
    expense_total = expenses.aggregate(v=Sum('amount'))['v'] or 0
    net = Decimal(str(sales_total)) - Decimal(str(purchase_total)) - Decimal(str(expense_total))
    rows = [
        ['Period From', start.isoformat()],
        ['Period To', end.isoformat()],
        ['Sales Total', float(sales_total)],
        ['Purchase Total', float(purchase_total)],
        ['Expense Total', float(expense_total)],
        ['Net Profit/Loss', float(net)],
        ['Sales Count', sales.count()],
        ['Purchase Count', purchases.count()],
        ['Expense Count', expenses.count()],
    ]
    return _export_excel('akshat-agni-reports.xlsx', ['Metric','Value'], rows)
