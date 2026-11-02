from django.contrib import admin
from .models import InvoiceQuote, PaymentRecord, ExpenseRecord


@admin.register(InvoiceQuote)
class InvoiceQuoteAdmin(admin.ModelAdmin):
    list_display = ('reference_no', 'requirement', 'doc_type', 'amount_invoiced', 'amount_received', 'status', 'created_at')
    list_filter = ('doc_type', 'status', 'created_at')
    search_fields = ('reference_no', 'requirement__client_name')
    readonly_fields = ('reference_no', 'created_at')


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('transaction_reference', 'invoice', 'amount', 'currency', 'payment_method', 'payment_status', 'payment_date')
    list_filter = ('payment_method', 'payment_status', 'currency', 'payment_date')
    search_fields = ('transaction_reference', 'notes')
    readonly_fields = ('payment_date',)


@admin.register(ExpenseRecord)
class ExpenseRecordAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'amount', 'date', 'recorded_by')
    list_filter = ('category', 'date')
    search_fields = ('title', 'notes')

