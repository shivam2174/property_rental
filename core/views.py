from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_DOWN
from calendar import monthrange
from django.db import transaction

from django.contrib import messages
from django.db import models, transaction, IntegrityError, connection
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date, timedelta
from datetime import datetime
from django.utils.dateparse import parse_date as django_parse_date
from django.views.decorators.http import require_POST
from dateutil.relativedelta import relativedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from calendar import month_name
from decimal import Decimal, ROUND_HALF_UP
from types import SimpleNamespace

from django.db import models, transaction
from django.shortcuts import render
User = get_user_model()



from xhtml2pdf import pisa

from core.models import (
    AdminUserProfile,
    Owner,
    Property,
    Tenant,
    TenantContactPerson,
    LeaseAgreement,
    LeaseNotification,
    RentHistory,
    Invoice,
    TDSLedger,
    GSTLedger,
    InvoiceItem,
    Payment,
    PropertyTax,
    PropertyDocument,

)
from .forms import TenantForm, AgreementForm, PropertyTaxForm, AdminProfileForm, AdminUserCreateForm

# =========================================================
# COMMON HELPERS
# =========================================================

ZERO = Decimal("0.00")
ONE_HUNDRED = Decimal("100")


def parse_decimal(value, default=ZERO):
    """
    Safely convert a value into Decimal.
    """
    if value in (None, ""):
        return default

    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return default


def parse_date(value, default=None):
    """
    Safely convert YYYY-MM-DD into a date.
    """
    if not value:
        return default

    try:
        return django_parse_date(str(value)) or default
    except (ValueError, TypeError):
        return default


def valid_percentage(value):
    """
    Validate percentage between 0 and 100.
    """
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return False

    return ZERO <= value <= ONE_HUNDRED


def add_months(original_date, months):
    """
    Add months to a date while safely handling month-end dates.

    Example:
        01-Jan-2026 + 12 months = 01-Jan-2027
        31-Jan-2026 + 1 month = 28-Feb-2026
    """

    if not original_date:
        return None

    month_index = (
        original_date.month
        - 1
        + months
    )

    year = (
        original_date.year
        + month_index // 12
    )

    month = (
        month_index % 12
    ) + 1

    day = min(
        original_date.day,
        monthrange(year, month)[1]
    )

    return date(
        year,
        month,
        day,
    )


def get_invoice_total_paid(invoice):
    """
    Return total amount paid against invoice.
    """
    return (
        invoice.payments.aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )


def get_invoice_rent_amount(invoice):
    """Return rent only, excluding GST and parking."""
    return (
        invoice.items.filter(item_type="rent")
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )



def get_invoice_tds_amount(invoice):
    """Calculate TDS at 10% of rent plus parking, before GST."""

    rent_amount = get_invoice_rent_amount(invoice)

    parking_amount = (
        invoice.items
        .filter(item_type="parking")
        .aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    tds_base_amount = rent_amount + parking_amount

    return (
        tds_base_amount * Decimal("10.00") / Decimal("100")
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )




def get_invoice_tds_credited(invoice):
    """Return TDS only when it has been marked as credited."""
    try:
        ledger = invoice.tds_ledger
    except TDSLedger.DoesNotExist:
        return ZERO

    if ledger.tds_credited:
        return ledger.tds_amount

    return ZERO


def get_invoice_net_payable(invoice):
    """Invoice total less the calculated TDS deduction."""
    tds_amount = get_invoice_tds_amount(invoice)

    return max(invoice.total_amount - tds_amount, ZERO)


def get_invoice_cash_balance(invoice):
    """Remaining cash/bank payment expected from the tenant."""
    paid = get_invoice_total_paid(invoice)

    return max(get_invoice_net_payable(invoice) - paid, ZERO)

def get_invoice_balance(invoice):
    """
    Return outstanding invoice balance.
    """
    paid = get_invoice_total_paid(invoice)

    return max(
        invoice.total_amount - paid,
        ZERO,
    )


# =========================================================
# OWNER MANAGEMENT
# =========================================================
@login_required
def owner_list(request):

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. Only Administrators can view the owner list."
        )

    owners = (
        Owner.objects
        .all()
        .order_by("name")
    )

    return render(
        request,
        "core/owner_list.html",
        {
            "owners": owners,
        },
    )


def owner_detail(request, pk):

    owner = get_object_or_404(
        Owner,
        pk=pk,
    )

    return render(
        request,
        "core/owner_detail.html",
        {
            "owner": owner,
        },
    )


def owner_add(request):

    if request.method == "POST":

        owner_code = request.POST.get(
            "owner_code",
            "",
        ).strip()

        name = request.POST.get(
            "name",
            "",
        ).strip()

        address = request.POST.get(
            "address",
            "",
        ).strip()

        city = request.POST.get(
            "city",
            "",
        ).strip()

        state = request.POST.get(
            "state",
            "",
        ).strip()

        pincode = request.POST.get(
            "pincode",
            "",
        ).strip()

        mobile = request.POST.get(
            "mobile",
            "",
        ).strip()

        email = request.POST.get(
            "email",
            "",
        ).strip()

        pan = request.POST.get(
            "pan",
            "",
        ).strip()

        gst_haryana = request.POST.get(
            "gst_haryana",
            "",
        ).strip()

        gst_delhi = request.POST.get(
            "gst_delhi",
            "",
        ).strip()

        if not name:

            messages.error(
                request,
                "Owner Name is required.",
            )

            return render(
                request,
                "core/owner_form.html",
            )

        try:

            Owner.objects.create(
                owner_code=owner_code or None,
                name=name,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                mobile=mobile,
                email=email,
                pan=pan,
                gst_haryana=gst_haryana,
                gst_delhi=gst_delhi,
            )

            messages.success(
                request,
                "Owner added successfully.",
            )

            return redirect(
                "owner_list"
            )

        except IntegrityError:

            messages.error(
                request,
                "Unable to add owner. Owner Code may already exist.",
            )

    return render(
        request,
        "core/owner_form.html",
    )


def owner_edit(request, pk):

    owner = get_object_or_404(
        Owner,
        pk=pk,
    )

    if request.method == "POST":

        owner_code = request.POST.get(
            "owner_code",
            "",
        ).strip()

        name = request.POST.get(
            "name",
            "",
        ).strip()

        if not name:

            messages.error(
                request,
                "Owner Name is required.",
            )

            return render(
                request,
                "core/owner_form.html",
                {
                    "owner": owner,
                },
            )

        owner.owner_code = (
            owner_code or None
        )

        owner.name = name

        owner.address = request.POST.get(
            "address",
            "",
        ).strip()

        owner.city = request.POST.get(
            "city",
            "",
        ).strip()

        owner.state = request.POST.get(
            "state",
            "",
        ).strip()

        owner.pincode = request.POST.get(
            "pincode",
            "",
        ).strip()

        owner.mobile = request.POST.get(
            "mobile",
            "",
        ).strip()

        owner.email = request.POST.get(
            "email",
            "",
        ).strip()

        owner.pan = request.POST.get(
            "pan",
            "",
        ).strip()

        owner.gst_haryana = request.POST.get(
            "gst_haryana",
            "",
        ).strip()

        owner.gst_delhi = request.POST.get(
            "gst_delhi",
            "",
        ).strip()

        try:

            owner.save()

            messages.success(
                request,
                "Owner updated successfully.",
            )

            return redirect(
                "owner_list"
            )

        except IntegrityError:

            messages.error(
                request,
                "Unable to update owner. Owner Code may already exist.",
            )

    return render(
        request,
        "core/owner_form.html",
        {
            "owner": owner,
        },
    )


def owner_delete(request, pk):

    owner = get_object_or_404(
        Owner,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "owner_list"
        )

    try:

        owner.delete()

        messages.success(
            request,
            "Owner deleted successfully.",
        )

    except ProtectedError:

        messages.error(
            request,
            "This owner cannot be deleted because related properties exist.",
        )

    return redirect(
        "owner_list"
    )


# =========================================================
# PROPERTY MANAGEMENT
# =========================================================



def property_list(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. Only Administrators can view the property list."
        )


    properties = (
        Property.objects
        .select_related("owner")
        .all()
        .order_by("name")
    )

    filter_type = request.GET.get(
        "filter",
        "all",
    )

    owner_id = request.GET.get(
        "owner"
    )

    if owner_id:
        properties = properties.filter(
            owner_id=owner_id
        )

    for property_obj in properties:

        # Current Property model uses unit_no
        total_units = (
            1
            if property_obj.unit_no
            else 0
        )

        # Check active Lease Agreement directly
        occupied = (
            LeaseAgreement.objects
            .filter(
                property=property_obj,
                status="active",
            )
            .exists()
        )

        occupied_units = (
            1
            if occupied and total_units > 0
            else 0
        )

        vacant_units = max(
            total_units - occupied_units,
            0,
        )

        property_obj.total_units_count = (
            total_units
        )

        property_obj.occupied_units_count = (
            occupied_units
        )

        property_obj.vacant_units_count = (
            vacant_units
        )

        # Set occupancy status
        if total_units == 0:

            property_obj.occupancy_status = (
                "none"
            )

        elif occupied_units == total_units:

            property_obj.occupancy_status = (
                "occupied"
            )

        elif occupied_units > 0:

            property_obj.occupancy_status = (
                "partial"
            )

        else:

            property_obj.occupancy_status = (
                "free"
            )

    # Occupied properties
    if filter_type == "occupied":

        properties = [
            property_obj
            for property_obj in properties
            if property_obj.occupancy_status == "occupied"
        ]

    # Free properties
    elif filter_type == "free":

        properties = [
            property_obj
            for property_obj in properties
            if property_obj.occupancy_status == "free"
        ]

    return render(
        request,
        "core/property_list.html",
        {
            "properties": properties,
            "filter_type": filter_type,
            "owners": Owner.objects.all().order_by(
                "name"
            ),
            "selected_owner": owner_id,
        },
    )



    properties = (
        Property.objects
        .select_related("owner")
        .all()
        .order_by("name")
    )

    filter_type = request.GET.get(
        "filter",
        "all",
    )

    owner_id = request.GET.get(
        "owner"
    )

    if owner_id:
        properties = properties.filter(
            owner_id=owner_id
        )

    for property_obj in properties:

        # Latest Property Tax record
        property_obj.latest_tax = (
            property_obj.property_taxes.first()
        )
        # Your current Property model uses unit_no
        total_units = (
            1
            if property_obj.unit_no
            else 0
        )

        # IMPORTANT:
        # An ACTIVE Lease Agreement means
        # the property is occupied.
        occupied = (
            LeaseAgreement.objects
            .filter(
                property=property_obj,
                status="active",
            )
            .exists()
        )

        if occupied and total_units > 0:
            occupied_units = 1
        else:
            occupied_units = 0

        vacant_units = max(
            total_units - occupied_units,
            0,
        )

        property_obj.total_units_count = (
            total_units
        )

        property_obj.occupied_units_count = (
            occupied_units
        )

        property_obj.vacant_units_count = (
            vacant_units
        )

        # Set final property status
        if total_units == 0:

            property_obj.occupancy_status = (
                "none"
            )

        elif occupied_units == total_units:

            property_obj.occupancy_status = (
                "occupied"
            )

        elif occupied_units > 0:

            property_obj.occupancy_status = (
                "partial"
            )

        else:

            property_obj.occupancy_status = (
                "free"
            )

    # Occupied filter
    if filter_type == "occupied":

        properties = [
            property_obj
            for property_obj in properties
            if property_obj.occupancy_status == "occupied"
        ]

    # Free filter
    elif filter_type == "free":

        properties = [
            property_obj
            for property_obj in properties
            if property_obj.occupancy_status == "free"
        ]

    return render(
        request,
        "core/property_list.html",
        {
            "properties": properties,
            "filter_type": filter_type,
            "owners": Owner.objects.all().order_by(
                "name"
            ),
            "selected_owner": owner_id,
        },
    )


def property_detail(request, pk):

    property_obj = get_object_or_404(
        Property.objects.select_related(
            "owner"
        ),
        pk=pk,
    )

    active_agreement = (
        LeaseAgreement.objects
        .select_related("tenant")
        .filter(
            property=property_obj,
            status="active",
        )
        .first()
    )

    property_taxes = property_obj.property_taxes.all()

    property_documents = property_obj.documents.all()

    return render(
        request,
        "core/property_detail.html",
        {
            "property": property_obj,
            "active_agreement": active_agreement,
            "property_taxes": property_taxes,
            "property_documents": property_documents,
        },
    )

