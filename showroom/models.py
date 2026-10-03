from decimal import Decimal

from django.db import models
from django.utils.text import slugify


class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True


class Category(TimeStamped):
    name = models.CharField(max_length=120)
    name_hi = models.CharField(max_length=120, blank=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
    description = models.TextField(blank=True)
    description_hi = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    published = models.BooleanField(default=True)

    class Meta:
        ordering = ['sort_order', 'name']
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'category'
            candidate, i = base, 2
            while Category.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base}-{i}'; i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.parent.name} / {self.name}' if self.parent else self.name


class Product(TimeStamped):
    name = models.CharField(max_length=180)
    name_hi = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL, related_name='products')
    segment = models.CharField(max_length=100, blank=True, help_text='Example: Single Light, Double Light, High Range, City Ride')
    short_description = models.CharField(max_length=250, blank=True)
    short_description_hi = models.CharField(max_length=250, blank=True)
    description = models.TextField(blank=True)
    description_hi = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    offer_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    featured = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    coming_soon = models.BooleanField(default=False)
    image_data = models.TextField(blank=True)
    sku = models.CharField(max_length=60, blank=True)
    battery = models.CharField(max_length=120, blank=True)
    range_text = models.CharField(max_length=120, blank=True)
    warranty = models.CharField(max_length=120, blank=True)
    motor_power = models.CharField(max_length=80, blank=True)
    top_speed = models.CharField(max_length=80, blank=True)
    charging_time = models.CharField(max_length=80, blank=True)
    seating_capacity = models.CharField(max_length=80, blank=True)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    booking_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    emi_enabled = models.BooleanField(default=False)

    class Meta:
        ordering = ['-featured', 'name']
        indexes = [models.Index(fields=['published', 'category']), models.Index(fields=['slug'])]

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or 'product'
            candidate, i = base, 2
            while Product.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f'{base}-{i}'; i += 1
            self.slug = candidate
        super().save(*args, **kwargs)

    @property
    def display_price(self):
        return self.offer_price if self.offer_price is not None else self.price

    @property
    def category_name(self):
        return self.category.name if self.category else ''

    @property
    def discount_amount(self):
        if self.offer_price is None or self.price <= 0:
            return Decimal('0')
        return max(Decimal('0'), self.price - self.offer_price)

    @property
    def discount_percent(self):
        if self.price <= 0 or self.offer_price is None:
            return Decimal('0')
        return (self.discount_amount / self.price * Decimal('100')).quantize(Decimal('0.01'))

    def __str__(self):
        return self.name


class ProductEMIPlan(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='emi_plans')
    tenure_months = models.PositiveIntegerField(default=12)
    interest_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0, help_text='Annual interest rate in percent')
    down_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'tenure_months']

    def __str__(self):
        return f'{self.product.name} - {self.tenure_months} months'

    @property
    def principal(self):
        return max(Decimal('0'), self.product.display_price - self.down_payment)

    @property
    def monthly_emi(self):
        principal = self.principal
        months = int(self.tenure_months or 0)
        annual = Decimal(self.interest_rate or 0)
        if months <= 0:
            return Decimal('0')
        if annual <= 0:
            return (principal / Decimal(months)).quantize(Decimal('0.01'))
        monthly_rate = annual / Decimal('1200')
        factor = (Decimal('1') + monthly_rate) ** months
        emi = principal * monthly_rate * factor / (factor - Decimal('1'))
        return emi.quantize(Decimal('0.01'))


class ProductGallery(TimeStamped):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')
    caption = models.CharField(max_length=150, blank=True)
    image_data = models.TextField()
    sort_order = models.PositiveIntegerField(default=0)
    published = models.BooleanField(default=True)
    def __str__(self): return f'{self.product.name} - image'
    class Meta: ordering = ['sort_order', '-created_at']


class GalleryImage(TimeStamped):
    CATEGORY_CHOICES = [
        ('SHOWROOM', 'Showroom'), ('OPENING', 'Opening'), ('EVENT', 'Event'),
        ('DELIVERY', 'Customer Delivery'), ('OFFER', 'Offer'), ('SERVICE', 'Service'), ('OTHER', 'Other')
    ]
    title = models.CharField(max_length=180)
    title_hi = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    description_hi = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='SHOWROOM')
    image_data = models.TextField()
    published = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    def __str__(self): return self.title
    class Meta: ordering = ['sort_order', '-created_at']


