from datetime import date, timedelta
from decimal import Decimal
import json
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q, Sum, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from openpyxl import Workbook
from xhtml2pdf import pisa
from django.template.loader import render_to_string
from .forms import EnquiryForm, OrderForm, ServiceQueryForm, SupportQueryForm, SiteSettingForm
from .models import Category, Product, ProductGallery, GalleryImage, Enquiry, Order, Sale, Purchase, Expense, LedgerEntry, SiteSetting, ServiceQuery, SupportQuery


def settings_obj():
    obj, _ = SiteSetting.objects.get_or_create(pk=1)
    return obj


def get_lang(request):
    lang = request.session.get('lang', 'en')
    return lang if lang in ('en', 'hi') else 'en'


def base_context(request):
    lang = get_lang(request)
    gallery = GalleryImage.objects.filter(published=True).order_by('sort_order', '-created_at')
    return {'site': settings_obj(), 'lang': lang, 'gallery_items': gallery[:8]}


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
    return render(request,'home.html',ctx)


def category_page(request, slug):
    category = get_object_or_404(Category, slug=slug, published=True)
    products = Product.objects.filter(published=True, category=category).select_related('category')
    segment = request.GET.get('segment','').strip()
    if segment: products = products.filter(segment=segment)
    segments = products.exclude(segment='').values_list('segment', flat=True).distinct()
    ctx=base_context(request); ctx.update({'category':category,'products':products,'segments':segments,'selected_segment':segment})
    return render(request,'category.html',ctx)


def product_detail(request, slug):
    product=get_object_or_404(Product.objects.select_related('category'),slug=slug,published=True)
    ctx=base_context(request); ctx.update({'product':product,'gallery':product.gallery.filter(published=True),'emi_plans':product.emi_plans.filter(active=True),'related':Product.objects.filter(published=True,category=product.category).exclude(pk=product.pk)[:4]})
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


@staff_member_required
def invoice_pdf(request, pk):
    sale = get_object_or_404(Sale.objects.select_related('product', 'customer', 'order'), pk=pk)
    site = settings_obj()

    def _pdf_image_callback(uri, rel):
        if uri.startswith('data:'):
            try:
                import base64, tempfile, os
                from PIL import Image
                import io
                header, data = uri.split(',', 1)
                img = Image.open(io.BytesIO(base64.b64decode(data)))
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                fd, path = tempfile.mkstemp(suffix='.jpg')
                with os.fdopen(fd, 'wb') as f:
                    img.save(f, 'JPEG', quality=90)
                return path
            except Exception:
                return None
        return uri

    context = {
        'sale': sale,
        'site': site,
        'request': request,
    }
    html = render_to_string('erp/invoice.html', context)
    resp = HttpResponse(content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="invoice-{sale.invoice_no}.pdf"'
    pisa.CreatePDF(html, dest=resp, link_callback=_pdf_image_callback)
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
