from django.contrib import admin

from .models import (
    Owner,
    Property,
    Tenant,
    TenantContactPerson,
    LeaseAgreement,
    RentHistory,
    Invoice,
    InvoiceItem,
    Payment,
    PropertyDocument,
    PropertyTax,
)


# =========================================================
# OWNER
# =========================================================

@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):

    list_display = (
        "owner_code",
        "name",
        "mobile",
        "email",
        "pan",
        "gst_haryana",
        "gst_delhi",
    )

    search_fields = (
        "owner_code",
        "name",
        "mobile",
        "email",
        "pan",
    )

    list_filter = (
        "state",
        "city",
    )


# =========================================================
# PROPERTY
# =========================================================

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "owner",
        "city",
        "state",
        "status",
    )

    search_fields = (
        "name",
        "address",
        "city",
        "state",
        "pincode",
        "owner__name",
    )

    list_filter = (
        "status",
        "city",
        "state",
    )


# =========================================================
# PROPERTY DOCUMENT
# =========================================================

@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "property",
        "document_name",
        "uploaded_at",
    )

    search_fields = (
        "property__name",
        "document_name",
    )

    list_filter = (
        "uploaded_at",
    )

    readonly_fields = (
        "uploaded_at",
    )


# =========================================================
# PROPERTY TAX
# =========================================================

@admin.register(PropertyTax)
class PropertyTaxAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "property",
        "tax_year",
        "tax_amount",
        "status",
        "paid_on",
    )

    search_fields = (
        "property__name",
        "tax_year",
    )

    list_filter = (
        "status",
        "tax_year",
    )


# =========================================================
# TENANT
# =========================================================

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "full_name",
        "father_name",
        "mobile",
        "email",
        "status",
        "security_deposit",
    )

    search_fields = (
        "full_name",
        "father_name",
        "mobile",
        "email",
        "id_number_1",
        "id_number_2",
        "id_number_3",
        "gst_number",
    )

    list_filter = (
        "status",
    )


# =========================================================
# TENANT CONTACT PERSON
# =========================================================

@admin.register(TenantContactPerson)
class TenantContactPersonAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tenant",
        "designation",
        "name",
        "email",
        "phone",
        "id_type",
        "id_number",
    )

    search_fields = (
        "tenant__full_name",
        "name",
        "email",
        "phone",
        "id_number",
    )

    list_filter = (
        "id_type",
        "designation",
    )


# =========================================================
# LEASE AGREEMENT
# =========================================================

@admin.register(LeaseAgreement)
class LeaseAgreementAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tenant",
        "property",
        "start_date",
        "end_date",
        "monthly_rent",
        "lock_in_months",
        "rent_free_period_days",
        "parking_charge",
        "free_parking_spaces",
        "security_deposit",
        "cgst_rate",
        "sgst_rate",
        "rent_due_day",
        "status",
    )

    search_fields = (
        "tenant__full_name",
        "tenant__mobile",
        "tenant__email",
        "property__name",
        "property__address",
    )

    list_filter = (
        "status",
        "property",
        "start_date",
        "end_date",
    )

    readonly_fields = (
        "total_monthly_amount",
        "current_cgst_amount",
        "current_sgst_amount",
        "current_total_with_gst",
        "lock_in_end_date",
        "rent_free_end_date",
    )


# =========================================================
# RENT HISTORY
# =========================================================

@admin.register(RentHistory)
class RentHistoryAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "lease_agreement",
        "effective_from",
        "effective_to",
        "monthly_rent",
        "increase_percent",
        "increase_accepted",
    )

    search_fields = (
        "lease_agreement__tenant__full_name",
        "lease_agreement__property__name",
    )

    list_filter = (
        "increase_accepted",
        "effective_from",
        "effective_to",
    )


# =========================================================
# INVOICE
# =========================================================

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):

    list_display = (
        "invoice_number",
        "invoice_date",
        "tenant_name",
        "property_name",
        "unit_number",
        "taxable_amount",
        "cgst_amount",
        "sgst_amount",
        "total_amount",
        "status",
    )

    search_fields = (
        "tenant_name",
        "tenant_mobile",
        "tenant_email",
        "property_name",
        "unit_number",
        "owner_name",
        "owner_company_name",
    )

    list_filter = (
        "status",
        "invoice_date",
        "billing_from",
        "billing_to",
    )

    readonly_fields = (
        "invoice_number",
        "created_at",
        "updated_at",
    )


# =========================================================
# INVOICE ITEM
# =========================================================

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "invoice",
        "item_type",
        "description",
        "unit_number",
        "rate",
        "amount",
    )

    search_fields = (
        "description",
        "unit_number",
        "invoice__tenant_name",
    )

    list_filter = (
        "item_type",
    )


# =========================================================
# PAYMENT
# =========================================================

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "invoice",
        "payment_date",
        "amount",
        "payment_method",
        "transaction_reference",
    )

    search_fields = (
        "invoice__tenant_name",
        "invoice__invoice_number",
        "transaction_reference",
    )

    list_filter = (
        "payment_method",
        "payment_date",
    )

    ordering = (
        "-payment_date",
        "-id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )