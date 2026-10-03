from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from .models import Customer, LedgerEntry, Product, Sale, Purchase


def _ledger(reference, entry_type, account, amount, date, narration=''):
    entry, _ = LedgerEntry.objects.get_or_create(
        reference=reference,
        entry_type=entry_type,
        defaults={
            'account': account,
            'amount': amount,
            'date': date,
            'narration': narration,
        },
    )
    entry.account = account
    entry.amount = amount
    entry.date = date
    entry.narration = narration
    entry.save(update_fields=['account', 'amount', 'date', 'narration', 'updated_at'])
    return entry


def _delete_ledger(reference_prefix):
    LedgerEntry.objects.filter(reference__startswith=reference_prefix).delete()


def _adjust_stock(product_id, delta):
    if not product_id or not delta:
        return
    product = Product.objects.select_for_update().get(pk=product_id)
    new_stock = product.stock + int(delta)
    if new_stock < 0:
        raise ValueError(
            f'Insufficient stock for {product.name}. Available: {product.stock}, required: {abs(int(delta))}.'
        )
    Product.objects.filter(pk=product.pk).update(stock=new_stock, updated_at=timezone.now())


def sync_sale(sale, is_delete=False):
    """Keep inventory + ledger in sync with a sale. Safe to call repeatedly."""
    with transaction.atomic():
        if sale.stock_applied_product_id and sale.stock_applied_quantity:
            _adjust_stock(sale.stock_applied_product_id, sale.stock_applied_quantity)

        if is_delete:
            _delete_ledger(f'SALE:{sale.pk}:')
            return

        if sale.product_id and sale.quantity:
            _adjust_stock(sale.product_id, -sale.quantity)
            Sale.objects.filter(pk=sale.pk).update(stock_applied_quantity=sale.quantity, stock_applied_product_id=sale.product_id)

        amount = Decimal(sale.amount or 0)
        _ledger(
            f'SALE:{sale.pk}:REVENUE', 'CREDIT', 'Sales Revenue', amount,
            sale.sale_date, f'Sale {sale.invoice_no}'
        )
        paid = min(Decimal(sale.paid_amount or 0), amount)
        if paid:
            payment_account = sale.payment_mode if sale.payment_mode != 'Credit' else 'Accounts Receivable'
            _ledger(
                f'SALE:{sale.pk}:PAYMENT', 'DEBIT', payment_account, paid,
                sale.sale_date, f'Payment received against {sale.invoice_no}'
            )
        else:
            _delete_ledger(f'SALE:{sale.pk}:PAYMENT')
        balance = max(Decimal('0'), amount - paid)
        if balance:
            _ledger(
                f'SALE:{sale.pk}:RECEIVABLE', 'DEBIT', 'Accounts Receivable', balance,
                sale.sale_date, f'Outstanding against {sale.invoice_no}'
            )
        else:
            _delete_ledger(f'SALE:{sale.pk}:RECEIVABLE')


def sync_purchase(purchase, is_delete=False):
    with transaction.atomic():
        if purchase.stock_applied_product_id and purchase.stock_applied_quantity:
            _adjust_stock(purchase.stock_applied_product_id, -purchase.stock_applied_quantity)

        if is_delete:
            _delete_ledger(f'PURCHASE:{purchase.pk}:')
            return

        if purchase.product_id and purchase.quantity:
            _adjust_stock(purchase.product_id, purchase.quantity)
            Purchase.objects.filter(pk=purchase.pk).update(stock_applied_quantity=purchase.quantity, stock_applied_product_id=purchase.product_id)

        amount = Decimal(purchase.amount or 0)
        _ledger(
            f'PURCHASE:{purchase.pk}:COST', 'DEBIT', 'Purchases / Inventory', amount,
            purchase.purchase_date, f'Purchase {purchase.bill_no}'
        )
        paid = min(Decimal(purchase.paid_amount or 0), amount)
        if paid:
            payment_account = purchase.payment_mode if purchase.payment_mode != 'Credit' else 'Accounts Payable'
            _ledger(
                f'PURCHASE:{purchase.pk}:PAYMENT', 'CREDIT', payment_account, paid,
                purchase.purchase_date, f'Payment made against {purchase.bill_no}'
            )
        else:
            _delete_ledger(f'PURCHASE:{purchase.pk}:PAYMENT')
        balance = max(Decimal('0'), amount - paid)
        if balance:
            _ledger(
                f'PURCHASE:{purchase.pk}:PAYABLE', 'CREDIT', 'Accounts Payable', balance,
                purchase.purchase_date, f'Outstanding against {purchase.bill_no}'
            )
        else:
            _delete_ledger(f'PURCHASE:{purchase.pk}:PAYABLE')