class Customer(TimeStamped):
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return f'{self.name} - {self.mobile}'


class Supplier(TimeStamped):
    name = models.CharField(max_length=180)
    mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=30, blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name


class Enquiry(TimeStamped):
    STATUS_CHOICES = [('NEW','New'),('CONTACTED','Contacted'),('CONVERTED','Converted'),('CLOSED','Closed')]
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    def __str__(self): return f'{self.name} - {self.phone}'


class Order(TimeStamped):
    STATUS_CHOICES = [('BOOKED','Booked'),('CONFIRMED','Confirmed'),('READY','Ready'),('DELIVERED','Delivered'),('COMPLETED','Completed'),('CANCELLED','Cancelled')]
    PAYMENT_CHOICES = [('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit'),('EMI','EMI')]
    PAYMENT_STATUS_CHOICES = [('PENDING','Pending'),('PARTIAL','Partially Paid'),('PAID','Paid')]
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    emi_plan = models.ForeignKey('ProductEMIPlan', null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mrp_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges_description = models.CharField(max_length=250, blank=True)
    payment_mode = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='Cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    @property
    def balance_amount(self):
        return max(Decimal('0'), self.amount - self.paid_amount)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BOOKED')
    def __str__(self): return f'Order #{self.pk} - {self.name}'


class Sale(TimeStamped):
    PAYMENT_CHOICES = [('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit'),('EMI','EMI')]
    invoice_no = models.CharField(max_length=50, unique=True)
    order = models.OneToOneField('Order', null=True, blank=True, on_delete=models.SET_NULL, related_name='sale')
    auto_generated_from_order = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mrp_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    processing_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_charges_description = models.CharField(max_length=250, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='Cash')
    sale_date = models.DateField()
    notes = models.TextField(blank=True)
    stock_applied_quantity = models.PositiveIntegerField(default=0, editable=False)
    stock_applied_product_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    @property
    def balance_amount(self): return max(Decimal('0'), self.amount - self.paid_amount)

    @property
    def cost_amount(self): return (self.product.cost_price * self.quantity) if self.product else 0
    @property
    def profit_amount(self): return self.amount - self.cost_amount
    def __str__(self): return self.invoice_no


class Purchase(TimeStamped):
    PAYMENT_CHOICES = [('Cash','Cash'),('UPI','UPI'),('Card','Card'),('Bank','Bank Transfer'),('Credit','Credit')]
    bill_no = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True, on_delete=models.SET_NULL)
    supplier_name = models.CharField(max_length=150)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.SET_NULL)
    quantity = models.PositiveIntegerField(default=1)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_mode = models.CharField(max_length=30, choices=PAYMENT_CHOICES, default='Cash')
    purchase_date = models.DateField()
    notes = models.TextField(blank=True)
    stock_applied_quantity = models.PositiveIntegerField(default=0, editable=False)
    stock_applied_product_id = models.PositiveBigIntegerField(null=True, blank=True, editable=False)
    def __str__(self): return self.bill_no


class Expense(TimeStamped):
    CATEGORY_CHOICES = [('Rent','Rent'),('Salary','Salary'),('Transport','Transport'),('Electricity','Electricity'),('Marketing','Marketing'),('Repair','Repair'),('Other','Other')]
    date = models.DateField()
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default='Other')
    description = models.CharField(max_length=220)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_mode = models.CharField(max_length=30, default='Cash')
    def __str__(self): return f'{self.date} - {self.description}'


