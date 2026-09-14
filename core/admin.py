from django.contrib import admin

from .models import (
    Owner,
    Property,
    Tenant,
    RentalAgreement,
    Invoice,
    InvoiceItem,
    Payment,
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
    )

    list_filter = (
        "status",
    )




# =========================================================
# RENTAL AGREEMENT
# =========================================================

@admin.register(RentalAgreement)
class RentalAgreementAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "tenant",
        "property",
        "start_date",
        "end_date",
        "monthly_rent",
        "parking_charge",
        "cgst_rate",
        "sgst_rate",
        "rent_due_day",
        "status",
    )

    search_fields = (
        "tenant__full_name",
        "tenant__mobile",
        "property__name",
        "unit__unit_number",
    )

    list_filter = (
        "status",
        "property",
        "start_date",
        "end_date",
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