def property_add(request):

    owners = (
        Owner.objects
        .all()
        .order_by("name")
    )

    if request.method == "POST":

        owner_id = request.POST.get("owner")

        name = request.POST.get(
            "name",
            "",
        ).strip()

        address = request.POST.get(
            "address",
            "",
        ).strip()

        unit_no = request.POST.get(
            "unit_no",
            "",
        ).strip()

        tower = request.POST.get(
            "tower",
            "",
        ).strip()

        city = request.POST.get(
            "city",
            "",
        ).strip()

        state = request.POST.get(
            "state",
            "",
        ).strip()

        pincode = request.POST.get(
            "pincode",
            "",
        ).strip()

        purchased_on = parse_date(
            request.POST.get("purchased_on")
        )

        total_area = parse_decimal(
            request.POST.get("total_area")
        )

        price = parse_decimal(
            request.POST.get("price")
        )

        per_sqft_rate = parse_decimal(
            request.POST.get("per_sqft_rate")
        )

        stamp_duty = parse_decimal(
            request.POST.get("stamp_duty")
        )

        total_purchase_price = parse_decimal(
            request.POST.get("total_purchase_price")
        )

        gst_number = request.POST.get(
            "gst_number",
            "",
        ).strip()

        lap_amount = parse_decimal(
            request.POST.get("lap_amount")
        )

        monthly_installment = parse_decimal(
            request.POST.get("monthly_installment")
        )

        lap_maturity = parse_date(
            request.POST.get("lap_maturity")
        )

        parking_slot = request.POST.get(
            "parking_slot",
            "",
        ).strip()

        status = request.POST.get(
            "status",
            "active",
        )

        # ==========================================
        # PROPERTY TAX
        # ==========================================

        tax_amount = parse_decimal(
            request.POST.get("tax_amount")
        )

        # ==========================================
        # PROPERTY DOCUMENTS
        # ==========================================

        document_names = request.POST.getlist(
            "document_name"
        )

        uploaded_documents = request.FILES.getlist(
            "document"
        )

        # ==========================================
        # BASIC VALIDATION
        # ==========================================

        if not name:

            messages.error(
                request,
                "Property Description is required.",
            )

            return render(
                request,
                "core/property_form.html",
                {
                    "owners": owners,
                },
            )

        # ==========================================
        # DOCUMENT VALIDATION
        # Maximum PDF size = 300 MB
        # ==========================================

        MAX_PROPERTY_DOCUMENT_SIZE = (
            300 * 1024 * 1024
        )

        for uploaded_document in uploaded_documents:

            # Check file size
            if (
                uploaded_document.size
                > MAX_PROPERTY_DOCUMENT_SIZE
            ):

                messages.error(
                    request,
                    f"File '{uploaded_document.name}' "
                    f"is too large. Maximum allowed size "
                    f"is 300 MB.",
                )

                return render(
                    request,
                    "core/property_form.html",
                    {
                        "owners": owners,
                    },
                )

            # Check PDF extension
            if not uploaded_document.name.lower().endswith(
                ".pdf"
            ):

                messages.error(
                    request,
                    f"Only PDF files are allowed: "
                    f"{uploaded_document.name}",
                )

                return render(
                    request,
                    "core/property_form.html",
                    {
                        "owners": owners,
                    },
                )

        # ==========================================
        # OWNER
        # ==========================================

        owner = None

        if owner_id:

            owner = get_object_or_404(
                Owner,
                pk=owner_id,
            )

        # ==========================================
        # AUTO CALCULATIONS
        # ==========================================

        if (
            per_sqft_rate == ZERO
            and total_area > ZERO
            and price > ZERO
        ):

            per_sqft_rate = (
                price / total_area
            ).quantize(
                Decimal("0.01")
            )

        if (
            total_purchase_price == ZERO
            and price > ZERO
        ):

            total_purchase_price = (
                price + stamp_duty
            )

        # ==========================================
        # DATABASE TRANSACTION
        # ==========================================

        try:

            with transaction.atomic():

                # ==================================
                # CREATE PROPERTY
                # ==================================

                property_obj = Property.objects.create(

                    owner=owner,

                    name=name,
                    address=address,
                    unit_no=unit_no,
                    tower=tower,

                    city=city,
                    state=state,
                    pincode=pincode,

                    purchased_on=purchased_on,

                    total_area=total_area,
                    price=price,
                    per_sqft_rate=per_sqft_rate,

                    stamp_duty=stamp_duty,
                    total_purchase_price=(
                        total_purchase_price
                    ),

                    gst_number=gst_number,

                    lap_amount=lap_amount,
                    monthly_installment=(
                        monthly_installment
                    ),
                    lap_maturity=lap_maturity,

                    parking_slot=parking_slot,

                    status=status,
                )

                # ==================================
                # CREATE PROPERTY TAX
                # ==================================

                if tax_amount > ZERO:

                    current_date = date.today()

                    if current_date.month >= 4:

                        tax_year = (
                            f"{current_date.year}-"
                            f"{str(current_date.year + 1)[-2:]}"
                        )

                    else:

                        tax_year = (
                            f"{current_date.year - 1}-"
                            f"{str(current_date.year)[-2:]}"
                        )

                    PropertyTax.objects.create(

                        property=property_obj,

                        tax_year=tax_year,

                        tax_amount=tax_amount,

                        status="unpaid",

                        paid_on=None,
                    )

                # ==================================
                # CREATE PROPERTY DOCUMENTS
                # ==================================

                for index, uploaded_document in enumerate(
                    uploaded_documents
                ):

                    document_name = ""

                    if index < len(document_names):

                        document_name = (
                            document_names[index].strip()
                        )

                    PropertyDocument.objects.create(

                        property=property_obj,

                        document_name=(
                            document_name
                            or uploaded_document.name
                        ),

                        document=uploaded_document,
                    )

            # ======================================
            # SUCCESS
            # ======================================

            messages.success(
                request,
                "Property added successfully.",
            )

            return redirect(
                "property_list"
            )

        except IntegrityError:

            messages.error(
                request,
                "Unable to add property. Please check the entered data.",
            )

    return render(
        request,
        "core/property_form.html",
        {
            "owners": owners,
        },
    )


def property_edit(request, pk):

    property_obj = get_object_or_404(
        Property,
        pk=pk,
    )

    owners = (
        Owner.objects
        .all()
        .order_by("name")
    )

    if request.method == "POST":

        owner_id = request.POST.get(
            "owner"
        )

        name = request.POST.get(
            "name",
            "",
        ).strip()

        if not name:

            messages.error(
                request,
                "Property Description is required.",
            )

            return render(
                request,
                "core/property_form.html",
                {
                    "property": property_obj,
                    "owners": owners,
                },
            )

        owner = None

        if owner_id:

            owner = get_object_or_404(
                Owner,
                pk=owner_id,
            )

        property_obj.owner = owner
        property_obj.name = name

        property_obj.address = request.POST.get(
            "address",
            "",
        ).strip()

        property_obj.unit_no = request.POST.get(
            "unit_no",
            "",
        ).strip()

        property_obj.tower = request.POST.get(
            "tower",
            "",
        ).strip()

        property_obj.city = request.POST.get(
            "city",
            "",
        ).strip()

        property_obj.state = request.POST.get(
            "state",
            "",
        ).strip()

        property_obj.pincode = request.POST.get(
            "pincode",
            "",
        ).strip()

        property_obj.purchased_on = parse_date(
            request.POST.get(
                "purchased_on"
            )
        )

        property_obj.total_area = parse_decimal(
            request.POST.get(
                "total_area"
            )
        )

        property_obj.price = parse_decimal(
            request.POST.get(
                "price"
            )
        )

        property_obj.per_sqft_rate = parse_decimal(
            request.POST.get(
                "per_sqft_rate"
            )
        )

        property_obj.stamp_duty = parse_decimal(
            request.POST.get(
                "stamp_duty"
            )
        )

        property_obj.total_purchase_price = (
            parse_decimal(
                request.POST.get(
                    "total_purchase_price"
                )
            )
        )

        property_obj.gst_number = request.POST.get(
            "gst_number",
            "",
        ).strip()

        property_obj.lap_amount = parse_decimal(
            request.POST.get(
                "lap_amount"
            )
        )

        property_obj.monthly_installment = (
            parse_decimal(
                request.POST.get(
                    "monthly_installment"
                )
            )
        )

        property_obj.lap_maturity = parse_date(
            request.POST.get(
                "lap_maturity"
            )
        )

        property_obj.parking_slot = request.POST.get(
            "parking_slot",
            "",
        ).strip()

        property_obj.status = request.POST.get(
            "status",
            "active",
        )

        if (
            property_obj.total_area > ZERO
            and property_obj.price > ZERO
        ):

            property_obj.per_sqft_rate = (
                property_obj.price
                / property_obj.total_area
            ).quantize(
                Decimal("0.01")
            )

        property_obj.total_purchase_price = (
            property_obj.price
            + property_obj.stamp_duty
        )

        try:

            property_obj.save()

            messages.success(
                request,
                "Property updated successfully.",
            )

            return redirect(
                "property_list"
            )

        except IntegrityError:

            messages.error(
                request,
                "Unable to update property.",
            )

    return render(
        request,
        "core/property_form.html",
        {
            "property": property_obj,
            "owners": owners,
        },
    )




    property_obj = get_object_or_404(
        Property,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "property_list"
        )

    try:

        property_obj.delete()

        messages.success(
            request,
            "Property deleted successfully.",
        )

    except ProtectedError:

        messages.error(
            request,
            "This property cannot be deleted because related rental records exist.",
        )

        
def property_delete(request, pk):

    if request.method != "POST":
        return redirect("property_list")

    try:
        property_obj = Property.objects.get(pk=pk)
        property_obj.delete()

        messages.success(
            request,
            "Property deleted successfully."
        )

    except Property.DoesNotExist:

        messages.error(
            request,
            "Property not found."
        )

    except Exception as exc:

        messages.error(
            request,
            f"Unable to delete property: {exc}"
        )

    return redirect("property_list")


# =========================================================
# TENANT MASTER DATA
# =========================================================

def tenant_list(request):

    status = request.GET.get(
        "status"
    )

    tenants = (
        Tenant.objects
        .all()
        .order_by("full_name")
    )

    # IMPORTANT:
    # Tenant model uses lowercase values:
    # active / inactive

    if status in [
        "active",
        "inactive",
    ]:

        tenants = tenants.filter(
            status=status
        )

    active_count = (
        Tenant.objects
        .filter(
            status="active"
        )
        .count()
    )

    inactive_count = (
        Tenant.objects
        .filter(
            status="inactive"
        )
        .count()
    )

    total_count = (
        Tenant.objects.count()
    )

    return render(
        request,
        "core/tenant_list.html",
        {
            "tenants": tenants,
            "active_count": active_count,
            "inactive_count": inactive_count,
            "total_count": total_count,
        },
    )
def tenant_report(request):

    tenants = (
        Tenant.objects
        .prefetch_related("contact_persons")
        .order_by("full_name")
    )

    return render(
        request,
        "core/tenant_report.html",
        {
            "tenants": tenants,
        },
    )

def tenant_detail(request, pk):

    tenant = get_object_or_404(
        Tenant,
        pk=pk,
    )

    return render(
        request,
        "core/tenant_detail.html",
        {
            "tenant": tenant,
        },
    )

def tenant_add(request):

    if request.method == "POST":

        form = TenantForm(request.POST)

        if form.is_valid():

            try:
                tenant = form.save()

                # Save multiple contact persons
                designations = request.POST.getlist("contact_designation[]")
                names = request.POST.getlist("contact_name[]")
                emails = request.POST.getlist("contact_email[]")
                phones = request.POST.getlist("contact_phone[]")
                id_types = request.POST.getlist("contact_id_type[]")
                id_numbers = request.POST.getlist("contact_id_number[]")

                for designation, name, email, phone, id_type, id_number in zip(
                    designations,
                    names,
                    emails,
                    phones,
                    id_types,
                    id_numbers,
                ):

                    # Ignore completely empty contact rows
                    if not any([
                        designation.strip(),
                        name.strip(),
                        email.strip(),
                        phone.strip(),
                        id_type.strip(),
                        id_number.strip(),
                    ]):
                        continue

                    TenantContactPerson.objects.create(
                        tenant=tenant,
                        designation=designation.strip(),
                        name=name.strip(),
                        email=email.strip(),
                        phone=phone.strip(),
                        id_type=id_type.strip(),
                        id_number=id_number.strip(),
                    )

                messages.success(
                    request,
                    "Tenant added successfully.",
                )

                return redirect("tenant_list")

            except IntegrityError:

                messages.error(
                    request,
                    "Unable to add tenant. Please check the entered information.",
                )

        return render(
            request,
            "core/tenant_form.html",
            {
                "form": form,
            },
        )

    form = TenantForm()

    return render(
        request,
        "core/tenant_form.html",
        {
            "form": form,
        },
    )

def tenant_edit(request, pk):

    tenant = get_object_or_404(
        Tenant,
        pk=pk,
    )

    contacts = tenant.contact_persons.all()

    if request.method == "POST":

        form = TenantForm(
            request.POST,
            instance=tenant,
        )

        if form.is_valid():

            try:
                tenant = form.save()

                # Get submitted contact persons
                designations = request.POST.getlist(
                    "contact_designation[]"
                )

                names = request.POST.getlist(
                    "contact_name[]"
                )

                emails = request.POST.getlist(
                    "contact_email[]"
                )

                phones = request.POST.getlist(
                    "contact_phone[]"
                )

                id_types = request.POST.getlist(
                    "contact_id_type[]"
                )

                id_numbers = request.POST.getlist(
                    "contact_id_number[]"
                )

                # Remove old contacts
                TenantContactPerson.objects.filter(
                    tenant=tenant
                ).delete()

                # Create current contacts
                for (
                    designation,
                    name,
                    email,
                    phone,
                    id_type,
                    id_number,
                ) in zip(
                    designations,
                    names,
                    emails,
                    phones,
                    id_types,
                    id_numbers,
                ):

                    designation = designation.strip()
                    name = name.strip()
                    email = email.strip()
                    phone = phone.strip()
                    id_type = id_type.strip()
                    id_number = id_number.strip()

                    # Skip completely empty rows
                    if not any([
                        designation,
                        name,
                        email,
                        phone,
                        id_type,
                        id_number,
                    ]):
                        continue

                    TenantContactPerson.objects.create(
                        tenant=tenant,
                        designation=designation,
                        name=name,
                        email=email,
                        phone=phone,
                        id_type=id_type,
                        id_number=id_number,
                    )

                messages.success(
                    request,
                    "Tenant updated successfully.",
                )

                return redirect(
                    "tenant_detail",
                    pk=tenant.pk,
                )

            except IntegrityError:

                messages.error(
                    request,
                    "Unable to update tenant.",
                )

        return render(
            request,
            "core/tenant_form.html",
            {
                "form": form,
                "tenant": tenant,
                "edit_mode": True,
                "contacts": contacts,
            },
        )

    # GET request
    form = TenantForm(
        instance=tenant,
    )

    return render(
        request,
        "core/tenant_form.html",
        {
            "form": form,
            "tenant": tenant,
            "edit_mode": True,
            "contacts": contacts,
        },
    )

def tenant_delete(request, pk):

    tenant = get_object_or_404(
        Tenant,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "tenant_list"
        )

    if LeaseAgreement.objects.filter(
        tenant=tenant
    ).exists():

        messages.error(
            request,
            "This tenant cannot be deleted because lease agreement history exists.",
        )

        return redirect(
            "tenant_list"
        )

    try:

        tenant.delete()

        messages.success(
            request,
            "Tenant deleted successfully.",
        )

    except ProtectedError:

        messages.error(
            request,
            "This tenant cannot be deleted because related records exist.",
        )

    return redirect(
        "tenant_list"
    )