class LedgerEntry(TimeStamped):
    ENTRY_CHOICES = [('CREDIT','Credit'),('DEBIT','Debit')]
    date = models.DateField()
    entry_type = models.CharField(max_length=10, choices=ENTRY_CHOICES)
    account = models.CharField(max_length=150)
    reference = models.CharField(max_length=100, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    narration = models.TextField(blank=True)
    def __str__(self): return f'{self.date} - {self.account}'


class Offer(TimeStamped):
    title = models.CharField(max_length=180)
    title_hi = models.CharField(max_length=180, blank=True)
    description = models.TextField(blank=True)
    description_hi = models.TextField(blank=True)
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.CASCADE, related_name='offers')
    discount_text = models.CharField(max_length=100, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    image_data = models.TextField(blank=True)
    published = models.BooleanField(default=True)
    def __str__(self): return self.title


class ServiceQuery(TimeStamped):
    STATUS_CHOICES = [('NEW','New'),('ASSIGNED','Assigned'),('IN_PROGRESS','In Progress'),('WAITING','Waiting for Customer'),('RESOLVED','Resolved'),('CLOSED','Closed')]
    PRIORITY_CHOICES = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('URGENT','Urgent')]
    CATEGORY_CHOICES = [('GENERAL','General Service'),('REPAIR','Repair'),('BATTERY','Battery'),('CHARGER','Charger'),('MOTOR','Motor'),('ELECTRICAL','Electrical'),('WARRANTY','Warranty'),('SPARES','Spare Parts'),('OTHER','Other')]
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=30)
    query = models.TextField(blank=True)  # optional by requirement
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='GENERAL')
    vehicle_model = models.CharField(max_length=150, blank=True)
    preferred_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    ticket_no = models.CharField(max_length=30, unique=True, blank=True)
    internal_notes = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.ticket_no:
            super().save(*args, **kwargs); self.ticket_no = f'AA-SRV-{self.pk:06d}'; return super().save(update_fields=['ticket_no'])
        super().save(*args, **kwargs)
    def __str__(self): return self.ticket_no or self.name


class SupportQuery(TimeStamped):
    STATUS_CHOICES = [('NEW','New'),('ASSIGNED','Assigned'),('IN_PROGRESS','In Progress'),('WAITING','Waiting for Customer'),('RESOLVED','Resolved'),('CLOSED','Closed')]
    PRIORITY_CHOICES = [('LOW','Low'),('MEDIUM','Medium'),('HIGH','High'),('URGENT','Urgent')]
    CATEGORY_CHOICES = [('PRODUCT','Product Information'),('ORDER','Order / Booking'),('PAYMENT','Payment'),('DELIVERY','Delivery'),('WARRANTY','Warranty'),('SERVICE','Service'),('SPARES','Spare Parts'),('COMPLAINT','Complaint'),('OTHER','Other')]
    name = models.CharField(max_length=150)
    mobile = models.CharField(max_length=30)
    query = models.TextField(blank=True)  # optional by requirement
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='PRODUCT')
    order_number = models.CharField(max_length=50, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    ticket_no = models.CharField(max_length=30, unique=True, blank=True)
    internal_notes = models.TextField(blank=True)
    def save(self, *args, **kwargs):
        if not self.ticket_no:
            super().save(*args, **kwargs); self.ticket_no = f'AA-SUP-{self.pk:06d}'; return super().save(update_fields=['ticket_no'])
        super().save(*args, **kwargs)
    def __str__(self): return self.ticket_no or self.name


class SiteSetting(TimeStamped):
    business_name = models.CharField(max_length=180, default='Akshat Agni EV Motors')
    tagline = models.CharField(max_length=250, default='Shubh Shuruaat, Agni ki Raftaar')
    tagline_hi = models.CharField(max_length=250, default='शुभ शुरुआत, अग्नि की रफ्तार')
    phone_primary = models.CharField(max_length=30, default='9425969464')
    phone_secondary = models.CharField(max_length=30, default='7974281559')
    address = models.TextField(default='Maihar, Madhya Pradesh')
    address_hi = models.TextField(default='मैहर, मध्य प्रदेश')
    whatsapp = models.CharField(max_length=30, default='9425969464')
    about = models.TextField(blank=True)
    about_hi = models.TextField(blank=True)
    hero_title = models.CharField(max_length=220, default='Electric mobility, made simple.')
    hero_title_hi = models.CharField(max_length=220, default='इलेक्ट्रिक मोबिलिटी, अब आसान।')
    hero_subtitle = models.TextField(blank=True)
    hero_subtitle_hi = models.TextField(blank=True)
    hero_image_data = models.TextField(blank=True)
    logo_data = models.TextField(blank=True)
    authorized_person = models.CharField(max_length=150, blank=True)
    gst_number = models.CharField(max_length=30, blank=True)
    website = models.CharField(max_length=220, blank=True)
    signatory_name = models.CharField(max_length=150, blank=True)
    signature_data = models.TextField(blank=True)
    def __str__(self): return self.business_name
