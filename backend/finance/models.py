import random
from django.db import models
from django.utils import timezone
from django.conf import settings
from requirements.models import ProjectRequirement
from projects.models import DeveloperProject


def generate_finance_ref(doc_type='INV'):
    year = timezone.now().year
    rand_seq = random.randint(1000, 9999)
    return f"XEYR-{doc_type}-{year}-{rand_seq}"


class InvoiceQuote(models.Model):
    class DocType(models.TextChoices):
        QUOTE = 'QUOTE', 'Quotation / Estimate'
        INVOICE = 'INVOICE', 'Tax Invoice'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent to Client'
        PARTIALLY_PAID = 'PARTIALLY_PAID', 'Partially Paid'
        PAID = 'PAID', 'Fully Paid'
        OVERDUE = 'OVERDUE', 'Overdue'
        CANCELLED = 'CANCELLED', 'Cancelled'

    requirement = models.ForeignKey(
        ProjectRequirement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='financial_docs'
    )
    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='financial_docs'
    )
    reference_no = models.CharField(max_length=40, unique=True, db_index=True)
    doc_type = models.CharField(max_length=20, choices=DocType.choices, default=DocType.INVOICE)

    # Distinct separation of financial values
    amount_quoted = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_approved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_invoiced = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_pending = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_refunded = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_invoices'
    )
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reference_no} ({self.get_doc_type_display()}) - ₹{self.amount_invoiced}"


class PaymentRecord(models.Model):
    class PaymentMethod(models.TextChoices):
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer (NEFT/RTGS/IMPS)'
        UPI = 'UPI', 'UPI / QR'
        CHEQUE = 'CHEQUE', 'Cheque / DD'
        CARD_RAZORPAY_PREP = 'CARD_RAZORPAY_PREP', 'Card / Gateway (Razorpay Foundation)'
        CASH = 'CASH', 'Cash'
        OTHER = 'OTHER', 'Other'

    class PaymentStatus(models.TextChoices):
        INITIATED = 'INITIATED', 'Initiated'
        VERIFIED = 'VERIFIED', 'Verified & Reconciled'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    invoice = models.ForeignKey(
        InvoiceQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    project = models.ForeignKey(
        DeveloperProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    transaction_reference = models.CharField(max_length=120, unique=True)
    payment_method = models.CharField(
        max_length=35,
        choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    payment_status = models.CharField(
        max_length=25,
        choices=PaymentStatus.choices,
        default=PaymentStatus.VERIFIED,
        db_index=True
    )
    payment_date = models.DateTimeField(default=timezone.now, db_index=True)
    notes = models.TextField(blank=True, default='')

    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_payments'
    )

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment ₹{self.amount} ({self.transaction_reference}) [{self.get_payment_status_display()}]"


class ExpenseRecord(models.Model):
    class ExpenseCategory(models.TextChoices):
        SOFTWARE_HOSTING = 'SOFTWARE_HOSTING', 'Software & Cloud Hosting'
        CONTRACTOR = 'CONTRACTOR', 'Contractor / Freelancer'
        HARDWARE_INFRA = 'HARDWARE_INFRA', 'Hardware & Infrastructure'
        OFFICE_ADMIN = 'OFFICE_ADMIN', 'Office & Administration'
        MARKETING = 'MARKETING', 'Marketing & Events'
        TRAINING = 'TRAINING', 'Training & Course Content'
        OTHER = 'OTHER', 'Other'

    title = models.CharField(max_length=200)
    category = models.CharField(
        max_length=35,
        choices=ExpenseCategory.choices,
        default=ExpenseCategory.SOFTWARE_HOSTING,
        db_index=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    date = models.DateField(default=timezone.now, db_index=True)
    notes = models.TextField(blank=True, default='')
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_expenses'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Expense: {self.title} - ₹{self.amount} ({self.get_category_display()})"