def customer_from_order(order):
    customer, _ = Customer.objects.get_or_create(
        mobile=order.phone,
        defaults={
            'name': order.name,
            'email': order.email,
            'address': order.address,
        },
    )
    changed = False
    if customer.name != order.name:
        customer.name = order.name; changed = True
    if order.email and customer.email != order.email:
        customer.email = order.email; changed = True
    if order.address and customer.address != order.address:
        customer.address = order.address; changed = True
    if changed:
        customer.save()
    return customer


def sync_order(order):
    """A delivered order becomes a sale automatically. Cancelling/re-opening removes only the auto-sale."""
    from .models import Sale
    with transaction.atomic():
        if order.status in ('DELIVERED', 'COMPLETED') and order.product_id:
            customer = customer_from_order(order)
            sale = Sale.objects.filter(order_id=order.pk).first()
            if sale is None:
                invoice = f'AA-{timezone.now().strftime("%Y%m%d")}-{order.pk:06d}'
                mrp = (order.product.price or 0) * (order.quantity or 1)
                display = (order.product.display_price or 0) * (order.quantity or 1)
                discount = max(0, mrp - display)
                gst = ((order.product.gst_percent or 0) * display / Decimal('100')).quantize(Decimal('0.01'))
                sale = Sale(
                    invoice_no=invoice,
                    order=order,
                    customer=customer,
                    customer_name=order.name,
                    phone=order.phone,
                    product=order.product,
                    quantity=order.quantity,
                    amount=order.amount,
                    mrp_amount=mrp,
                    discount_amount=discount,
                    processing_fee=0,
                    gst_amount=gst,
                    other_charges=0,
                    paid_amount=order.paid_amount,
                    payment_mode=order.payment_mode,
                    sale_date=timezone.localdate(),
                    notes=f'Auto-created from Order #{order.pk}',
                    auto_generated_from_order=True,
                )
                sale.save()
            elif sale.auto_generated_from_order:
                mrp = (order.product.price or 0) * (order.quantity or 1)
                display = (order.product.display_price or 0) * (order.quantity or 1)
                discount = max(0, mrp - display)
                gst = ((order.product.gst_percent or 0) * display / Decimal('100')).quantize(Decimal('0.01'))
                sale.customer = customer
                sale.customer_name = order.name
                sale.phone = order.phone
                sale.product = order.product
                sale.quantity = order.quantity
                sale.amount = order.amount
                sale.mrp_amount = mrp
                sale.discount_amount = discount
                sale.processing_fee = 0
                sale.gst_amount = gst
                sale.other_charges = 0
                sale.paid_amount = order.paid_amount
                sale.payment_mode = order.payment_mode
                sale.save()
        else:
            sale = Sale.objects.filter(order_id=order.pk, auto_generated_from_order=True).first()
            if sale:
                sale.delete()


def sync_expense(expense, is_delete=False):
    with transaction.atomic():
        if is_delete:
            _delete_ledger(f'EXPENSE:{expense.pk}:')
            return
        amount = Decimal(expense.amount or 0)
        _ledger(
            f'EXPENSE:{expense.pk}:COST', 'DEBIT', expense.category, amount,
            expense.date, expense.description
        )
        _ledger(
            f'EXPENSE:{expense.pk}:PAYMENT', 'CREDIT', expense.payment_mode, amount,
            expense.date, f'Payment for {expense.description}'
        )
