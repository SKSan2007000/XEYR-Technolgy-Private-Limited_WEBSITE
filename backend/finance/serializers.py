from rest_framework import serializers
from .models import InvoiceQuote, PaymentRecord, ExpenseRecord


class InvoiceQuoteSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = InvoiceQuote
        fields = [
            'id', 'requirement', 'project', 'reference_no', 'doc_type', 'doc_type_display',
            'amount_quoted', 'amount_approved', 'amount_invoiced', 'amount_received',
            'amount_pending', 'amount_refunded', 'currency', 'status', 'status_display',
            'due_date', 'notes', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at']


class PaymentRecordSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)

    class Meta:
        model = PaymentRecord
        fields = [
            'id', 'invoice', 'project', 'transaction_reference', 'payment_method',
            'payment_method_display', 'amount', 'currency', 'payment_status',
            'payment_status_display', 'payment_date', 'notes', 'verified_by', 'verified_by_name'
        ]
        read_only_fields = ['id', 'verified_by']


class ExpenseRecordSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ExpenseRecord
        fields = [
            'id', 'title', 'category', 'category_display', 'amount', 'currency',
            'date', 'notes', 'recorded_by', 'recorded_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'recorded_by', 'created_at']
