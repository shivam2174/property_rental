from django.urls import path
from . import views


urlpatterns = [

    # =====================================================
    # DASHBOARD
    # =====================================================

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    # =====================================================
# PROPERTY
# =====================================================

path(
    "property/",
    views.property_list,
    name="property_list",
),

path(
    "property/add/",
    views.property_add,
    name="property_add",
),

path(
    "property/<int:pk>/",
    views.property_detail,
    name="property_detail",
),

path(
    "property/<int:pk>/edit/",
    views.property_edit,
    name="property_edit",
),

path(
    "property/<int:pk>/delete/",
    views.property_delete,
    name="property_delete",
),


   

    # =====================================================
    # UNIT
    # =====================================================

    

    # =====================================================
    # TENANT
    # =====================================================

    path(
        "tenants/",
        views.tenant_list,
        name="tenant_list",
    ),

    path(
        "tenants/add/",
        views.tenant_add,
        name="tenant_add",
    ),

    path(
        "tenants/<int:pk>/edit/",
        views.tenant_edit,
        name="tenant_edit",
    ),

    path(
        "tenants/<int:pk>/delete/",
        views.tenant_delete,
        name="tenant_delete",
    ),

    path(
    "tenants/<int:pk>/",
    views.tenant_detail,
    name="tenant_detail",
    ),

    path(
    "tenants/<int:pk>/edit/",
    views.tenant_edit,
    name="tenant_edit",
),

path(
    "tenants/<int:pk>/delete/",
    views.tenant_delete,
    name="tenant_delete",
),


    # =====================================================
    # RENTAL AGREEMENT
    # =====================================================

    path(
        "agreements/",
        views.agreement_list,
        name="agreement_list",
    ),

    path(
        "agreements/add/",
        views.agreement_add,
        name="agreement_add",
    ),

    path(
        "agreements/<int:pk>/edit/",
        views.agreement_edit,
        name="agreement_edit",
    ),

    path(
        "agreements/<int:pk>/terminate/",
        views.agreement_terminate,
        name="agreement_terminate",
    ),

    path(
        "agreements/<int:pk>/delete/",
        views.agreement_delete,
        name="agreement_delete",
    ),

    path(
        "agreements/<int:agreement_id>/generate-invoice/",
        views.generate_invoice,
        name="generate_invoice",
    ),
    path(
    "agreements/<int:pk>/view/",
    views.agreement_view,
    name="agreement_view",
),


    # =====================================================
    # OWNER
    # =====================================================
# =====================================================
# OWNERS
# =====================================================

path(
    "owners/",
    views.owner_list,
    name="owner_list",
),

path(
    "owners/add/",
    views.owner_add,
    name="owner_add",
),

path(
    "owners/<int:pk>/",
    views.owner_detail,
    name="owner_detail",
),

path(
    "owners/<int:pk>/edit/",
    views.owner_edit,
    name="owner_edit",
),

path(
    "owners/<int:pk>/delete/",
    views.owner_delete,
    name="owner_delete",
),


    # =====================================================
    # INVOICE
    # =====================================================

    path(
        "invoices/",
        views.invoice_list,
        name="invoice_list",
    ),

    path(
        "invoices/<int:pk>/",
        views.invoice_detail,
        name="invoice_detail",
    ),

    path(
        "invoices/<int:pk>/pdf/",
        views.invoice_pdf,
        name="invoice_pdf",
    ),


    # =====================================================
    # PAYMENT
    # =====================================================

    path(
        "payments/",
        views.payment_list,
        name="payment_list",
    ),

    path(
        "payments/record/<int:invoice_id>/",
        views.record_payment,
        name="record_payment",
    ),

    path(
        "payments/<int:payment_id>/receipt/",
        views.payment_receipt,
        name="payment_receipt",
    ),
    path(
    "invoices/<int:invoice_id>/payments/",
    views.invoice_payment_history,
    name="invoice_payment_history",
),


    # =====================================================
    # FINANCIAL REPORT
    # =====================================================

    path(
        "financial-report/",
        views.financial_report,
        name="financial_report",
    ),


    # =====================================================
    # RESET TEST DATA
    # =====================================================

    path(
        "reset-test-data/",
        views.reset_test_data,
        name="reset_test_data",
    ),
]