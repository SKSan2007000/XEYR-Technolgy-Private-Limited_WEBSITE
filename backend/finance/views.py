from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import InvoiceQuote, PaymentRecord, ExpenseRecord, generate_finance_ref
from .serializers import InvoiceQuoteSerializer, PaymentRecordSerializer, ExpenseRecordSerializer
from core.models import AuditLog


class InvoiceQuoteListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        docs = InvoiceQuote.objects.select_related('created_by').all()
        return Response(InvoiceQuoteSerializer(docs, many=True).data)

    def post(self, request):
        if not request.user.can_manage_finance:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data.copy()
        doc_type = data.get('doc_type', 'INVOICE')
        ref_no = data.get('reference_no') or generate_finance_ref('INV' if doc_type == 'INVOICE' else 'QT')

        doc = InvoiceQuote.objects.create(
            requirement_id=data.get('requirement'),
            project_id=data.get('project'),
            reference_no=ref_no,
            doc_type=doc_type,
            amount_quoted=data.get('amount_quoted', 0.00),
            amount_approved=data.get('amount_approved', 0.00),
            amount_invoiced=data.get('amount_invoiced', 0.00),
            amount_received=data.get('amount_received', 0.00),
            amount_pending=data.get('amount_pending', 0.00),
            amount_refunded=data.get('amount_refunded', 0.00),
            currency=data.get('currency', 'INR'),
            status=data.get('status', 'DRAFT'),
            due_date=data.get('due_date'),
            notes=data.get('notes', ''),
            created_by=request.user
        )
        AuditLog.log('FINANCIAL_DOC_CREATED', 'InvoiceQuote', doc.id, user=request.user, details={'reference_no': ref_no, 'doc_type': doc_type}, request=request)
        return Response(InvoiceQuoteSerializer(doc).data, status=status.HTTP_201_CREATED)


class PaymentRecordListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payments = PaymentRecord.objects.select_related('invoice', 'verified_by').all()
        return Response(PaymentRecordSerializer(payments, many=True).data)

    def post(self, request):
        if not request.user.can_manage_finance:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        payment = PaymentRecord.objects.create(
            invoice_id=data.get('invoice'),
            project_id=data.get('project'),
            transaction_reference=data.get('transaction_reference'),
            payment_method=data.get('payment_method', 'BANK_TRANSFER'),
            amount=data.get('amount', 0.00),
            currency=data.get('currency', 'INR'),
            payment_status=data.get('payment_status', 'VERIFIED'),
            payment_date=data.get('payment_date'),
            notes=data.get('notes', ''),
            verified_by=request.user
        )

        # Update invoice amount_received and amount_pending if connected
        if payment.invoice and payment.payment_status == 'VERIFIED':
            inv = payment.invoice
            inv.amount_received += payment.amount
            inv.amount_pending = max(0, inv.amount_invoiced - inv.amount_received)
            if inv.amount_pending == 0 and inv.amount_invoiced > 0:
                inv.status = 'PAID'
            elif inv.amount_received > 0:
                inv.status = 'PARTIALLY_PAID'
            inv.save()

        AuditLog.log('PAYMENT_RECORDED', 'PaymentRecord', payment.id, user=request.user, details={'amount': float(payment.amount), 'ref': payment.transaction_reference}, request=request)
        return Response(PaymentRecordSerializer(payment).data, status=status.HTTP_201_CREATED)


class ExpenseListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        expenses = ExpenseRecord.objects.select_related('recorded_by').all()
        return Response(ExpenseRecordSerializer(expenses, many=True).data)

    def post(self, request):
        if not request.user.can_manage_finance:
            return Response({'error': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        expense = ExpenseRecord.objects.create(
            title=data.get('title'),
            category=data.get('category', 'SOFTWARE_HOSTING'),
            amount=data.get('amount', 0.00),
            currency=data.get('currency', 'INR'),
            date=data.get('date'),
            notes=data.get('notes', ''),
            recorded_by=request.user
        )
        AuditLog.log('EXPENSE_RECORDED', 'ExpenseRecord', expense.id, user=request.user, details={'title': expense.title, 'amount': float(expense.amount)}, request=request)
        return Response(ExpenseRecordSerializer(expense).data, status=status.HTTP_201_CREATED)