# =========================================================
# RENTAL AGREEMENTS
# =========================================================

def agreement_list(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. Only Administrators can view lease agreements."
        )

    agreements = (
        LeaseAgreement.objects
        .select_related(
            "tenant",
            "property",
            "property__owner",
        )
        .all()
        .order_by("-start_date")
    )

    return render(
        request,
        "core/agreement_list.html",
        {
            "agreements": agreements,
        },
    )



def monthly_gst_report(request):
    

    today = date.today()
    ZERO = Decimal("0.00")
    CENT = Decimal("0.01")

    def money(value):
        return (value or ZERO).quantize(
            CENT, rounding=ROUND_HALF_UP
        )

    # Selected month
    try:
        month = int(request.GET.get("month", today.month))
        if not 1 <= month <= 12:
            month = today.month
    except (TypeError, ValueError):
        month = today.month

    # Selected year
    try:
        year = int(request.GET.get("year", today.year))
        if not 1900 <= year <= 2200:
            year = today.year
    except (TypeError, ValueError):
        year = today.year

    try:
        serial_start = max(1, int(request.GET.get("serial_start", 1)))
    except (TypeError, ValueError):
        serial_start = 1

    selected_owner = request.GET.get("owner", "").strip()

    month_start = date(year, month, 1)

    next_month = (
        date(year + 1, 1, 1)
        if month == 12
        else date(year, month + 1, 1)
    )

    month_end = next_month - timedelta(days=1)

    owners = Owner.objects.all().order_by("name")

    agreements = LeaseAgreement.objects.filter(
        (
            models.Q(start_date__lte=month_end)
            & (
                models.Q(end_date__isnull=True)
                | models.Q(end_date__gte=month_start)
            )
        )
        | (
            models.Q(extension_1_start_date__lte=month_end)
            & (
                models.Q(extension_1_end_date__isnull=True)
                | models.Q(extension_1_end_date__gte=month_start)
            )
        )
        | (
            models.Q(extension_2_start_date__lte=month_end)
            & (
                models.Q(extension_2_end_date__isnull=True)
                | models.Q(extension_2_end_date__gte=month_start)
            )
        )
    ).filter(
        models.Q(termination_date__isnull=True)
        | models.Q(termination_date__gte=month_start)
    ).select_related(
        "tenant", "property", "property__owner"
    ).prefetch_related(
        "rent_history"
    ).order_by(
        "tenant__full_name", "property__name", "id"
    )

    if selected_owner and selected_owner.lower() != "all":
        if selected_owner.isdigit():
            agreements = agreements.filter(
                property__owner_id=int(selected_owner)
            )
        else:
            selected_owner = ""

    report_rows = []
    taxable_total = ZERO
    cgst_total = ZERO
    sgst_total = ZERO
    invoice_total = ZERO

    serial_no = serial_start
    created_count = 0
    existing_count = 0

    for agreement in agreements:

        # Skip agreements terminated before the selected month.
        if (
            agreement.termination_date
            and agreement.termination_date < month_start
        ):
            continue

        # Check rent-free status only if the model supports it.
        # This avoids AttributeError when is_rent_free is absent.
        rent_free_checker = getattr(
            agreement, "is_rent_free", None
        )
        rent_free_end_date = getattr(
            agreement, "rent_free_end_date", None
        )

        if (
            callable(rent_free_checker)
            and rent_free_end_date
            and rent_free_end_date >= month_end
            and rent_free_checker(month_start)
        ):
            continue

        # Find the rent applicable to this month.
        rent_record = (
            agreement.rent_history.filter(
                effective_from__lte=month_end
            ).filter(
                models.Q(effective_to__isnull=True)
                | models.Q(effective_to__gte=month_start)
            ).order_by("-effective_from").first()
        )

        monthly_rent = (
            rent_record.monthly_rent
            if rent_record
            else agreement.monthly_rent or ZERO
        )

        # Apply the first extension rent when applicable.
        if (
            agreement.extension_1_start_date
            and agreement.extension_1_monthly_rent
            and agreement.extension_1_monthly_rent > ZERO
            and agreement.extension_1_start_date <= month_end
            and (
                not agreement.extension_1_end_date
                or agreement.extension_1_end_date >= month_start
            )
        ):
            monthly_rent = agreement.extension_1_monthly_rent

        # Apply the second extension rent when applicable.
        if (
            agreement.extension_2_start_date
            and agreement.extension_2_monthly_rent
            and agreement.extension_2_monthly_rent > ZERO
            and agreement.extension_2_start_date <= month_end
            and (
                not agreement.extension_2_end_date
                or agreement.extension_2_end_date >= month_start
            )
        ):
            monthly_rent = agreement.extension_2_monthly_rent

        monthly_rent = money(monthly_rent)
        parking_charge = money(agreement.parking_charge)

        taxable_amount = money(
            monthly_rent + parking_charge
        )

        cgst_rate = agreement.cgst_rate or ZERO
        sgst_rate = agreement.sgst_rate or ZERO

        cgst_amount = money(
            taxable_amount * cgst_rate / Decimal("100")
        )
        sgst_amount = money(
            taxable_amount * sgst_rate / Decimal("100")
        )

        total_amount = money(
            taxable_amount + cgst_amount + sgst_amount
        )

        tenant = agreement.tenant
        prop = agreement.property
        owner = prop.owner

        # Generate invoices only when the Generate Report
        # button is clicked.
        if request.GET.get("generate") == "1":
            from .models import Invoice, InvoiceItem

            with transaction.atomic():
                invoice = Invoice.objects.filter(
                    lease_agreement=agreement,
                    billing_from=month_start,
                    billing_to=month_end,
                ).first()

                if invoice:
                    # Preserve existing invoices and payments.
                    existing_count += 1
                else:
                    due_day = agreement.rent_due_day or 5
                    due_date = date(
                        year,
                        month,
                        min(due_day, month_end.day),
                    )

                    invoice = Invoice.objects.create(
                        tenant=tenant,
                        lease_agreement=agreement,
                        invoice_date=today,
                        billing_from=month_start,
                        billing_to=month_end,
                        payment_due_date=due_date,
                        taxable_amount=taxable_amount,
                        cgst_rate=cgst_rate,
                        cgst_amount=cgst_amount,
                        sgst_rate=sgst_rate,
                        sgst_amount=sgst_amount,
                        total_amount=total_amount,

                        tenant_name=tenant.full_name,
                        tenant_gst=getattr(
                            tenant, "gst_number", ""
                        ) or "",
                        tenant_pan=getattr(
                            tenant, "pan_number", ""
                        ) or "",
                        tenant_mobile=getattr(
                            tenant, "mobile", ""
                        ) or "",
                        tenant_email=getattr(
                            tenant, "email", ""
                        ) or "",
                        billing_address=getattr(
                            tenant, "address", ""
                        ) or "",

                        property_name=prop.name,
                        property_address=prop.address,
                        unit_number=prop.unit_no,

                        owner_name=getattr(
                            owner, "name", ""
                        ) or "",
                        owner_company_name=getattr(
                            owner, "company_name", ""
                        ) or "",
                        owner_address=getattr(
                            owner, "address", ""
                        ) or "",
                        owner_city=getattr(
                            owner, "city", ""
                        ) or "",
                        owner_state=prop.state or "",
                        owner_pincode=prop.pincode or "",
                        owner_mobile=getattr(
                            owner, "mobile", ""
                        ) or "",
                        owner_email=getattr(
                            owner, "email", ""
                        ) or "",
                        owner_gstin=getattr(
                            owner, "gstin", ""
                        ) or "",
                        owner_pan=getattr(
                            owner, "pan", ""
                        ) or "",
                    )

                    area = agreement.rental_area or ZERO

                    rate_per_sqft = (
                        money(monthly_rent / area)
                        if area > ZERO
                        else ZERO
                    )

                    # Rent invoice item.
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        item_type="rent",
                        description="Monthly Rent",
                        unit_number=prop.unit_no or "",
                        area=area,
                        rate=rate_per_sqft,
                        amount=monthly_rent,
                    )

                    # Parking invoice item.
                    if parking_charge > ZERO:
                        InvoiceItem.objects.create(
                            invoice=invoice,
                            item_type="parking",
                            description="Parking Charges",
                            unit_number=prop.unit_no or "",
                            area=ZERO,
                            rate=parking_charge,
                            amount=parking_charge,
                        )

                    created_count += 1

        report_invoice = SimpleNamespace(
            tenant=tenant,
            lease_agreement=agreement,
            tenant_name=tenant.full_name,
            tenant_gst=(
                getattr(tenant, "gst_number", "") or ""
            ).strip(),
            owner_state=(prop.state or "").strip(),
            billing_from=month_start,
            billing_to=month_end,
            taxable_amount=taxable_amount,
            cgst_amount=cgst_amount,
            sgst_amount=sgst_amount,
            total_amount=total_amount,
        )

        report_rows.append({
            "serial_no": serial_no,
            "invoice": report_invoice,
        })

        serial_no += 1

        taxable_total += taxable_amount
        cgst_total += cgst_amount
        sgst_total += sgst_amount
        invoice_total += total_amount

    totals = {
        "taxable_total": taxable_total,
        "cgst_total": cgst_total,
        "sgst_total": sgst_total,
        "invoice_total": invoice_total,
    }

    context = {
        "selected_month": month,
        "selected_year": year,
        "selected_owner": selected_owner,
        "serial_start": serial_start,
        "months": [
            (number, month_name[number])
            for number in range(1, 13)
        ],
        "years": range(2022, today.year + 16),
        "owners": owners,
        "report_rows": report_rows,
        "totals": totals,
        "created_count": created_count,
        "existing_count": existing_count,
        "report_generated": request.GET.get("generate") == "1",
    }

    return render(
        request,
        "core/monthly_gst_report.html",
        context,
    )



def agreement_add(request):
    tenants = Tenant.objects.all().order_by("full_name")
    properties = Property.objects.all().order_by("name")

    if request.method == "POST":

        # =====================================================
        # TENANT
        # =====================================================

        tenant_id = request.POST.get("tenant")

        if not tenant_id:
            messages.error(request, "Please select a Tenant.")
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        tenant = get_object_or_404(
            Tenant,
            pk=tenant_id,
        )

        # =====================================================
        # PROPERTY
        # =====================================================

        property_id = request.POST.get("property")

        if not property_id:
            messages.error(request, "Please select a Property.")
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        property_obj = get_object_or_404(
            Property,
            pk=property_id,
        )

        # =====================================================
        # CHECK ACTIVE AGREEMENT
        # =====================================================

        existing_active = LeaseAgreement.objects.filter(
            property=property_obj,
            status="active",
        ).exists()

        if existing_active:
            messages.error(
                request,
                "This property is already occupied by an active lease agreement.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        # =====================================================
        # DATES
        # =====================================================

        start_date = parse_date(
            request.POST.get("start_date")
        )

        end_date = parse_date(
            request.POST.get("end_date")
        )

        if not start_date:
            messages.error(
                request,
                "Agreement start date is required.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        if end_date and end_date < start_date:
            messages.error(
                request,
                "Agreement end date cannot be before start date.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        # =====================================================
        # MONTHLY RENT
        # =====================================================

        monthly_rent = parse_decimal(
            request.POST.get("monthly_rent")
        )

        if monthly_rent is None or monthly_rent <= ZERO:
            messages.error(
                request,
                "Please enter a valid monthly rent.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

       

        # =====================================================
        # NEXT INCREASE DATE
        # =====================================================

        next_increase_date = parse_date(
            request.POST.get("next_increase_date")
        )

        if next_increase_date:

            if next_increase_date <= start_date:
                messages.error(
                    request,
                    "Next increase date must be after agreement start date.",
                )
                return render(
                    request,
                    "core/agreement_add.html",
                    {
                        "tenants": tenants,
                        "properties": properties,
                    },
                )

            if end_date and next_increase_date > end_date:
                next_increase_date = None

        rental_area = parse_decimal(
          request.POST.get("rental_area")
        )

        if rental_area is None:
            rental_area = ZERO

        if rental_area < ZERO:
           rental_area = ZERO

        # =====================================================
        # PARKING
        # =====================================================

        parking_charge = parse_decimal(
            request.POST.get("parking_charge")
        )

        if parking_charge is None:
            parking_charge = ZERO

        if parking_charge < ZERO:
            parking_charge = ZERO

        # =====================================================
        # SECURITY DEPOSIT
        # =====================================================

        security_deposit = parse_decimal(
            request.POST.get("security_deposit")
        )

        if security_deposit is None:
            security_deposit = ZERO

        if security_deposit < ZERO:
            security_deposit = ZERO

        # =====================================================
        # GST
        # =====================================================

        cgst_rate = parse_decimal(
            request.POST.get("cgst_rate")
        )

        sgst_rate = parse_decimal(
            request.POST.get("sgst_rate")
        )

        if cgst_rate is None:
            cgst_rate = ZERO

        if sgst_rate is None:
            sgst_rate = ZERO

        if not valid_percentage(cgst_rate):
            messages.error(
                request,
                "CGST rate must be between 0 and 100.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        if not valid_percentage(sgst_rate):
            messages.error(
                request,
                "SGST rate must be between 0 and 100.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        # =====================================================
        # RENT DUE DAY
        # =====================================================

        try:
            rent_due_day = int(
                request.POST.get(
                    "rent_due_day",
                    "5",
                )
            )
        except (TypeError, ValueError):
            rent_due_day = 5

        if rent_due_day < 1 or rent_due_day > 28:
            messages.error(
                request,
                "Rent due day must be between 1 and 28.",
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        # =====================================================
        # STATUS
        # =====================================================

        status = request.POST.get(
            "status",
            "active",
        )

        if status not in {
            "active",
            "expired",
            "terminated",
        }:
            status = "active"

        # =====================================================
        # TERMINATION
        # =====================================================

        termination_date = parse_date(
            request.POST.get("termination_date")
        )

        termination_reason = request.POST.get(
            "termination_reason",
            "",
        ).strip()

        if status != "terminated":
            termination_date = None
            termination_reason = ""

        # =====================================================
        # NOTES
        # =====================================================

        notes = request.POST.get(
            "notes",
            "",
        ).strip()
        
    
        
        # =====================================================
        # LEASE EXTENSION 1
        # =====================================================

        extension_1_start_date = parse_date(
            request.POST.get("extension_1_start_date")
        )

        extension_1_end_date = parse_date(
            request.POST.get("extension_1_end_date")
        )

        extension_1_monthly_rent = parse_decimal(
            request.POST.get("extension_1_monthly_rent")
        )

        extension_1_security_deposit = parse_decimal(
            request.POST.get("extension_1_security_deposit")
        )

        # =====================================================
        # LEASE EXTENSION 2
        # =====================================================

        extension_2_start_date = parse_date(
            request.POST.get("extension_2_start_date")
        )

        extension_2_end_date = parse_date(
            request.POST.get("extension_2_end_date")
        )

        extension_2_monthly_rent = parse_decimal(
            request.POST.get("extension_2_monthly_rent")
        )

        extension_2_security_deposit = parse_decimal(
            request.POST.get("extension_2_security_deposit")
        )

        # Validate extension dates
        if (
            extension_1_start_date
            and extension_1_end_date
            and extension_1_end_date < extension_1_start_date
        ):
            messages.error(
                request,
                "Extension 1 end date cannot be before its start date."
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        if (
            extension_2_start_date
            and extension_2_end_date
            and extension_2_end_date < extension_2_start_date
        ):
            messages.error(
                request,
                "Extension 2 end date cannot be before its start date."
            )
            return render(
                request,
                "core/agreement_add.html",
                {
                    "tenants": tenants,
                    "properties": properties,
                },
            )

        # =====================================================
        # CREATE AGREEMENT
        # =====================================================

        try:
            with transaction.atomic():

                agreement = LeaseAgreement.objects.create(
                    tenant=tenant,
                    property=property_obj,
                    start_date=start_date,
                    end_date=end_date,
                    monthly_rent=monthly_rent,
                    free_parking_spaces=int(
                    request.POST.get("free_parking_spaces") or 0
                    ),
                    paid_parking_spaces=int(
                    request.POST.get("paid_parking_spaces") or 0
                    ),
                    
                    # Lease Extension 1
                    extension_1_start_date=extension_1_start_date,
                    extension_1_end_date=extension_1_end_date,
                    extension_1_monthly_rent=(
                        extension_1_monthly_rent
                        if extension_1_monthly_rent is not None
                        else ZERO
                    ),
                    extension_1_security_deposit=(
                        extension_1_security_deposit
                        if extension_1_security_deposit is not None
                        else ZERO
                    ),

                    # Lease Extension 2
                    extension_2_start_date=extension_2_start_date,
                    extension_2_end_date=extension_2_end_date,
                    extension_2_monthly_rent=(
                        extension_2_monthly_rent
                        if extension_2_monthly_rent is not None
                        else ZERO
                    ),
                    extension_2_security_deposit=(
                        extension_2_security_deposit
                        if extension_2_security_deposit is not None
                        else ZERO
                    ),
                    rental_area=rental_area,


                    parking_charge=parking_charge,
                    security_deposit=security_deposit,

                    cgst_rate=cgst_rate,
                    sgst_rate=sgst_rate,

                    rent_due_day=rent_due_day,

                    status=status,

                    termination_date=(
                        termination_date
                    ),
                    termination_reason=(
                        termination_reason
                    ),

                    notes=notes,
                )

                lease_document=request.FILES.get("lease_document"),

                # =================================================
                # INITIAL RENT HISTORY
                # =================================================

                RentHistory.objects.create(
                    lease_agreement=agreement,
                    effective_from=start_date,
                    effective_to=None,
                    monthly_rent=monthly_rent,
                    increase_percent=ZERO,
                    increase_accepted=True,
                )

            messages.success(
                request,
                "Lease Agreement created successfully.",
            )

            return redirect("agreement_list")

        except IntegrityError as e:
            messages.error(
                request,
                f"Unable to create the Lease Agreement: {e}",
            )

    # =========================================================
    # GET REQUEST
    # =========================================================

    return render(
        request,
        "core/agreement_add.html",
        {
            "tenants": tenants,
            "properties": properties,
        },
    )





    # =========================================================
    # GET
    # =========================================================

    return render(
        request,
        "core/agreement_add.html",
        {
            "tenants": tenants,
            "properties": properties,
        }
    )

def agreement_edit(request, pk):

    agreement = get_object_or_404(
        LeaseAgreement.objects.select_related(
            "tenant",
            "property",
        ),
        pk=pk,
    )

    tenants = Tenant.objects.all().order_by("full_name")
    properties = Property.objects.all().order_by("name")

    if request.method == "POST":

        # =====================================================
        # TENANT
        # =====================================================

        tenant_id = request.POST.get("tenant")

        if not tenant_id:
            messages.error(request, "Please select a Tenant.")
        else:
            agreement.tenant = get_object_or_404(
                Tenant,
                pk=tenant_id,
            )

        # =====================================================
        # PROPERTY
        # =====================================================

        property_id = request.POST.get("property")

        if not property_id:
            messages.error(request, "Please select a Property.")
        else:
            agreement.property = get_object_or_404(
                Property,
                pk=property_id,
            )

        # =====================================================
        # ORIGINAL LEASE DATES
        # =====================================================

        start_date = parse_date(
            request.POST.get("start_date")
        )

        end_date = parse_date(
            request.POST.get("end_date")
        )

        if not start_date:
            messages.error(
                request,
                "Agreement start date is required.",
            )
        else:
            agreement.start_date = start_date

        if end_date and start_date and end_date < start_date:
            messages.error(
                request,
                "Agreement end date cannot be before start date.",
            )
        else:
            agreement.end_date = end_date

        # =====================================================
        # ORIGINAL MONTHLY RENT
        # =====================================================

        monthly_rent = parse_decimal(
            request.POST.get("monthly_rent")
        )

        if monthly_rent is not None and monthly_rent >= ZERO:
            agreement.monthly_rent = monthly_rent
        else:
            messages.error(
                request,
                "Please enter a valid monthly rent.",
            )

        # =====================================================
        # LOCK-IN
        # =====================================================

        lock_in_months = request.POST.get("lock_in_months")

        try:
            agreement.lock_in_months = int(
                lock_in_months
            ) if lock_in_months else 0
        except (TypeError, ValueError):
            agreement.lock_in_months = 0
            messages.error(
                request,
                "Please enter a valid lock-in period.",
            )

        # =====================================================
        # RENT-FREE PERIOD
        # =====================================================

        rent_free_months = request.POST.get(
            "rent_free_months"
        )

        try:
            agreement.rent_free_months = int(
                rent_free_months
            ) if rent_free_months else 0
        except (TypeError, ValueError):
            agreement.rent_free_months = 0
            messages.error(
                request,
                "Please enter a valid rent-free period.",
            )

        # =====================================================
        # LEASE EXTENSION 1
        # =====================================================

        extension_1_start_date = parse_date(
            request.POST.get("extension_1_start_date")
        )

        extension_1_end_date = parse_date(
            request.POST.get("extension_1_end_date")
        )

        extension_1_monthly_rent = parse_decimal(
            request.POST.get("extension_1_monthly_rent")
        )

        extension_1_security_deposit = parse_decimal(
            request.POST.get("extension_1_security_deposit")
        )

        agreement.extension_1_start_date = (
            extension_1_start_date
        )

        agreement.extension_1_end_date = (
            extension_1_end_date
        )

        agreement.extension_1_monthly_rent = (
            extension_1_monthly_rent
            if extension_1_monthly_rent is not None
            else ZERO
        )

        agreement.extension_1_security_deposit = (
            extension_1_security_deposit
            if extension_1_security_deposit is not None
            else ZERO
        )

        if (
            extension_1_start_date
            and extension_1_end_date
            and extension_1_end_date < extension_1_start_date
        ):
            messages.error(
                request,
                "Extension 1 end date cannot be before start date.",
            )

        # =====================================================
        # LEASE EXTENSION 2
        # =====================================================

        extension_2_start_date = parse_date(
            request.POST.get("extension_2_start_date")
        )

        extension_2_end_date = parse_date(
            request.POST.get("extension_2_end_date")
        )

        extension_2_monthly_rent = parse_decimal(
            request.POST.get("extension_2_monthly_rent")
        )

        extension_2_security_deposit = parse_decimal(
            request.POST.get("extension_2_security_deposit")
        )

        agreement.extension_2_start_date = (
            extension_2_start_date
        )

        agreement.extension_2_end_date = (
            extension_2_end_date
        )

        agreement.extension_2_monthly_rent = (
            extension_2_monthly_rent
            if extension_2_monthly_rent is not None
            else ZERO
        )

        agreement.extension_2_security_deposit = (
            extension_2_security_deposit
            if extension_2_security_deposit is not None
            else ZERO
        )

        if (
            extension_2_start_date
            and extension_2_end_date
            and extension_2_end_date < extension_2_start_date
        ):
            messages.error(
                request,
                "Extension 2 end date cannot be before start date.",
            )

        # =====================================================
        # PARKING
        # =====================================================

        parking_charge = parse_decimal(
            request.POST.get("parking_charge")
        )

        free_parking_spaces = request.POST.get(
            "free_parking_spaces"
        )

        paid_parking_spaces = request.POST.get(
            "paid_parking_spaces"
        )

        agreement.parking_charge = (
            parking_charge
            if parking_charge is not None
            else ZERO
        )

        try:
            agreement.free_parking_spaces = int(
                free_parking_spaces
            ) if free_parking_spaces else 0
        except (TypeError, ValueError):
            agreement.free_parking_spaces = 0
            messages.error(
                request,
                "Please enter a valid number of free parking spaces.",
            )

        try:
            agreement.paid_parking_spaces = int(
                paid_parking_spaces
            ) if paid_parking_spaces else 0
        except (TypeError, ValueError):
            agreement.paid_parking_spaces = 0
            messages.error(
                request,
                "Please enter a valid number of paid parking spaces.",
            )

        # =====================================================
        # SECURITY DEPOSIT
        # =====================================================

        security_deposit = parse_decimal(
            request.POST.get("security_deposit")
        )

        if security_deposit is not None and security_deposit >= ZERO:
            agreement.security_deposit = security_deposit
        else:
            agreement.security_deposit = ZERO
            messages.error(
                request,
                "Please enter a valid security deposit.",
            )

        # =====================================================
        # GST
        # =====================================================

        cgst_rate = parse_decimal(
            request.POST.get("cgst_rate")
        )

        sgst_rate = parse_decimal(
            request.POST.get("sgst_rate")
        )

        agreement.cgst_rate = (
            cgst_rate
            if cgst_rate is not None
            else ZERO
        )

        agreement.sgst_rate = (
            sgst_rate
            if sgst_rate is not None
            else ZERO
        )

        # =====================================================
        # PAYMENT SETTINGS
        # =====================================================

        rent_due_day = request.POST.get("rent_due_day")

        try:
            rent_due_day = int(rent_due_day)

            if not 1 <= rent_due_day <= 31:
                raise ValueError

            agreement.rent_due_day = rent_due_day

        except (TypeError, ValueError):
            messages.error(
                request,
                "Rent due day must be between 1 and 31.",
            )

        # =====================================================
        # STATUS
        # =====================================================

        status = request.POST.get("status")

        if status in dict(LeaseAgreement.AGREEMENT_STATUS):
            agreement.status = status

        # =====================================================
        # TERMINATION
        # =====================================================

        termination_date = parse_date(
            request.POST.get("termination_date")
        )

        agreement.termination_date = termination_date

        agreement.termination_reason = (
            request.POST.get("termination_reason", "").strip()
        )

        # =====================================================
        # NOTES
        # =====================================================

        agreement.notes = (
            request.POST.get("notes", "").strip()
        )

        form = AgreementForm(
        request.POST or None,
        request.FILES or None,
        instance=agreement,  # Use your existing instance variable.
        )

        # =====================================================
        # SAVE
        # =====================================================

        if not any(
            message.level == messages.ERROR
            for message in messages.get_messages(request)
        ):
            agreement.save()

            messages.success(
                request,
                "Lease agreement updated successfully.",
            )

            return redirect(
                "agreement_view",
                pk=agreement.pk,
            )

    # =========================================================
    # GET / INVALID POST
    # =========================================================

    return render(
        request,
        "core/agreement_edit.html",
        {
            "agreement": agreement,
            "tenants": tenants,
            "properties": properties,
        },
    )

def agreement_view(request, pk):

    agreement = get_object_or_404(
        LeaseAgreement.objects.select_related(
            "tenant",
            "property",
            "property__owner",
        ),
        pk=pk,
    )

    contact_persons = agreement.tenant.contact_persons.all()

    return render(
        request,
        "core/agreement_view.html",
        {
            "agreement": agreement,
            "contact_persons": contact_persons,
        }
    )


# =========================================================
# RENTAL AGREEMENT TERMINATION
# =========================================================

def agreement_terminate(request, pk):
    """
    Terminate an active rental agreement.

    Existing invoices and payments are preserved.
    """

    agreement = get_object_or_404(
        LeaseAgreement.objects.select_related(
            "tenant",
            "property",
        ),
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "agreement_list"
        )

    if agreement.status != "active":

        messages.warning(
            request,
            "This rental agreement is already terminated or expired.",
        )

        return redirect(
            "agreement_list"
        )

    termination_date = parse_date(
        request.POST.get(
            "termination_date"
        )
    ) or date.today()

    termination_reason = request.POST.get(
        "termination_reason",
        "",
    ).strip()

    if termination_date < agreement.start_date:

        messages.error(
            request,
            "Termination date cannot be before agreement start date.",
        )

        return redirect(
            "agreement_list"
        )

    with transaction.atomic():

        locked_agreement = (
            LeaseAgreement.objects
            .select_for_update()
            .get(
                pk=agreement.pk
            )
        )

        locked_agreement.status = (
            "terminated"
        )

        locked_agreement.end_date = (
            termination_date
        )

        locked_agreement.termination_date = (
            termination_date
        )

        locked_agreement.termination_reason = (
            termination_reason
        )

        locked_agreement.increase_pending = (
            False
        )

        locked_agreement.save(
            update_fields=[
                "status",
                "end_date",
                "termination_date",
                "termination_reason",
                "increase_pending",
                "updated_at",
            ]
        )

    messages.success(
        request,
        "Rental agreement terminated successfully. The property is now available.",
    )

    return redirect(
        "agreement_list"
    )


def agreement_delete(request, pk):

    agreement = get_object_or_404(
        LeaseAgreement,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "agreement_list"
        )

    if Invoice.objects.filter(
        lease_agreement=agreement
    ).exists():

        messages.error(
            request,
            "This agreement cannot be deleted because invoices are linked to it. Use Terminate instead.",
        )

        return redirect(
            "agreement_list"
        )

    try:

        agreement.delete()

        messages.success(
            request,
            "Rental agreement deleted successfully.",
        )

    except ProtectedError:

        messages.error(
            request,
            "This agreement cannot be deleted because related records exist.",
        )

    return redirect(
        "agreement_list"
    )


# =========================================================
# RENT INCREASE CHECK
# =========================================================

def is_rent_increase_due(
    agreement,
    billing_date,
):
   

    if (
        agreement.rent_increase_percentage
        <= ZERO
    ):
        return False

    if not agreement.next_increase_date:
        return False

    if (
        agreement.end_date
        and billing_date > agreement.end_date
    ):
        return False

    return (
        billing_date
        >= agreement.next_increase_date
    )


# =========================================================
# APPLY RENT INCREASE
# =========================================================

def apply_rent_increase(
    agreement,
    effective_date,
):
    """
    Apply the pending rent increase.

    Example:

        Current rent = 100
        Increase = 10%

        New rent = 110

    The next increase date is calculated from
    the date on which the increase was actually accepted.
    """

    current_rent = (
        parse_decimal(
            agreement.monthly_rent
        )
    )

    increase_percentage = (
        parse_decimal(
            agreement.rent_increase_percentage
        )
    )

    increase_amount = (
        current_rent
        * increase_percentage
        / ONE_HUNDRED
    )

    new_rent = (
        current_rent
        + increase_amount
    ).quantize(
        Decimal("0.01")
    )

    agreement.monthly_rent = new_rent

    agreement.increase_pending = False

    # -----------------------------------------------------
    # NEXT INCREASE
    # -----------------------------------------------------

    next_date = add_months(
        effective_date,
        agreement.rent_increase_frequency_months,
    )

    if (
        agreement.end_date
        and next_date > agreement.end_date
    ):

        agreement.next_increase_date = None

    else:

        agreement.next_increase_date = (
            next_date
        )

    agreement.save(
        update_fields=[
            "monthly_rent",
            "increase_pending",
            "next_increase_date",
            "updated_at",
        ]
    )

    return new_rent


# =========================================================
# INVOICE GENERATION
# =========================================================

def generate_invoice(request, agreement_id):
    agreement = get_object_or_404(
        LeaseAgreement.objects.select_related(
            "tenant",
            "property",
            "property__owner",
        ),
        pk=agreement_id,
    )

    if agreement.status != "active":
        messages.error(
            request,
            "Invoice can only be generated for an active lease agreement.",
        )
        return redirect("agreement_list")

    today = date.today()

    # GET: display invoice generation form
    if request.method == "GET":
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": today.strftime("%Y-%m"),
            },
        )

    # BILLING MONTH
    billing_month_input = request.POST.get(
        "billing_month", ""
    ).strip()

    if not billing_month_input:
        messages.error(request, "Please select a billing month.")
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": "",
            },
        )

    try:
        billing_year, billing_month = map(
            int, billing_month_input.split("-")
        )

        billing_from = date(
            billing_year, billing_month, 1
        )

        billing_to = date(
            billing_year,
            billing_month,
            monthrange(billing_year, billing_month)[1],
        )

    except (ValueError, TypeError):
        messages.error(request, "Invalid billing month selected.")
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": billing_month_input,
            },
        )

    # AGREEMENT DATE VALIDATION
    if billing_to < agreement.start_date:
        messages.error(
            request,
            "The selected billing month is before the rental agreement started.",
        )
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": billing_month_input,
            },
        )

    if agreement.end_date and billing_from > agreement.end_date:
        messages.error(
            request,
            "The selected billing month is after the rental agreement ended.",
        )
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": billing_month_input,
            },
        )

    # ACTUAL BILLABLE PERIOD
    actual_billing_from = max(
        billing_from, agreement.start_date
    )

    actual_billing_to = billing_to

    if agreement.end_date:
        actual_billing_to = min(
            billing_to, agreement.end_date
        )

    if actual_billing_from > actual_billing_to:
        messages.error(
            request,
            "There are no billable days in the selected month.",
        )
        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": billing_month_input,
            },
        )

    bill_days = (
        actual_billing_to - actual_billing_from
    ).days + 1

    days_in_month = monthrange(
        billing_year, billing_month
    )[1]

    # PREVENT DUPLICATE INVOICES
    existing_invoice = Invoice.objects.filter(
        lease_agreement=agreement,
        billing_from=actual_billing_from,
        billing_to=actual_billing_to,
    ).first()

    if existing_invoice:
        messages.warning(
            request,
            "Invoice for this billing period already exists.",
        )
        return redirect(
            "invoice_detail",
            pk=existing_invoice.invoice_number,
        )

    # TERM CALCULATION
    current_term = agreement.get_current_term(
        actual_billing_from
    )

    proposed_rent = parse_decimal(
        agreement.get_term_rent(current_term)
    )

    increase_percent = parse_decimal(
        agreement.get_current_increase_percent(
            actual_billing_from
        )
    )

    # Resolve the effective start date for the current term.
    if current_term == 1:
        term_start_date = agreement.start_date
    else:
        term_start_date = (
            getattr(
                agreement,
                f"term{current_term}_start_date",
                None,
            )
            or agreement.start_date
        )

    # RENT INCREASE HISTORY
    accepted_history = RentHistory.objects.filter(
        lease_agreement=agreement,
        effective_from=term_start_date,
        increase_accepted=True,
    ).order_by("-created_at").first()

    increase_already_accepted = bool(accepted_history)

    # PREVIOUS TERM RENT
    if current_term == 1:
        previous_rent = parse_decimal(
            agreement.monthly_rent
        )
    else:
        previous_rent = parse_decimal(
            agreement.get_term_rent(current_term - 1)
        )

    # RENT INCREASE CONFIRMATION
    rent_decision = request.POST.get(
        "rent_increase_decision", ""
    ).strip().lower()

    if not increase_already_accepted:
        if rent_decision not in {"yes", "no"}:
            return render(
                request,
                "core/invoice_rent_confirmation.html",
                {
                    "agreement": agreement,
                    "selected_month": billing_month_input,
                    "current_term": current_term,
                    "previous_rent": previous_rent,
                    "proposed_rent": proposed_rent,
                    "increase_percent": increase_percent,
                    "increase_amount": (
                        proposed_rent - previous_rent
                    ).quantize(
                        Decimal("0.01"),
                        rounding=ROUND_HALF_UP,
                    ),
                },
            )

        if rent_decision == "yes":
            monthly_rent = proposed_rent
            accept_increase = True
        else:
            monthly_rent = previous_rent
            accept_increase = False

    else:
        monthly_rent = proposed_rent
        accept_increase = False

    monthly_rent = parse_decimal(monthly_rent)

    # SAVE RENT HISTORY WHEN INCREASE IS ACCEPTED
    if accept_increase:
        RentHistory.objects.filter(
            lease_agreement=agreement,
            effective_to__isnull=True,
            effective_from__lt=term_start_date,
        ).update(
            effective_to=term_start_date - date.resolution
        )

        if current_term < 5:
            next_term_date = getattr(
                agreement,
                f"term{current_term + 1}_start_date",
                None,
            )

            if next_term_date:
                effective_to = (
                    next_term_date - date.resolution
                )
            else:
                effective_to = agreement.end_date
        else:
            effective_to = agreement.end_date

        if (
            agreement.end_date
            and effective_to
            and effective_to > agreement.end_date
        ):
            effective_to = agreement.end_date

        RentHistory.objects.update_or_create(
            lease_agreement=agreement,
            effective_from=term_start_date,
            defaults={
                "effective_to": effective_to,
                "monthly_rent": monthly_rent,
                "increase_percent": increase_percent,
                "increase_accepted": True,
            },
        )

    # =========================================================
    # PARKING CALCULATION
    # =========================================================
    free_parking_slots = int(
        agreement.free_parking_spaces or 0
    )

    paid_parking_slots = int(
        agreement.paid_parking_spaces or 0
    )

    # parking_charge must be the price of ONE paid slot.
    parking_rate = parse_decimal(
        agreement.parking_charge
    )

    parking_amount = (
        parking_rate * Decimal(paid_parking_slots)
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # PRORATED RENT
    if (
        actual_billing_from == billing_from
        and actual_billing_to == billing_to
    ):
        rent_amount = monthly_rent
    else:
        rent_amount = (
            monthly_rent
            * Decimal(bill_days)
            / Decimal(days_in_month)
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # TAXABLE AMOUNT
    taxable_amount = (
        rent_amount + parking_amount
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # GST
    cgst_rate = parse_decimal(agreement.cgst_rate)
    sgst_rate = parse_decimal(agreement.sgst_rate)

    cgst_amount = (
        taxable_amount * cgst_rate / ONE_HUNDRED
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    sgst_amount = (
        taxable_amount * sgst_rate / ONE_HUNDRED
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    total_amount = (
        taxable_amount + cgst_amount + sgst_amount
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # PAYMENT DUE DATE
    payment_due_day = min(
        agreement.rent_due_day,
        days_in_month,
    )

    payment_due_date = date(
        billing_year,
        billing_month,
        payment_due_day,
    )

    # OWNER AND PROPERTY DETAILS
    owner = agreement.property.owner
    tenant = agreement.tenant
    property_obj = agreement.property

    owner_gst = ""
    if owner:
        owner_gst = (
            getattr(owner, "gst_haryana", "")
            or getattr(owner, "gst_delhi", "")
            or ""
        )

    # CREATE INVOICE AND ITEMS ATOMICALLY
    with transaction.atomic():
        invoice = Invoice.objects.create(
            lease_agreement=agreement,
            tenant=tenant,
            invoice_date=today,
            billing_from=actual_billing_from,
            billing_to=actual_billing_to,
            payment_due_date=payment_due_date,
            taxable_amount=taxable_amount,
            cgst_rate=cgst_rate,
            cgst_amount=cgst_amount,
            sgst_rate=sgst_rate,
            sgst_amount=sgst_amount,
            total_amount=total_amount,
            status="pending",

            # Tenant snapshot
            tenant_name=tenant.full_name,
            tenant_gst="",
            tenant_pan="",
            tenant_mobile=tenant.mobile,
            tenant_email=tenant.email,
            billing_address=tenant.permanent_address,

            # Property snapshot
            property_name=property_obj.name,
            property_address=property_obj.address,
            unit_number=getattr(
                property_obj, "unit_no", ""
            ),

            # Owner snapshot
            owner_name=owner.name if owner else "",
            owner_company_name="",
            owner_address=owner.address if owner else "",
            owner_city=owner.city if owner else "",
            owner_state=owner.state if owner else "",
            owner_pincode=owner.pincode if owner else "",
            owner_mobile=owner.mobile if owner else "",
            owner_email=owner.email if owner else "",
            owner_gstin=owner_gst,
            owner_pan=owner.pan if owner else "",
        )

        # RENT ITEM
        if (
            actual_billing_from == billing_from
            and actual_billing_to == billing_to
        ):
            rent_description = (
                f"Monthly Rent - Term {current_term}"
            )
        else:
            rent_description = (
                f"Rent - Term {current_term} "
                f"({actual_billing_from.strftime('%d %b %Y')} - "
                f"{actual_billing_to.strftime('%d %b %Y')})"
            )

        InvoiceItem.objects.create(
            invoice=invoice,
            item_type="rent",
            description=rent_description,
            unit_number=getattr(
                property_obj, "unit_no", ""
            ),
            area=ZERO,
            rate=monthly_rent,
            slots=1,
            bill_days=bill_days,
            available_days=bill_days,
            amount=rent_amount,
        )

        # PARKING ITEM
        if paid_parking_slots > 0 and parking_amount > ZERO:
            parking_description = (
                f"Parking Charges - {paid_parking_slots} Paid Slots "
                f"x ₹{parking_rate:.2f} per slot; "
                f"{free_parking_slots} Free Slots"
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                item_type="parking",
                description=parking_description,
                unit_number=getattr(
                    property_obj, "unit_no", ""
                ),
                area=ZERO,
                rate=parking_rate,
                slots=paid_parking_slots,
                bill_days=bill_days,
                available_days=bill_days,
                amount=parking_amount,
            )

    # SUCCESS MESSAGE
    if accept_increase:
        success_text = (
            f"Invoice #{invoice.invoice_number} generated successfully. "
            f"Term {current_term} rent increase accepted. "
            f"Rent: ₹{monthly_rent:.2f}"
        )
    elif (
        not increase_already_accepted
        and rent_decision == "no"
    ):
        success_text = (
            f"Invoice #{invoice.invoice_number} generated successfully. "
            "Rent increase was not applied for this month. "
            f"Rent: ₹{monthly_rent:.2f}. "
            "You will be asked again next month."
        )
    else:
        success_text = (
            f"Invoice #{invoice.invoice_number} generated successfully. "
            f"Term {current_term} rent: ₹{monthly_rent:.2f}"
        )

    messages.success(request, success_text)

    return redirect(
        "invoice_detail",
        pk=invoice.invoice_number,
    )



# =========================================================
# INVOICES
# =========================================================

def invoice_list(request):
    base_invoices = (
        Invoice.objects
        .select_related(
            "tenant",
            "lease_agreement",
            "lease_agreement__property",
        )
        .all()
        .order_by("-invoice_date", "-invoice_number")
    )

    # Build month options from existing invoice billing dates.
    month_options = []
    seen_months = set()

    for billing_date in base_invoices.values_list(
        "billing_from", flat=True
    ).order_by("-billing_from"):
        month_value = billing_date.strftime("%Y-%m")

        if month_value not in seen_months:
            seen_months.add(month_value)
            month_options.append({
                "value": month_value,
                "label": billing_date.strftime("%B %Y"),
            })

    # Owner names are stored as snapshots on Invoice.
    owner_options = list(
        base_invoices
        .exclude(owner_name="")
        .exclude(owner_name__isnull=True)
        .values_list("owner_name", flat=True)
        .distinct()
        .order_by("owner_name")
    )

    # Default: pending/unpaid invoices.
    selected_status = request.GET.get("status", "pending").lower()
    selected_month = request.GET.get("month", "").strip()
    selected_owner = request.GET.get("owner", "").strip()
    if "month" in request.GET:
        selected_month = request.GET.get("month", "").strip()
    else:
        selected_month = timezone.localdate().strftime("%Y-%m")

    if selected_status not in ("all", "pending", "paid"):
        selected_status = "pending"

    invoices = base_invoices

    # Filter by billing month.
    if selected_month:
        try:
            month_date = datetime.strptime(
                selected_month, "%Y-%m"
            ).date()

            invoices = invoices.filter(
                billing_from__year=month_date.year,
                billing_from__month=month_date.month,
            )
        except ValueError:
            selected_month = ""

    # Filter by owner.
    if selected_owner in owner_options:
        invoices = invoices.filter(owner_name=selected_owner)
    else:
        selected_owner = ""

    # Filter by payment status.
    if selected_status == "pending":
        invoices = (
            invoices
            .exclude(status__iexact="paid")
            .exclude(status__iexact="cancelled")
        )
    elif selected_status == "paid":
        invoices = invoices.filter(status__iexact="paid")

    # Calculate paid amount and outstanding balance for each invoice.
    for invoice in invoices:
        invoice.total_paid = get_invoice_total_paid(invoice)
        invoice.balance = max(
            invoice.total_amount - invoice.total_paid,
            ZERO,
        )

    # Summary cards reflect the selected filters.
    total_invoices = invoices.count()

    paid_count = invoices.filter(
        status__iexact="paid"
    ).count()

    pending_count = (
        invoices
        .exclude(status__iexact="paid")
        .exclude(status__iexact="cancelled")
        .count()
    )

    total_invoiced = (
        invoices
        .exclude(status__iexact="cancelled")
        .aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    return render(
        request,
        "core/invoice_list.html",
        {
            "invoices": invoices,
            "total_invoices": total_invoices,
            "paid_count": paid_count,
            "pending_count": pending_count,
            "total_invoiced": total_invoiced,
            "month_options": month_options,
            "owner_options": owner_options,
            "selected_month": selected_month,
            "selected_owner": selected_owner,
            "selected_status": selected_status,
        },
    )




def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects
        .select_related(
            "tenant",
            "lease_agreement",
            "lease_agreement__property",
        )
        .prefetch_related("items", "payments"),
        invoice_number=pk,
    )

    total_paid = get_invoice_total_paid(invoice)
    tds_amount = get_invoice_tds_amount(invoice)
    tds_credited = get_invoice_tds_credited(invoice)
    net_payable = get_invoice_net_payable(invoice)
    cash_balance = get_invoice_cash_balance(invoice)

    # Accounting balance includes TDS only after it is credited.
    balance = max(
        invoice.total_amount - total_paid - tds_credited,
        ZERO,
    )

    return render(
        request,
        "core/invoice_detail.html",
        {
            "invoice": invoice,
            "total_paid": total_paid,
            "tds_amount": tds_amount,
            "tds_credited": tds_credited,
            "net_payable": net_payable,
            "cash_balance": cash_balance,
            "balance": balance,
        },
    )

# =========================================================
# INVOICE PDF
# =========================================================

def invoice_pdf(request, pk):

    invoice = get_object_or_404(
        Invoice.objects
        .select_related(
            "tenant",
            "lease_agreement",
            "lease_agreement__property",
        )
        .prefetch_related(
            "items",
            "payments",
        ),
        invoice_number=pk,
    )

    total_paid = (
        get_invoice_total_paid(
            invoice
        )
    )

    balance = max(
        invoice.total_amount
        - total_paid,
        ZERO,
    )

    html = render(
        request,
        "core/invoice_pdf.html",
        {
            "invoice": invoice,
            "total_paid": total_paid,
            "balance": balance,
        },
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
    )

    pisa_status = pisa.CreatePDF(
        html.content,
        dest=response,
    )

    if pisa_status.err:

        return HttpResponse(
            "Unable to generate PDF.",
            status=500,
        )

    return response


# =========================================================
# PAYMENTS
# =========================================================

def payment_list(request):

    payments = (
        Payment.objects
        .select_related(
            "invoice",
            "invoice__tenant",
        )
        .all()
        .order_by(
            "-payment_date",
            "-id",
        )
    )

    return render(
        request,
        "core/payment_list.html",
        {
            "payments": payments,
        },
    )





def record_payment(request, invoice_id):
    invoice = get_object_or_404(
        Invoice,
        invoice_number=invoice_id,
    )

    if invoice.status == "cancelled":
        messages.error(
            request,
            "Payment cannot be recorded against a cancelled invoice.",
        )
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    # -----------------------------------------------------
    # RENT + PARKING BREAKDOWN (BEFORE GST)
    # -----------------------------------------------------
    items = invoice.items.all()

    rent_amount = (
        items.filter(item_type="rent")
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    parking_amount = (
        items.filter(item_type="parking")
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    tds_base_amount = rent_amount + parking_amount

    # -----------------------------------------------------
    # DISPLAY PAYMENT FORM
    # -----------------------------------------------------
    if request.method == "GET":
        total_paid = get_invoice_total_paid(invoice)

        # This helper must use rent + parking before GST.
        tds_amount = get_invoice_tds_amount(invoice)

        net_payable = max(
            invoice.total_amount - tds_amount,
            ZERO,
        )

        balance = max(
            net_payable - total_paid,
            ZERO,
        )

        if balance <= ZERO:
            messages.warning(
                request,
                "The net payable amount has already been paid.",
            )
            return redirect(
                "invoice_detail",
                pk=invoice.invoice_number,
            )

        return render(
            request,
            "core/payment_form.html",
            {
                "invoice": invoice,
                "balance": balance,
                "total_paid": total_paid,
                "tds_amount": tds_amount,
                "net_payable": net_payable,
                "rent_amount": rent_amount,
                "parking_amount": parking_amount,
                "tds_base_amount": tds_base_amount,
                "today": date.today(),
            },
        )

    # -----------------------------------------------------
    # READ SUBMITTED PAYMENT DETAILS
    # -----------------------------------------------------
    payment_amount = parse_decimal(
        request.POST.get("amount")
    )

    payment_date = parse_date(
        request.POST.get("payment_date")
    ) or date.today()

    payment_method = request.POST.get(
        "payment_method", ""
    ).strip()

    transaction_reference = request.POST.get(
        "transaction_reference", ""
    ).strip()

    notes = request.POST.get("notes", "").strip()

    if payment_amount <= ZERO:
        messages.error(
            request,
            "Payment amount must be greater than zero.",
        )
        return redirect(
            "record_payment",
            invoice_id=invoice.invoice_number,
        )

    # -----------------------------------------------------
    # VALIDATE AND SAVE PAYMENT ATOMICALLY
    # -----------------------------------------------------
    with transaction.atomic():
        locked_invoice = (
            Invoice.objects
            .select_for_update()
            .get(invoice_number=invoice.invoice_number)
        )

        if locked_invoice.status == "cancelled":
            messages.error(
                request,
                "Payment cannot be recorded against a cancelled invoice.",
            )
            return redirect(
                "invoice_detail",
                pk=locked_invoice.invoice_number,
            )

        locked_total_paid = (
            Payment.objects
            .filter(invoice=locked_invoice)
            .aggregate(total=Sum("amount"))
            .get("total")
            or ZERO
        )

        # IMPORTANT:
        # get_invoice_tds_amount() must calculate 10% of
        # rent + parking before GST.
        locked_tds_amount = get_invoice_tds_amount(
            locked_invoice
        )

        locked_net_payable = max(
            locked_invoice.total_amount - locked_tds_amount,
            ZERO,
        )

        locked_balance = max(
            locked_net_payable - locked_total_paid,
            ZERO,
        )

        if locked_balance <= ZERO:
            messages.warning(
                request,
                "The net payable amount has already been paid.",
            )
            return redirect(
                "invoice_detail",
                pk=locked_invoice.invoice_number,
            )

        if payment_amount > locked_balance:
            messages.error(
                request,
                (
                    "Payment cannot exceed the outstanding "
                    f"net payable balance of ₹{locked_balance:,.2f}."
                ),
            )
            return redirect(
                "record_payment",
                invoice_id=locked_invoice.invoice_number,
            )

        Payment.objects.create(
            invoice=locked_invoice,
            payment_date=payment_date,
            amount=payment_amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            notes=notes,
        )

        new_total_paid = locked_total_paid + payment_amount

        remaining_net_payable = max(
            locked_net_payable - new_total_paid,
            ZERO,
        )

        if remaining_net_payable == ZERO:
            locked_invoice.status = "paid"
            locked_invoice.payment_date = payment_date
        else:
            locked_invoice.status = "pending"
            locked_invoice.payment_date = None

        locked_invoice.save(
            update_fields=["status", "payment_date"]
        )

    messages.success(
        request,
        f"Payment of ₹{payment_amount:,.2f} recorded successfully.",
    )

    return redirect(
        "invoice_detail",
        pk=invoice.invoice_number,
    )






def payment_receipt(request, payment_id):
    payment = get_object_or_404(
        Payment.objects.select_related(
            "invoice",
            "invoice__tenant",
        ),
        pk=payment_id,
    )

    invoice = payment.invoice

    total_paid = get_invoice_total_paid(invoice)
    tds_amount = get_invoice_tds_amount(invoice)
    credited_tds = get_invoice_tds_credited(invoice)

    balance = max(
        invoice.total_amount - total_paid - credited_tds,
        ZERO,
    )

    html = render(
        request,
        "core/payment_receipt.html",
        {
            "payment": payment,
            "invoice": invoice,
            "total_paid": total_paid,
            "tds_amount": tds_amount,
            "credited_tds": credited_tds,
            "balance": balance,
        },
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="payment_receipt_{payment.id}.pdf"'
    )

    pisa_status = pisa.CreatePDF(
        html.content,
        dest=response,
    )

    if pisa_status.err:
        return HttpResponse(
            "Unable to generate payment receipt.",
            status=500,
        )

    return response




def invoice_payment_history(request, invoice_id):
    invoice = get_object_or_404(
        Invoice,
        invoice_number=invoice_id,
    )

    payments = Payment.objects.filter(
        invoice=invoice
    ).order_by("-payment_date", "-id")

    total_paid = (
        payments.aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    tds_amount = get_invoice_tds_amount(invoice)
    credited_tds = get_invoice_tds_credited(invoice)

    balance = max(
        invoice.total_amount - total_paid - credited_tds,
        ZERO,
    )

    return render(
        request,
        "core/invoice_payment_history.html",
        {
            "invoice": invoice,
            "payments": payments,
            "total_paid": total_paid,
            "tds_amount": tds_amount,
            "credited_tds": credited_tds,
            "balance": balance,
        },
    )


# =========================================================
# DASHBOARD
# =========================================================

@login_required
def dashboard(request):

    # =====================================================
    # STAFF DASHBOARD
    # =====================================================
    if not request.user.is_superuser:
        unpaid_property_taxes = (
            PropertyTax.objects
            .filter(status="unpaid")
            .select_related("property")
            .order_by("tax_year")
        )

        return render(
            request,
            "core/staff_dashboard.html",
            {
                "unpaid_property_taxes": unpaid_property_taxes,
            },
        )

    # =====================================================
    # ADMIN DASHBOARD
    # =====================================================
    today = date.today()
    renewal_cutoff = today + relativedelta(months=6)

    total_properties = Property.objects.count()

    occupied_properties = (
        LeaseAgreement.objects
        .filter(status="active")
        .values("property")
        .distinct()
        .count()
    )

    vacant_properties = max(
        total_properties - occupied_properties,
        0,
    )

    total_tenants = Tenant.objects.count()
    total_invoices = Invoice.objects.count()

    total_invoiced = (
        Invoice.objects.aggregate(
            total=Sum("total_amount")
        )["total"] or ZERO
    )

    total_collected = (
        Payment.objects.aggregate(
            total=Sum("amount")
        )["total"] or ZERO
    )

    total_tds_amount = (
        TDSLedger.objects.aggregate(
            total=Sum("tds_amount")
        )["total"] or ZERO
    )

    recent_payments = (
        Payment.objects
        .select_related("invoice", "invoice__tenant")
        .order_by("-payment_date", "-id")[:10]
    )

    recent_invoices = (
        Invoice.objects
        .select_related("tenant")
        .order_by("-invoice_date", "-invoice_number")[:10]
    )

    # =====================================================
    # UPCOMING LEASE RENEWALS — NEXT 6 MONTHS
    # Check the current lease end date.
    # Do not use the latest extension date here.
    # =====================================================
    upcoming_renewals = []

    agreements_for_renewal = (
        LeaseAgreement.objects
        .select_related(
            "tenant",
            "property",
            "property__owner",
        )
        .filter(status="active")
        .filter(termination_date__isnull=True)
        .filter(end_date__isnull=False)
        .filter(
            end_date__gte=today,
            end_date__lte=renewal_cutoff,
        )
        .order_by("end_date")
    )

    for agreement in agreements_for_renewal:
        upcoming_renewals.append({
            "agreement": agreement,
            "tenant": agreement.tenant,
            "property": agreement.property,
            "end_date": agreement.end_date,
            "monthly_rent": agreement.monthly_rent,
            "days_remaining": (
                agreement.end_date - today
            ).days,
        })

    # =====================================================
    # OVERDUE PAYMENT ALERTS
    # =====================================================
    overdue_payment_alerts = []

    overdue_invoices = (
        Invoice.objects
        .filter(payment_due_date__lt=today)
        .exclude(status__in=["paid", "cancelled"])
        .select_related("tenant")
        .order_by("payment_due_date")
    )

    for invoice in overdue_invoices:
        balance = get_invoice_cash_balance(invoice)

        if balance <= ZERO:
            continue

        overdue_payment_alerts.append({
            "invoice": invoice,
            "tenant_name": (
                getattr(invoice, "tenant_name", "")
                or str(invoice.tenant)
            ),
            "due_date": invoice.payment_due_date,
            "days_overdue": (
                today - invoice.payment_due_date
            ).days,
            "balance": balance,
        })

    # =====================================================
    # EXISTING IN-APP NOTIFICATIONS
    # =====================================================
    unread_notifications = (
        LeaseNotification.objects
        .filter(is_read=False)
        .select_related(
            "lease_agreement",
            "lease_agreement__tenant",
        )
        .order_by("-created_at")[:10]
    )

    unread_notification_count = (
        LeaseNotification.objects
        .filter(is_read=False)
        .count()
    )

    # =====================================================
    # DASHBOARD CONTEXT
    # =====================================================
    context = {
        "total_properties": total_properties,
        "occupied_properties": occupied_properties,
        "vacant_properties": vacant_properties,
        "total_tenants": total_tenants,
        "total_invoices": total_invoices,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "total_tds_amount": total_tds_amount,
        "recent_payments": recent_payments,
        "recent_invoices": recent_invoices,
        "upcoming_renewals": upcoming_renewals,
        "unread_notifications": unread_notifications,
        "unread_notification_count": unread_notification_count,
        "overdue_payment_alerts": overdue_payment_alerts,
        "overdue_payment_count": len(overdue_payment_alerts),
    }

    return render(
        request,
        "core/home.html",
        context,
    )

# =========================================================
# FINANCIAL REPORT
# =========================================================


ZERO = Decimal("0.00")


def get_financial_report_filters(request):
    """Return the selected month, owner, and property filters."""
    today = date.today()
    default_month = today.strftime("%Y-%m")

    selected_month = request.GET.get("month", default_month)

    try:
        year, month_number = map(
            int,
            selected_month.split("-"),
        )
        if not 1 <= month_number <= 12 or year < 1:
            raise ValueError
        month_start = date(year, month_number, 1)
    except (ValueError, TypeError):
        selected_month = default_month
        month_start = today.replace(day=1)

    last_day = monthrange(
        month_start.year,
        month_start.month,
    )[1]

    month_end = month_start.replace(day=last_day)

    owner_name = request.GET.get("owner", "").strip()
    property_name = request.GET.get("property", "").strip()

    # Snapshot fields are used intentionally so historical invoices
    # retain the owner and property names saved when they were created.
    owner_options = list(
        Invoice.objects.exclude(owner_name="")
        .values_list("owner_name", flat=True)
        .distinct()
        .order_by("owner_name")
    )

    property_options = list(
        Invoice.objects.exclude(property_name="")
        .values_list("property_name", flat=True)
        .distinct()
        .order_by("property_name")
    )

    invoices = Invoice.objects.filter(
        invoice_date__gte=month_start,
        invoice_date__lte=month_end,
    )

    if owner_name:
        invoices = invoices.filter(owner_name=owner_name)

    if property_name:
        invoices = invoices.filter(property_name=property_name)

    payments = Payment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lte=month_end,
        invoice__invoice_date__gte=month_start,
        invoice__invoice_date__lte=month_end,
    )

    if owner_name:
        payments = payments.filter(invoice__owner_name=owner_name)

    if property_name:
        payments = payments.filter(invoice__property_name=property_name)

    tds_entries = TDSLedger.objects.filter(
        invoice__invoice_date__gte=month_start,
        invoice__invoice_date__lte=month_end,
    )

    if owner_name:
        tds_entries = tds_entries.filter(
            invoice__owner_name=owner_name
        )

    if property_name:
        tds_entries = tds_entries.filter(
            invoice__property_name=property_name
        )

    return {
        "month": selected_month,
        "month_start": month_start,
        "month_end": month_end,
        "owner": owner_name,
        "property": property_name,
        "owner_options": owner_options,
        "property_options": property_options,
        "invoices": invoices.order_by(
            "-invoice_date",
            "-invoice_number",
        ),
        "payments": payments,
        "tds_entries": tds_entries,
    }


def get_invoice_paid_amount(invoice):
    """Return all payments recorded against one invoice."""
    return (
        Payment.objects.filter(invoice=invoice)
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )



def financial_report(request):
    from decimal import Decimal
    from django.db.models import Sum
    from django.shortcuts import render

    today = date.today()
    month = request.GET.get("month", today.strftime("%Y-%m"))

    try:
        year, month_number = map(int, month.split("-"))
        if not 1 <= month_number <= 12:
            raise ValueError
        month_start = date(year, month_number, 1)
    except (ValueError, TypeError):
        month = today.strftime("%Y-%m")
        month_start = today.replace(day=1)

    month_end = month_start.replace(
        day=monthrange(
            month_start.year,
            month_start.month,
        )[1]
    )

    invoices = Invoice.objects.filter(
        invoice_date__gte=month_start,
        invoice_date__lte=month_end,
    )

    total_invoiced = (
        invoices.aggregate(total=Sum("total_amount"))["total"]
        or Decimal("0.00")
    )

    # Collections received during the selected calendar month.
    payments = Payment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lte=month_end,
    )

    total_collected = (
        payments.aggregate(total=Sum("amount"))["total"]
        or Decimal("0.00")
    )

    # Outstanding balances on invoices issued in the selected month.
    outstanding_amount = Decimal("0.00")

    for invoice in invoices:
        paid = (
            Payment.objects.filter(invoice=invoice)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        outstanding_amount += max(
            invoice.total_amount - paid,
            Decimal("0.00"),
        )

    context = {
        "month": month,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "outstanding_amount": outstanding_amount,
    }

    return render(
        request,
        "core/financial_report.html",
        context,
    )


def tenant_wise_outstanding_report(request):
    """Detailed invoice balances for the selected month and filters."""
    filters = get_financial_report_filters(request)
    rows = []
    total_outstanding = ZERO

    for invoice in filters["invoices"]:
        paid_amount = get_invoice_paid_amount(invoice)
        outstanding = max(invoice.total_amount - paid_amount, ZERO)

        rows.append({
            "invoice": invoice,
            "tenant_name": invoice.tenant_name,
            "invoice_number": invoice.invoice_number,
            "property_name": invoice.property_name,
            "unit_number": invoice.unit_number,
            "invoice_amount": invoice.total_amount,
            "paid_amount": paid_amount,
            "outstanding": outstanding,
            "due_date": invoice.payment_due_date,
        })
        total_outstanding += outstanding

    context = {
        **filters,
        "report_type": "outstanding",
        "report_title": "Tenant-wise Outstanding",
        "rows": rows,
        "total_outstanding": total_outstanding,
    }

    return render(
        request,
        "core/financial_detail_report.html",
        context,
    )


def property_wise_collection_report(request):
    """Group payments received during the selected month by property."""
    filters = get_financial_report_filters(request)

    property_collection = (
        filters["payments"]
        .values("invoice__property_name")
        .annotate(total=Sum("amount"))
        .order_by("-total", "invoice__property_name")
    )

    total_collected = (
        filters["payments"]
        .aggregate(total=Sum("amount"))["total"]
        or ZERO
    )

    context = {
        **filters,
        "report_type": "collection",
        "report_title": "Property-wise Collection",
        "property_collection": property_collection,
        "total_collected": total_collected,
    }

    return render(
        request,
        "core/financial_detail_report.html",
        context,
    )


def financial_report_summary(request):
    """Detailed financial totals and invoice status counts."""
    filters = get_financial_report_filters(request)
    invoices = filters["invoices"]
    payments = filters["payments"]

    total_invoiced = (
        invoices.aggregate(total=Sum("total_amount"))["total"]
        or ZERO
    )
    total_collected = (
        payments.aggregate(total=Sum("amount"))["total"]
        or ZERO
    )
    total_tds_amount = (
        filters["tds_entries"]
        .aggregate(total=Sum("tds_amount"))["total"]
        or ZERO
    )

    outstanding_amount = ZERO

    for invoice in invoices:
        paid_amount = get_invoice_paid_amount(invoice)
        outstanding_amount += max(
            invoice.total_amount - paid_amount,
            ZERO,
        )

    context = {
        **filters,
        "report_type": "summary",
        "report_title": "Report Summary",
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "total_tds_amount": total_tds_amount,
        "outstanding_amount": outstanding_amount,
        "total_invoices": invoices.count(),
        "paid_invoices": invoices.filter(status="paid").count(),
        "pending_invoices": invoices.filter(status="pending").count(),
        "generated_invoices": invoices.filter(status="generated").count(),
    }

    return render(
        request,
        "core/financial_detail_report.html",
        context,
    )


# =========================================================
# RESET TEST DATA
# =========================================================


def reset_test_data(request):
    if request.method != "POST":
        return redirect("dashboard")

    try:
        with transaction.atomic():

            # 1. Delete TDS ledger records first because they
            #    protect their related invoices.
            TDSLedger.objects.all().delete()

            # 2. Delete payment records.
            Payment.objects.all().delete()

            # 3. Delete invoice line items.
            InvoiceItem.objects.all().delete()

            # 4. Delete invoices.
            Invoice.objects.all().delete()

            # 5. Delete lease agreements.
            #    Related RentHistory records may be deleted
            #    automatically, depending on their FK settings.
            LeaseAgreement.objects.all().delete()

            # 6. Delete tenants.
            Tenant.objects.all().delete()

            # Owners and Properties are preserved as master data.

        # Reset invoice numbering for SQLite.
        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM sqlite_sequence WHERE name = %s",
                    ["core_invoice"],
                )

        messages.success(
            request,
            "Test data reset successfully. "
            "Owners and properties were preserved.",
        )

    except Exception as exc:
        messages.error(
            request,
            f"Unable to reset test data: {exc}",
        )

    return redirect("dashboard")



def property_tax_add(request, property_id):

    property_obj = get_object_or_404(
        Property,
        pk=property_id,
    )

    if request.method == "POST":

        form = PropertyTaxForm(request.POST)

        if form.is_valid():

            tax = form.save(commit=False)
            tax.property = property_obj
            tax.save()

            return redirect(
                "property_detail",
                pk=property_obj.pk,
            )

    else:

        form = PropertyTaxForm()

    return render(
        request,
        "core/property_tax_add.html",
        {
            "form": form,
            "property": property_obj,
        },
    )



@login_required
def property_tax_edit(request, pk):
    tax = get_object_or_404(
        PropertyTax.objects.select_related("property"),
        pk=pk,
    )

    if request.method == "POST":
        form = PropertyTaxForm(
            request.POST,
            instance=tax,
        )

        if form.is_valid():
            form.save()

            # Staff: redirect to Staff Dashboard
            if request.user.is_staff and not request.user.is_superuser:
                return redirect("dashboard")

            # Admin: retain the existing Property Details redirect
            return redirect(
                "property_tax_report",
                
            )

        else:
            print("Property Tax form errors:", form.errors)

    else:
        form = PropertyTaxForm(instance=tax)

    return render(
        request,
        "core/property_tax_edit.html",
        {
            "form": form,
            "tax": tax,
            "property": tax.property,
        },
    )


def property_tax_delete(request, pk):

    tax = get_object_or_404(
        PropertyTax.objects.select_related("property"),
        pk=pk,
    )

    property_id = tax.property.pk

    if request.method == "POST":

        tax.delete()

        return redirect(
            "property_detail",
            pk=property_id,
        )

    return render(
        request,
        "core/property_tax_delete.html",
        {
            "tax": tax,
            "property": tax.property,
        },
    )

def property_tax_report(request):

    taxes = (
        PropertyTax.objects
        .select_related(
            "property",
            "property__owner",
        )
        .all()
        .order_by(
            "-tax_year",
            "property__name",
            "-id",
        )
    )

    return render(
        request,
        "core/property_tax_report.html",
        {
            "taxes": taxes,
        },
    )

def property_tax_receipt(request, pk):

    tax = get_object_or_404(
        PropertyTax.objects.select_related(
            "property",
            "property__owner",
        ),
        pk=pk,
        status="paid",
    )

    return render(
        request,
        "core/property_tax_receipt.html",
        {
            "tax": tax,
        },
    )

def lease_notifications(request):
    notifications = LeaseNotification.objects.select_related(
        "lease_agreement",
        "lease_agreement__tenant",
    ).order_by("-created_at")

    return render(
        request,
        "core/lease_notifications.html",
        {
            "notifications": notifications,
        },
    )


@require_POST
def mark_lease_notification_read(request, pk):
    notification = get_object_or_404(
        LeaseNotification,
        pk=pk,
    )

    notification.is_read = True
    notification.save(update_fields=["is_read"])

    return redirect("lease_notifications")


def tds_ledger_report(request):
    today = date.today()

    mode = request.GET.get("mode", "month")
    month_value = request.GET.get("month", "2026-10")
    from_date_value = request.GET.get("from_date", "2026-10-01")
    to_date_value = request.GET.get("to_date", "2026-10-31")
    tenant_id = request.GET.get("tenant", "all")

    tenants = Tenant.objects.all().order_by("full_name")

    entries = TDSLedger.objects.select_related(
        "invoice",
        "tenant",
        "invoice__lease_agreement",
    ).all()

    # Create missing ledger entries for existing invoices.
    # Rent is taken from the invoice's rent line, not GST.
    invoices = Invoice.objects.exclude(status="cancelled").prefetch_related(
        "items"
    )

    for invoice in invoices:
        rent_item = invoice.items.filter(item_type="rent").first()

        if rent_item is None:
            continue

        rent_amount = rent_item.amount or Decimal("0.00")

        TDSLedger.objects.get_or_create(
            invoice=invoice,
            defaults={
                "tenant": invoice.tenant,
                "rent_amount": rent_amount,
                "tds_rate": Decimal("10.00"),
            },
        )

    # Reload after syncing existing invoices.
    entries = TDSLedger.objects.select_related(
        "invoice",
        "tenant",
        "invoice__lease_agreement",
    ).all()

    if mode == "month":
        try:
            year, month = map(int, month_value.split("-"))
            if not 1 <= month <= 12:
                raise ValueError

            entries = entries.filter(
                invoice__billing_from__year=year,
                invoice__billing_from__month=month,
            )
        except (ValueError, TypeError):
            mode = "month"
            month_value = f"{today.year}-{today.month:02d}"
            entries = entries.filter(
                invoice__billing_from__year=today.year,
                invoice__billing_from__month=today.month,
            )

    elif mode == "date":
        try:
            start_date = date.fromisoformat(from_date_value)
            end_date = date.fromisoformat(to_date_value)

            if start_date > end_date:
                start_date, end_date = end_date, start_date

            entries = entries.filter(
                invoice__billing_from__gte=start_date,
                invoice__billing_from__lte=end_date,
            )
        except (ValueError, TypeError):
            mode = "month"
            month_value = f"{today.year}-{today.month:02d}"
            entries = entries.filter(
                invoice__billing_from__year=today.year,
                invoice__billing_from__month=today.month,
            )

    # mode=all does not apply a date filter.
    if tenant_id != "all":
        if tenant_id.isdigit():
            entries = entries.filter(tenant_id=int(tenant_id))
        else:
            tenant_id = "all"

    entries = entries.order_by(
        "invoice__billing_from",
        "invoice__invoice_number",
    )

    totals = entries.aggregate(
        total_rent=Sum("rent_amount"),
        total_tds=Sum("tds_amount"),
    )

    context = {
        "entries": entries,
        "tenants": tenants,
        "selected_tenant": tenant_id,
        "mode": mode,
        "month_value": month_value,
        "from_date_value": from_date_value,
        "to_date_value": to_date_value,
        "total_rent": totals["total_rent"] or Decimal("0.00"),
        "total_tds": totals["total_tds"] or Decimal("0.00"),
    }

    return render(
        request,
        "core/tds_ledger_report.html",
        context,
    )



@login_required
def admin_profile(request):
    User = get_user_model()

    if not request.user.is_active or not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. An active Administrator account is required."
        )

    profile, _ = AdminUserProfile.objects.get_or_create(
        user=request.user
    )

    if request.method == "POST":
        form = AdminProfileForm(
            request.POST,
            instance=profile,
            user=request.user,
        )

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()

                messages.success(
                    request,
                    "Your profile and account details were updated successfully."
                )
                return redirect("admin_profile")

            except Exception:
                messages.error(
                    request,
                    "Unable to save your changes. Please try again."
                )
    else:
        form = AdminProfileForm(
            instance=profile,
            user=request.user,
        )

    # Staff accounts: all non-superuser accounts
    staff_users = User.objects.filter(
        is_superuser=False
    ).order_by("username")

    # Summary card counts
    active_user_count = User.objects.filter(
        is_active=True
    ).count()

    admin_count = User.objects.filter(
        is_active=True,
        is_superuser=True,
    ).count()

    staff_count = User.objects.filter(
        is_active=True,
        is_superuser=False,
    ).count()

    context = {
        "form": form,
        "staff_users": staff_users,
        "active_user_count": active_user_count,
        "admin_count": admin_count,
        "staff_count": staff_count,
    }

    return render(
        request,
        "registration/admin_profile.html",
        context,
    )

    



@login_required
def admin_edit_staff(request, user_id):
    # Only active administrators may manage staff accounts.
    if not request.user.is_active or not request.user.is_superuser:
        return HttpResponseForbidden(
            "Only administrators can manage staff accounts."
        )

    staff_user = get_object_or_404(
        User,
        pk=user_id,
        is_superuser=False,
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        new_password = request.POST.get("new_password", "").strip()

        if not username:
            messages.error(request, "Username is required.")
        elif User.objects.filter(
            username__iexact=username
        ).exclude(pk=staff_user.pk).exists():
            messages.error(request, "That username is already in use.")
        elif email and User.objects.filter(
            email__iexact=email
        ).exclude(pk=staff_user.pk).exists():
            messages.error(request, "That email address is already in use.")
        else:
            try:
                with transaction.atomic():
                    staff_user.username = username
                    staff_user.email = email

                    if new_password:
                        validate_password(new_password, staff_user)
                        staff_user.set_password(new_password)

                    staff_user.save()

                messages.success(
                    request,
                    f"Staff account '{staff_user.username}' was updated."
                )
                return redirect("admin_profile")

            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            except Exception:
                messages.error(
                    request,
                    "Could not update this staff account."
                )

    return render(
        request,
        "registration/admin_edit_staff.html",
        {"staff_user": staff_user},
    )



def admin_change_password(request):
    if (
        not request.user.is_authenticated
        or not request.user.is_active
        or not request.user.is_superuser
    ):

        
        return HttpResponseForbidden("Superuser access required.")

    if request.method == "POST":
        form = PasswordChangeForm(
            user=request.user,
            data=request.POST,
        )

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(
                request,
                "Your password was changed successfully.",
            )
            return redirect("admin_change_password")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(
        request,
        "registration/admin_change_password.html",
        {"form": form},
    )

def password_reset_rate_limited(request):
    ip = request.META.get("REMOTE_ADDR", "unknown")
    key = f"password_reset_rate:{ip}"

    count = cache.get(key, 0)

    if count >= 5:
        return True

    cache.set(key, count + 1, timeout=15 * 60)
    return False




class RateLimitedPasswordResetView(PasswordResetView):
    def post(self, request, *args, **kwargs):
        if password_reset_rate_limited(request):
            return HttpResponse(
                "Too many password-reset requests. Please try again in 15 minutes.",
                status=429,
            )

        return super().post(request, *args, **kwargs)


MAX_ADMIN_USERS = 4



@login_required
def admin_user_create(request):
    User = get_user_model()
    MAX_ADMIN_USERS = 4

    if not request.user.is_active or not request.user.is_superuser:
        return HttpResponseForbidden("Superuser access required.")

    if request.method == "POST":
        form = AdminUserCreateForm(request.POST)

        if form.is_valid():
            role = form.cleaned_data["role"]

            active_admin_count = User.objects.filter(
                is_active=True,
                is_superuser=True,
            ).count()

            if role == "admin" and active_admin_count >= MAX_ADMIN_USERS:
                form.add_error(
                    None,
                    "The maximum of 4 active administrator accounts "
                    "has been reached.",
                )
            else:
                try:
                    new_user = form.save()

                    role_label = (
                        "Administrator"
                        if new_user.is_superuser
                        else "Staff"
                    )

                    messages.success(
                        request,
                        f"{role_label} '{new_user.username}' "
                        "was created successfully.",
                    )
                    return redirect("admin_profile")

                except IntegrityError:
                    form.add_error(
                        None,
                        "The account could not be created because "
                        "of a database conflict. Please try again.",
                    )
    else:
        # Initialize an empty form when the page is opened.
        form = AdminUserCreateForm()

    active_admin_count = User.objects.filter(
        is_active=True,
        is_superuser=True,
    ).count()

    return render(
        request,
        "registration/admin_user_create.html",
        {
            "form": form,
            "active_admin_count": active_admin_count,
            "max_admin_users": MAX_ADMIN_USERS,
        },
    )


@login_required
def role_redirect(request):
    if not request.user.is_active:
        return redirect("login")

    return redirect("dashboard")



@login_required
def staff_account_edit(request, user_id):
    User = get_user_model()

    # Only active administrators can manage staff accounts.
    if not request.user.is_active or not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. Administrator access is required."
        )

    staff_user = get_object_or_404(
        User,
        pk=user_id,
        is_superuser=False,
    )

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        if not username:
            messages.error(request, "Username is required.")

        elif User.objects.filter(
            username__iexact=username
        ).exclude(pk=staff_user.pk).exists():
            messages.error(request, "This username is already in use.")

        elif email and User.objects.filter(
            email__iexact=email
        ).exclude(pk=staff_user.pk).exists():
            messages.error(request, "This email is already in use.")

        elif password and password != confirm_password:
            messages.error(request, "Passwords do not match.")

        else:
            staff_user.username = username
            staff_user.email = email

            if password:
                staff_user.set_password(password)

            staff_user.save()

            messages.success(
                request,
                f"Staff account '{staff_user.username}' updated successfully."
            )

            # If the staff member's password was changed, they may need
            # to log in again on their next session.
            return redirect("admin_profile")

    return render(
        request,
        "registration/staff_account_edit.html",
        {"staff_user": staff_user},
    )

@login_required
def gst_ledger_report(request):
    from decimal import Decimal
    

    if not request.user.is_superuser:
        return HttpResponseForbidden(
            "Access denied. Only Administrators can view the GST Ledger."
        )

    # Include existing invoices and exclude cancelled invoices.
    invoices = (
        Invoice.objects
        .exclude(status="cancelled")
        .select_related("tenant")
        .prefetch_related("items")
        .order_by("-invoice_date", "-invoice_number")
    )

    # Synchronize the ledger from saved invoice values.
    # This does not change or recalculate invoice GST.
    for invoice in invoices:
        rent_item = invoice.items.filter(
            item_type="rent"
        ).first()

        if rent_item is not None:
            rent_amount = rent_item.amount or Decimal("0.00")
        else:
            # Fallback for older invoices without a rent line.
            rent_amount = invoice.taxable_amount or Decimal("0.00")

        GSTLedger.objects.update_or_create(
            invoice=invoice,
            defaults={
                "tenant": invoice.tenant,
                "rent_amount": rent_amount,
                "cgst_amount": invoice.cgst_amount or Decimal("0.00"),
                "sgst_amount": invoice.sgst_amount or Decimal("0.00"),
            },
        )

    entries = (
        GSTLedger.objects
        .select_related("invoice", "tenant")
        .order_by("-invoice__invoice_date", "-invoice__invoice_number")
    )

    totals = entries.aggregate(
        total_rent=Sum("rent_amount"),
        total_cgst=Sum("cgst_amount"),
        total_sgst=Sum("sgst_amount"),
        total_gst=Sum("total_gst_amount"),
    )

    context = {
        "entries": entries,
        "total_rent": totals["total_rent"] or Decimal("0.00"),
        "total_cgst": totals["total_cgst"] or Decimal("0.00"),
        "total_sgst": totals["total_sgst"] or Decimal("0.00"),
        "total_gst": totals["total_gst"] or Decimal("0.00"),
    }

    return render(
        request,
        "core/gst_ledger_report.html",
        context,
    )


def month_wise_financial_report(request):
    from calendar import monthrange
    from datetime import date
    from decimal import Decimal

    from django.db.models import Sum
    from django.shortcuts import render

    today = date.today()
    month = request.GET.get("month", today.strftime("%Y-%m"))
    owner = request.GET.get("owner", "").strip()
    property_name = request.GET.get("property", "").strip()
    invoice_status = request.GET.get("status", "all").strip().lower()

    try:
        year, month_number = map(int, month.split("-"))
        if not 1 <= month_number <= 12:
            raise ValueError
        month_start = date(year, month_number, 1)
    except (ValueError, TypeError):
        month = today.strftime("%Y-%m")
        month_start = today.replace(day=1)

    month_end = month_start.replace(
        day=monthrange(month_start.year, month_start.month)[1]
    )

    invoices = Invoice.objects.filter(
        invoice_date__gte=month_start,
        invoice_date__lte=month_end,
    )

    if owner:
        invoices = invoices.filter(owner_name=owner)

    if property_name:
        invoices = invoices.filter(property_name=property_name)

    rows = []
    total_invoiced = Decimal("0.00")
    total_collected = Decimal("0.00")
    total_outstanding = Decimal("0.00")

    for invoice in invoices.order_by("-invoice_date", "-invoice_number"):
        paid = (
            Payment.objects.filter(invoice=invoice)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        outstanding = max(
            invoice.total_amount - paid,
            Decimal("0.00"),
        )

        # Generated invoices are presented as Pending.
        display_status = (
            "Pending"
            if invoice.status in ("generated", "pending")
            else invoice.status.title()
        )

        # Status filter:
        # Paid = invoice status is paid.
        # Unpaid = invoice has a remaining balance.
        # Pending = invoice status is pending or generated.
        if invoice_status == "paid" and invoice.status != "paid":
            continue
        if invoice_status == "unpaid" and outstanding <= 0:
            continue
        if invoice_status == "pending" and invoice.status not in (
            "generated", "pending"
        ):
            continue

        rows.append({
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.invoice_date,
            "tenant_name": invoice.tenant_name,
            "owner_name": invoice.owner_name,
            "property_name": invoice.property_name,
            "unit_number": invoice.unit_number,
            "invoice_amount": invoice.total_amount,
            "paid_amount": paid,
            "outstanding": outstanding,
            "status": display_status,
        })

        total_invoiced += invoice.total_amount
        total_collected += paid
        total_outstanding += outstanding

    context = {
        "month": month,
        "month_start": month_start,
        "owner": owner,
        "property": property_name,
        "status": invoice_status,
        "owner_options": Invoice.objects.exclude(
            owner_name=""
        ).values_list("owner_name", flat=True).distinct().order_by("owner_name"),
        "property_options": Invoice.objects.exclude(
            property_name=""
        ).values_list("property_name", flat=True).distinct().order_by("property_name"),
        "rows": rows,
        "total_invoiced": total_invoiced,
        "total_collected": total_collected,
        "total_outstanding": total_outstanding,
    }

    return render(
        request,
        "core/month_wise_financial_report.html",
        context,
    )
