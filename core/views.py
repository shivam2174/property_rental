from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, ROUND_DOWN
from datetime import date
from calendar import monthrange
from django.db import transaction

from django.contrib import messages
from django.db import models, transaction, IntegrityError, connection
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date, timedelta
from django.utils.dateparse import parse_date as django_parse_date

from xhtml2pdf import pisa

from .models import (
    Owner,
    Property,
    Tenant,
    RentalAgreement,
    RentHistory,
    Invoice,
    InvoiceItem,
    Payment,
)
from .forms import TenantForm, AgreementForm

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

def owner_list(request):

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

        # Check active Rental Agreement directly
        occupied = (
            RentalAgreement.objects
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

        # Your current Property model uses unit_no
        total_units = (
            1
            if property_obj.unit_no
            else 0
        )

        # IMPORTANT:
        # An ACTIVE Rental Agreement means
        # the property is occupied.
        occupied = (
            RentalAgreement.objects
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
        RentalAgreement.objects
        .select_related("tenant")
        .filter(
            property=property_obj,
            status="active",
        )
        .first()
    )

    return render(
        request,
        "core/property_detail.html",
        {
            "property": property_obj,
            "active_agreement": active_agreement,
        },
    )


def property_add(request):

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
            request.POST.get(
                "purchased_on"
            )
        )

        total_area = parse_decimal(
            request.POST.get(
                "total_area"
            )
        )

        price = parse_decimal(
            request.POST.get(
                "price"
            )
        )

        per_sqft_rate = parse_decimal(
            request.POST.get(
                "per_sqft_rate"
            )
        )

        stamp_duty = parse_decimal(
            request.POST.get(
                "stamp_duty"
            )
        )

        total_purchase_price = parse_decimal(
            request.POST.get(
                "total_purchase_price"
            )
        )

        gst_number = request.POST.get(
            "gst_number",
            "",
        ).strip()

        lap_amount = parse_decimal(
            request.POST.get(
                "lap_amount"
            )
        )

        monthly_installment = parse_decimal(
            request.POST.get(
                "monthly_installment"
            )
        )

        lap_maturity = parse_date(
            request.POST.get(
                "lap_maturity"
            )
        )

        parking_slot = request.POST.get(
            "parking_slot",
            "",
        ).strip()

        status = request.POST.get(
            "status",
            "active",
        )

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

        owner = None

        if owner_id:

            owner = get_object_or_404(
                Owner,
                pk=owner_id,
            )

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

        try:

            Property.objects.create(

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
                form.save()

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

    if request.method == "POST":

        full_name = request.POST.get("full_name", "").strip()
        father_name = request.POST.get("father_name", "").strip()
        mobile = request.POST.get("mobile", "").strip()
        email = request.POST.get("email", "").strip()
        permanent_address = request.POST.get("permanent_address", "").strip()

        id_type_1 = request.POST.get("id_type_1", "").strip()
        id_number_1 = request.POST.get("id_number_1", "").strip()

        id_type_2 = request.POST.get("id_type_2", "").strip()
        id_number_2 = request.POST.get("id_number_2", "").strip()

        id_type_3 = request.POST.get("id_type_3", "").strip()
        id_number_3 = request.POST.get("id_number_3", "").strip()

        security_deposit = parse_decimal(
            request.POST.get("security_deposit")
        )

        status = request.POST.get(
            "status",
            "active",
        )

        if not full_name:
            messages.error(
                request,
                "Tenant name is required.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if not id_type_1 or not id_number_1:
            messages.error(
                request,
                "ID 1 Type and ID 1 Number are required.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if not id_type_2 or not id_number_2:
            messages.error(
                request,
                "ID 2 Type and ID 2 Number are required.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if id_type_3 and not id_number_3:
            messages.error(
                request,
                "Please enter ID 3 Number.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if id_number_3 and not id_type_3:
            messages.error(
                request,
                "Please select ID 3 Type.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        selected_id_types = [
            id_type_1,
            id_type_2,
        ]

        if id_type_3:
            selected_id_types.append(id_type_3)

        if len(selected_id_types) != len(set(selected_id_types)):
            messages.error(
                request,
                "The same ID type cannot be selected more than once.",
            )
            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        tenant.full_name = full_name
        tenant.father_name = father_name
        tenant.mobile = mobile
        tenant.email = email
        tenant.permanent_address = permanent_address

        tenant.id_type_1 = id_type_1
        tenant.id_number_1 = id_number_1

        tenant.id_type_2 = id_type_2
        tenant.id_number_2 = id_number_2

        tenant.id_type_3 = id_type_3
        tenant.id_number_3 = id_number_3

        tenant.security_deposit = security_deposit
        tenant.status = status

        try:
            tenant.save()

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
            "tenant": tenant,
            "edit_mode": True,
        },
    )

    tenant = get_object_or_404(
        Tenant,
        pk=pk,
    )

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            "",
        ).strip()

        father_name = request.POST.get(
            "father_name",
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

        permanent_address = request.POST.get(
            "permanent_address",
            "",
        ).strip()

        id_type_1 = request.POST.get(
            "id_type_1",
            "",
        ).strip()

        id_number_1 = request.POST.get(
            "id_number_1",
            "",
        ).strip()

        id_type_2 = request.POST.get(
            "id_type_2",
            "",
        ).strip()

        id_number_2 = request.POST.get(
            "id_number_2",
            "",
        ).strip()

        id_type_3 = request.POST.get(
            "id_type_3",
            "",
        ).strip()

        id_number_3 = request.POST.get(
            "id_number_3",
            "",
        ).strip()

        security_deposit = parse_decimal(
            request.POST.get(
                "security_deposit"
            )
        )

        status = request.POST.get(
            "status",
            "active",
        )

        if not full_name:

            messages.error(
                request,
                "Tenant name is required.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if not id_type_1 or not id_number_1:

            messages.error(
                request,
                "ID 1 Type and ID 1 Number are required.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if not id_type_2 or not id_number_2:

            messages.error(
                request,
                "ID 2 Type and ID 2 Number are required.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if id_type_3 and not id_number_3:

            messages.error(
                request,
                "Please enter ID 3 Number.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        if id_number_3 and not id_type_3:

            messages.error(
                request,
                "Please select ID 3 Type.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        selected_id_types = [
            id_type_1,
            id_type_2,
        ]

        if id_type_3:

            selected_id_types.append(
                id_type_3
            )

        if len(selected_id_types) != len(
            set(selected_id_types)
        ):

            messages.error(
                request,
                "The same ID type cannot be selected more than once.",
            )

            return render(
                request,
                "core/tenant_form.html",
                {
                    "tenant": tenant,
                    "edit_mode": True,
                },
            )

        tenant.full_name = full_name
        tenant.father_name = father_name
        tenant.mobile = mobile
        tenant.email = email
        tenant.permanent_address = (
            permanent_address
        )

        tenant.id_type_1 = id_type_1
        tenant.id_number_1 = id_number_1

        tenant.id_type_2 = id_type_2
        tenant.id_number_2 = id_number_2

        tenant.id_type_3 = id_type_3
        tenant.id_number_3 = id_number_3

        tenant.security_deposit = (
            security_deposit
        )

        tenant.status = status

        try:

            tenant.save()

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
            "tenant": tenant,
            "edit_mode": True,
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

    if RentalAgreement.objects.filter(
        tenant=tenant
    ).exists():

        messages.error(
            request,
            "This tenant cannot be deleted because rental agreement history exists.",
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

    agreements = (
        RentalAgreement.objects
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

        existing_active = RentalAgreement.objects.filter(
            property=property_obj,
            status="active",
        ).exists()

        if existing_active:
            messages.error(
                request,
                "This property is already occupied by an active rental agreement.",
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
        # TERM 1
        # =====================================================

        term1_increase_percent = parse_decimal(
            request.POST.get("term1_increase_percent")
        )

        if term1_increase_percent is None:
            term1_increase_percent = Decimal("5.00")

        if not valid_percentage(term1_increase_percent):
            messages.error(
                request,
                "Term 1 increase percentage must be between 0 and 100.",
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
        # TERM 2
        # =====================================================

        term2_increase_percent = parse_decimal(
            request.POST.get("term2_increase_percent")
        )

        if term2_increase_percent is None:
            term2_increase_percent = Decimal("10.00")

        if not valid_percentage(term2_increase_percent):
            messages.error(
                request,
                "Term 2 increase percentage must be between 0 and 100.",
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
        # TERM 3
        # =====================================================

        term3_increase_percent = parse_decimal(
            request.POST.get("term3_increase_percent")
        )

        if term3_increase_percent is None:
            term3_increase_percent = Decimal("15.00")

        if not valid_percentage(term3_increase_percent):
            messages.error(
                request,
                "Term 3 increase percentage must be between 0 and 100.",
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
        # TERM 4
        # =====================================================

        term4_increase_percent = parse_decimal(
            request.POST.get("term4_increase_percent")
        )

        if term4_increase_percent is None:
            term4_increase_percent = Decimal("20.00")

        if not valid_percentage(term4_increase_percent):
            messages.error(
                request,
                "Term 4 increase percentage must be between 0 and 100.",
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
        # TERM 5
        # =====================================================

        term5_increase_percent = parse_decimal(
            request.POST.get("term5_increase_percent")
        )

        if term5_increase_percent is None:
            term5_increase_percent = Decimal("25.00")

        if not valid_percentage(term5_increase_percent):
            messages.error(
                request,
                "Term 5 increase percentage must be between 0 and 100.",
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
        # CREATE AGREEMENT
        # =====================================================

        try:
            with transaction.atomic():

                agreement = RentalAgreement.objects.create(
                    tenant=tenant,
                    property=property_obj,
                    start_date=start_date,
                    end_date=end_date,
                    monthly_rent=monthly_rent,

                    term1_increase_percent=(
                        term1_increase_percent
                    ),
                    term2_increase_percent=(
                        term2_increase_percent
                    ),
                    term3_increase_percent=(
                        term3_increase_percent
                    ),
                    term4_increase_percent=(
                        term4_increase_percent
                    ),
                    term5_increase_percent=(
                        term5_increase_percent
                    ),

                    next_increase_date=(
                        next_increase_date
                    ),

                    rent_increase_pending=False,

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

                # =================================================
                # INITIAL RENT HISTORY
                # =================================================

                RentHistory.objects.create(
                    rental_agreement=agreement,
                    effective_from=start_date,
                    effective_to=None,
                    monthly_rent=monthly_rent,
                    increase_percent=ZERO,
                    increase_accepted=True,
                )

            messages.success(
                request,
                "Rental Agreement created successfully.",
            )

            return redirect("agreement_list")

        except IntegrityError as e:
            messages.error(
                request,
                f"Unable to create the Rental Agreement: {e}",
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
        RentalAgreement.objects.select_related(
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
        # MONTHLY RENT
        # =====================================================

        monthly_rent = parse_decimal(
            request.POST.get("monthly_rent")
        )

        if monthly_rent is not None and monthly_rent > ZERO:
            agreement.monthly_rent = monthly_rent
        else:
            messages.error(
                request,
                "Please enter a valid monthly rent.",
            )

        # =====================================================
        # TERM 1 INCREASE
        # =====================================================

        term1_increase_percent = parse_decimal(
            request.POST.get("term1_increase_percent")
        )

        if term1_increase_percent is None:
            term1_increase_percent = Decimal("5.00")

        if valid_percentage(term1_increase_percent):
            agreement.term1_increase_percent = (
                term1_increase_percent
            )
        else:
            messages.error(
                request,
                "Term 1 increase percentage must be between 0 and 100.",
            )

        # =====================================================
        # TERM 2 INCREASE
        # =====================================================

        term2_increase_percent = parse_decimal(
            request.POST.get("term2_increase_percent")
        )

        if term2_increase_percent is None:
            term2_increase_percent = Decimal("10.00")

        if valid_percentage(term2_increase_percent):
            agreement.term2_increase_percent = (
                term2_increase_percent
            )
        else:
            messages.error(
                request,
                "Term 2 increase percentage must be between 0 and 100.",
            )

        # =====================================================
        # TERM 3 INCREASE
        # =====================================================

        term3_increase_percent = parse_decimal(
            request.POST.get("term3_increase_percent")
        )

        if term3_increase_percent is None:
            term3_increase_percent = Decimal("15.00")

        if valid_percentage(term3_increase_percent):
            agreement.term3_increase_percent = (
                term3_increase_percent
            )
        else:
            messages.error(
                request,
                "Term 3 increase percentage must be between 0 and 100.",
            )

        # =====================================================
        # TERM 4 INCREASE
        # =====================================================

        term4_increase_percent = parse_decimal(
            request.POST.get("term4_increase_percent")
        )

        if term4_increase_percent is None:
            term4_increase_percent = Decimal("20.00")

        if valid_percentage(term4_increase_percent):
            agreement.term4_increase_percent = (
                term4_increase_percent
            )
        else:
            messages.error(
                request,
                "Term 4 increase percentage must be between 0 and 100.",
            )

        # =====================================================
        # TERM 5 INCREASE
        # =====================================================

        term5_increase_percent = parse_decimal(
            request.POST.get("term5_increase_percent")
        )

        if term5_increase_percent is None:
            term5_increase_percent = Decimal("25.00")

        if valid_percentage(term5_increase_percent):
            agreement.term5_increase_percent = (
                term5_increase_percent
            )



def agreement_view(request, pk):

    agreement = get_object_or_404(
        RentalAgreement.objects.select_related(
            "tenant",
            "property",
            "property__owner",
        ),
        pk=pk,
    )

    return render(
        request,
        "core/agreement_view.html",
        {
            "agreement": agreement,
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
        RentalAgreement.objects.select_related(
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
            RentalAgreement.objects
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
        RentalAgreement,
        pk=pk,
    )

    if request.method != "POST":

        return redirect(
            "agreement_list"
        )

    if Invoice.objects.filter(
        rental_agreement=agreement
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
    """
    Return True when rent increase is due.

    IMPORTANT:

    The increase does NOT automatically happen.

    It only becomes pending.

    The user must approve it.
    """

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
        RentalAgreement.objects.select_related(
            "tenant",
            "property",
            "property__owner",
        ),
        pk=agreement_id,
    )

    if agreement.status != "active":
        messages.error(
            request,
            "Invoice can only be generated for an active rental agreement.",
        )
        return redirect("agreement_list")

    today = date.today()

    # =========================================================
    # GET REQUEST
    # =========================================================

    if request.method == "GET":

        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": today.strftime("%Y-%m"),
            },
        )

    # =========================================================
    # BILLING MONTH
    # =========================================================

    billing_month_input = request.POST.get(
        "billing_month",
        "",
    ).strip()

    if not billing_month_input:

        messages.error(
            request,
            "Please select a billing month.",
        )

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
            int,
            billing_month_input.split("-"),
        )

        billing_from = date(
            billing_year,
            billing_month,
            1,
        )

        billing_to = date(
            billing_year,
            billing_month,
            monthrange(
                billing_year,
                billing_month,
            )[1],
        )

    except (ValueError, TypeError):

        messages.error(
            request,
            "Invalid billing month selected.",
        )

        return render(
            request,
            "core/invoice_generate.html",
            {
                "agreement": agreement,
                "selected_month": billing_month_input,
            },
        )

    # =========================================================
    # AGREEMENT DATE VALIDATION
    # =========================================================

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

    # =========================================================
    # ACTUAL BILLABLE PERIOD
    # =========================================================

    actual_billing_from = max(
        billing_from,
        agreement.start_date,
    )

    actual_billing_to = billing_to

    if agreement.end_date:

        actual_billing_to = min(
            billing_to,
            agreement.end_date,
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
        billing_year,
        billing_month,
    )[1]

    # =========================================================
    # EXISTING INVOICE CHECK
    # =========================================================

    existing_invoice = Invoice.objects.filter(
        rental_agreement=agreement,
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

    # =========================================================
    # TERM CALCULATION
    # =========================================================

    current_term = agreement.get_current_term(
        actual_billing_from
    )

    # New rent according to the current term
    proposed_rent = parse_decimal(
        agreement.get_term_rent(
            current_term
        )
    )

    increase_percent = parse_decimal(
        agreement.get_current_increase_percent(
            actual_billing_from
        )
    )

    # =========================================================
    # FIND TERM START DATE
    # =========================================================

    if current_term == 1:

        term_start_date = agreement.term1_start_date

    elif current_term == 2:

        term_start_date = agreement.term2_start_date

    elif current_term == 3:

        term_start_date = agreement.term3_start_date

    elif current_term == 4:

        term_start_date = agreement.term4_start_date

    else:

        term_start_date = agreement.term5_start_date

    # =========================================================
    # CHECK WHETHER THIS TERM'S INCREASE IS ALREADY ACCEPTED
    # =========================================================

    accepted_history = RentHistory.objects.filter(
        rental_agreement=agreement,
        effective_from=term_start_date,
        increase_accepted=True,
    ).order_by("-created_at").first()

    increase_already_accepted = bool(
        accepted_history
    )

    # =========================================================
    # FIND PREVIOUS TERM RENT
    # =========================================================
    #
    # This is the rent that will be used if the user selects NO.
    #

    if current_term == 1:

        previous_rent = parse_decimal(
            agreement.monthly_rent
        )

    else:

        previous_rent = parse_decimal(
            agreement.get_term_rent(
                current_term - 1
            )
        )

    # =========================================================
    # RENT INCREASE CONFIRMATION
    # =========================================================
    #
    # If the current term has not been accepted yet,
    # show Yes / No confirmation.
    #

    rent_decision = request.POST.get(
        "rent_increase_decision",
        "",
    ).strip().lower()

    if not increase_already_accepted:

        # -----------------------------------------------------
        # First request: show confirmation
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # YES
        # -----------------------------------------------------

        if rent_decision == "yes":

            monthly_rent = proposed_rent

            accept_increase = True

        # -----------------------------------------------------
        # NO
        # -----------------------------------------------------

        else:

            monthly_rent = previous_rent

            accept_increase = False

    else:

        # -----------------------------------------------------
        # Increase was already accepted previously.
        # Do NOT ask again.
        # -----------------------------------------------------

        monthly_rent = proposed_rent

        accept_increase = False

    monthly_rent = parse_decimal(
        monthly_rent
    )

    # =========================================================
    # SAVE RENT HISTORY ONLY WHEN YES
    # =========================================================

    if accept_increase:

        # Close any previous open history for this agreement.
        RentHistory.objects.filter(
            rental_agreement=agreement,
            effective_to__isnull=True,
            effective_from__lt=term_start_date,
        ).update(
            effective_to=term_start_date - date.resolution
        )

        # Find next term date.
        if current_term < 5:

            if current_term == 1:
                next_term_date = agreement.term2_start_date

            elif current_term == 2:
                next_term_date = agreement.term3_start_date

            elif current_term == 3:
                next_term_date = agreement.term4_start_date

            else:
                next_term_date = agreement.term5_start_date

            effective_to = (
                next_term_date - date.resolution
            )

            if (
                agreement.end_date
                and effective_to > agreement.end_date
            ):
                effective_to = agreement.end_date

        else:

            effective_to = agreement.end_date

        # Prevent duplicate history for same term.
        RentHistory.objects.update_or_create(
            rental_agreement=agreement,
            effective_from=term_start_date,
            defaults={
                "effective_to": effective_to,
                "monthly_rent": monthly_rent,
                "increase_percent": increase_percent,
                "increase_accepted": True,
            },
        )

    # =========================================================
    # PARKING
    # =========================================================

    parking_amount = parse_decimal(
        agreement.parking_charge
    )

    # =========================================================
    # PRORATED RENT
    # =========================================================

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

    # =========================================================
    # TAXABLE AMOUNT
    # =========================================================

    taxable_amount = (
        rent_amount +
        parking_amount
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # =========================================================
    # GST
    # =========================================================

    cgst_rate = parse_decimal(
        agreement.cgst_rate
    )

    sgst_rate = parse_decimal(
        agreement.sgst_rate
    )

    cgst_amount = (
        taxable_amount
        * cgst_rate
        / ONE_HUNDRED
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    sgst_amount = (
        taxable_amount
        * sgst_rate
        / ONE_HUNDRED
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    total_amount = (
        taxable_amount
        + cgst_amount
        + sgst_amount
    ).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    # =========================================================
    # PAYMENT DUE DATE
    # =========================================================

    payment_due_day = min(
        agreement.rent_due_day,
        monthrange(
            billing_year,
            billing_month,
        )[1],
    )

    payment_due_date = date(
        billing_year,
        billing_month,
        payment_due_day,
    )

    # =========================================================
    # OWNER GST
    # =========================================================

    owner = agreement.property.owner

    owner_gst = ""

    if owner:

        owner_gst = (
            getattr(
                owner,
                "gst_haryana",
                "",
            )
            or getattr(
                owner,
                "gst_delhi",
                "",
            )
            or ""
        )

    # =========================================================
    # TENANT / PROPERTY
    # =========================================================

    tenant = agreement.tenant

    property_obj = agreement.property

    # =========================================================
    # CREATE INVOICE
    # =========================================================

    with transaction.atomic():

        invoice = Invoice.objects.create(

            rental_agreement=agreement,

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

            # -------------------------------------------------
            # TENANT SNAPSHOT
            # -------------------------------------------------

            tenant_name=tenant.full_name,

            tenant_gst="",

            tenant_pan="",

            tenant_mobile=tenant.mobile,

            tenant_email=tenant.email,

            billing_address=tenant.permanent_address,

            # -------------------------------------------------
            # PROPERTY SNAPSHOT
            # -------------------------------------------------

            property_name=property_obj.name,

            property_address=property_obj.address,

            unit_number=getattr(
                property_obj,
                "unit_no",
                "",
            ),

            # -------------------------------------------------
            # OWNER SNAPSHOT
            # -------------------------------------------------

            owner_name=(
                owner.name
                if owner
                else ""
            ),

            owner_company_name="",

            owner_address=(
                owner.address
                if owner
                else ""
            ),

            owner_city=(
                owner.city
                if owner
                else ""
            ),

            owner_state=(
                owner.state
                if owner
                else ""
            ),

            owner_pincode=(
                owner.pincode
                if owner
                else ""
            ),

            owner_mobile=(
                owner.mobile
                if owner
                else ""
            ),

            owner_email=(
                owner.email
                if owner
                else ""
            ),

            owner_gstin=owner_gst,

            owner_pan=(
                owner.pan
                if owner
                else ""
            ),
        )

        # =====================================================
        # RENT INVOICE ITEM
        # =====================================================

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
                f"({actual_billing_from.strftime('%d %b %Y')}"
                f" - "
                f"{actual_billing_to.strftime('%d %b %Y')})"
            )

        InvoiceItem.objects.create(

            invoice=invoice,

            item_type="rent",

            description=rent_description,

            unit_number=getattr(
                property_obj,
                "unit_no",
                "",
            ),

            area=ZERO,

            rate=monthly_rent,

            slots=1,

            bill_days=bill_days,

            available_days=bill_days,

            amount=rent_amount,
        )

        # =====================================================
        # PARKING
        # =====================================================

        if parking_amount > ZERO:

            InvoiceItem.objects.create(

                invoice=invoice,

                item_type="parking",

                description="Parking Charges",

                unit_number=getattr(
                    property_obj,
                    "unit_no",
                    "",
                ),

                area=ZERO,

                rate=parking_amount,

                slots=1,

                bill_days=bill_days,

                available_days=bill_days,

                amount=parking_amount,
            )

    # =========================================================
    # SUCCESS MESSAGE
    # =========================================================

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
            f"Rent increase was not applied for this month. "
            f"Rent: ₹{monthly_rent:.2f}. "
            f"You will be asked again next month."
        )

    else:

        success_text = (
            f"Invoice #{invoice.invoice_number} generated successfully. "
            f"Term {current_term} rent: ₹{monthly_rent:.2f}"
        )

    messages.success(
        request,
        success_text,
    )

    return redirect(
        "invoice_detail",
        pk=invoice.invoice_number,
    )


# =========================================================
# INVOICES
# =========================================================

def invoice_list(request):

    invoices = (
        Invoice.objects
        .select_related(
            "tenant",
            "rental_agreement",
            "rental_agreement__property",
        )
        .all()
        .order_by(
            "-invoice_date",
            "-invoice_number",
        )
    )

    for invoice in invoices:

        invoice.total_paid = (
            get_invoice_total_paid(
                invoice
            )
        )

        invoice.balance = max(
            invoice.total_amount
            - invoice.total_paid,
            ZERO,
        )

    return render(
        request,
        "core/invoice_list.html",
        {
            "invoices": invoices,
        },
    )


def invoice_detail(request, pk):

    invoice = get_object_or_404(
        Invoice.objects
        .select_related(
            "tenant",
            "rental_agreement",
            "rental_agreement__property",
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

    return render(
        request,
        "core/invoice_detail.html",
        {
            "invoice": invoice,
            "total_paid": total_paid,
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
            "rental_agreement",
            "rental_agreement__property",
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

    total_paid = get_invoice_total_paid(invoice)

    balance = max(
        invoice.total_amount - total_paid,
        ZERO,
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

    if balance <= ZERO:
        messages.warning(
            request,
            "This invoice is already fully paid.",
        )
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    if request.method == "GET":
        return render(
            request,
            "core/payment_form.html",
            {
                "invoice": invoice,
                "balance": balance,
                "today": date.today(),
            },
        )

    payment_amount = parse_decimal(
        request.POST.get("amount")
    )

    payment_date = parse_date(
        request.POST.get("payment_date")
    ) or date.today()

    payment_method = request.POST.get(
        "payment_method",
        "",
    ).strip()

    transaction_reference = request.POST.get(
        "transaction_reference",
        "",
    ).strip()

    notes = request.POST.get(
        "notes",
        "",
    ).strip()

    if payment_amount <= ZERO:
        messages.error(
            request,
            "Payment amount must be greater than zero.",
        )
        return redirect(
            "record_payment",
            invoice_id=invoice.invoice_number,
        )

    if payment_amount > balance:
        messages.error(
            request,
            f"Payment cannot exceed outstanding balance of ₹{balance:,.2f}.",
        )
        return redirect(
            "record_payment",
            invoice_id=invoice.invoice_number,
        )

    with transaction.atomic():

        locked_invoice = (
            Invoice.objects
            .select_for_update()
            .get(
                invoice_number=invoice.invoice_number
            )
        )

        locked_total_paid = (
            Payment.objects
            .filter(invoice=locked_invoice)
            .aggregate(total=Sum("amount"))
            .get("total")
            or ZERO
        )

        locked_balance = max(
            locked_invoice.total_amount - locked_total_paid,
            ZERO,
        )

        if payment_amount > locked_balance:
            messages.error(
                request,
                f"Payment cannot exceed outstanding balance of ₹{locked_balance:,.2f}.",
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

        if new_total_paid >= locked_invoice.total_amount:
            locked_invoice.status = "paid"
            locked_invoice.payment_date = payment_date
        else:
            locked_invoice.status = "pending"

        locked_invoice.save(
            update_fields=[
                "status",
                "payment_date",
            ]
        )

    messages.success(
        request,
        f"Payment of ₹{payment_amount:,.2f} recorded successfully.",
    )

    return redirect(
        "invoice_detail",
        pk=invoice.invoice_number,
    )


    invoice = get_object_or_404(
        Invoice,
        invoice_number=invoice_id,
    )

    total_paid = get_invoice_total_paid(invoice)

    balance = max(
        invoice.total_amount - total_paid,
        ZERO,
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

    if balance <= ZERO:
        messages.warning(
            request,
            "This invoice is already fully paid.",
        )
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    if request.method != "POST":
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    payment_amount = parse_decimal(
        request.POST.get("amount")
    )

    payment_date = parse_date(
        request.POST.get("payment_date")
    ) or date.today()

    payment_method = request.POST.get(
        "payment_method",
        "",
    ).strip()

    transaction_reference = request.POST.get(
        "transaction_reference",
        "",
    ).strip()

    notes = request.POST.get(
        "notes",
        "",
    ).strip()

    if payment_amount <= ZERO:
        messages.error(
            request,
            "Payment amount must be greater than zero.",
        )
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    if payment_amount > balance:
        messages.error(
            request,
            f"Payment cannot exceed outstanding balance of ₹{balance:,.2f}.",
        )
        return redirect(
            "invoice_detail",
            pk=invoice.invoice_number,
        )

    with transaction.atomic():

        locked_invoice = (
            Invoice.objects
            .select_for_update()
            .get(
                invoice_number=invoice.invoice_number
            )
        )

        locked_total_paid = (
            Payment.objects
            .filter(invoice=locked_invoice)
            .aggregate(total=Sum("amount"))
            .get("total")
            or ZERO
        )

        locked_balance = max(
            locked_invoice.total_amount - locked_total_paid,
            ZERO,
        )

        if payment_amount > locked_balance:
            messages.error(
                request,
                f"Payment cannot exceed outstanding balance of ₹{locked_balance:,.2f}.",
            )
            return redirect(
                "invoice_detail",
                pk=locked_invoice.invoice_number,
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

        if new_total_paid >= locked_invoice.total_amount:
            locked_invoice.status = "paid"
            locked_invoice.payment_date = payment_date
        else:
            locked_invoice.status = "pending"

        locked_invoice.save(
            update_fields=[
                "status",
                "payment_date",
            ]
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
        "core/payment_receipt.html",
        {
            "payment": payment,
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
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    payments = Payment.objects.filter(
        invoice=invoice
    ).order_by("-payment_date", "-id")

    total_paid = payments.aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0.00")

    balance = invoice.total_amount - total_paid

    return render(
        request,
        "core/invoice_payment_history.html",
        {
            "invoice": invoice,
            "payments": payments,
            "total_paid": total_paid,
            "balance": balance,
        },
    )
# =========================================================
# DASHBOARD
# =========================================================

def dashboard(request):

    total_properties = (
        Property.objects.count()
    )

    occupied_properties = (
        RentalAgreement.objects
        .filter(
            status="active"
        )
        .values("property")
        .distinct()
        .count()
    )

    vacant_properties = max(
        total_properties
        - occupied_properties,
        0,
    )

    total_tenants = (
        Tenant.objects.count()
    )

    total_invoices = (
        Invoice.objects.count()
    )

    total_invoiced = (
        Invoice.objects
        .aggregate(
            total=Sum("total_amount")
        )["total"]
        or ZERO
    )

    total_collected = (
        Payment.objects
        .aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )

    total_outstanding = max(
        total_invoiced
        - total_collected,
        ZERO,
    )

    recent_payments = (
        Payment.objects
        .select_related(
            "invoice",
            "invoice__tenant",
        )
        .order_by(
            "-payment_date",
            "-id",
        )[:10]
    )

    recent_invoices = (
        Invoice.objects
        .select_related(
            "tenant",
        )
        .order_by(
            "-invoice_date",
            "-invoice_number",
        )[:10]
    )

    context = {

        "total_properties":
            total_properties,

        "occupied_properties":
            occupied_properties,

        "vacant_properties":
            vacant_properties,

        "total_tenants":
            total_tenants,

        "total_invoices":
            total_invoices,

        "total_invoiced":
            total_invoiced,

        "total_collected":
            total_collected,

        "total_outstanding":
            total_outstanding,

        "recent_payments":
            recent_payments,

        "recent_invoices":
            recent_invoices,
    }

    return render(
        request,
        "core/home.html",
        context,
    )


# =========================================================
# FINANCIAL REPORT
# =========================================================

def financial_report(request):

    today = date.today()

    start_date = request.GET.get(
        "start_date",
        today.replace(day=1).isoformat(),
    )

    end_date = request.GET.get(
        "end_date",
        today.isoformat(),
    )

    start = parse_date(start_date)
    end = parse_date(end_date)

    if not start:
        start = today.replace(day=1)

    if not end:
        end = today

    # =========================================================
    # INVOICES IN REPORT PERIOD
    # =========================================================

    invoices = (
        Invoice.objects
        .select_related(
            "tenant",
            "rental_agreement",
        )
        .filter(
            invoice_date__gte=start,
            invoice_date__lte=end,
        )
        .order_by(
            "-invoice_date",
            "-invoice_number",
        )
    )

    # =========================================================
    # TOTAL INVOICED
    # =========================================================

    total_invoiced = (
        invoices.aggregate(
            total=Sum("total_amount")
        )["total"]
        or ZERO
    )

    # =========================================================
    # PAYMENTS FOR THESE INVOICES
    #
    # IMPORTANT:
    # Use invoice__in=invoices instead of
    # invoice_id__in=invoice_numbers.
    # =========================================================

    invoice_payments = Payment.objects.filter(
        invoice__in=invoices
    )

    total_collected = (
        invoice_payments.aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )

    # =========================================================
    # OUTSTANDING
    # =========================================================

    total_outstanding = max(
        total_invoiced - total_collected,
        ZERO,
    )

    # Keep old variable name also, in case another template
    # or code is using it.
    outstanding_amount = total_outstanding

    # =========================================================
    # INVOICE STATUS COUNTS
    # =========================================================

    total_invoices = invoices.count()

    paid_invoices = invoices.filter(
        status="paid"
    ).count()

    pending_invoices = invoices.filter(
        status="pending"
    ).count()

    generated_invoices = invoices.filter(
        status="generated"
    ).count()

    # =========================================================
    # TENANT-WISE OUTSTANDING
    # =========================================================

    tenant_outstanding = []

    for invoice in invoices:

        invoice_paid = (
            Payment.objects
            .filter(invoice=invoice)
            .aggregate(
                total=Sum("amount")
            )["total"]
            or ZERO
        )

        invoice_balance = max(
            invoice.total_amount - invoice_paid,
            ZERO,
        )

        tenant_outstanding.append(
            {
                "renter_name": invoice.tenant_name,
                "tenant_name": invoice.tenant_name,

                "invoice_number": invoice.invoice_number,

                "property_name": invoice.property_name,

                "unit_number": invoice.unit_number,

                "invoice_amount": invoice.total_amount,

                "paid_amount": invoice_paid,

                "outstanding": invoice_balance,

                "due_date": invoice.payment_due_date,
            }
        )

    # =========================================================
    # PROPERTY-WISE COLLECTION
    #
    # Payments received during the selected report period.
    # =========================================================

    property_collection = (
        Payment.objects
        .filter(
            payment_date__gte=start,
            payment_date__lte=end,
        )
        .values(
            "invoice__property_name"
        )
        .annotate(
            total=Sum("amount")
        )
        .order_by(
            "-total"
        )
    )

    # =========================================================
    # PAYMENT HISTORY
    #
    # Payments received during selected period.
    # =========================================================

    recent_payments = (
        Payment.objects
        .select_related(
            "invoice",
            "invoice__tenant",
        )
        .filter(
            payment_date__gte=start,
            payment_date__lte=end,
        )
        .order_by(
            "-payment_date",
            "-id",
        )
    )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "start_date": start.isoformat(),

        "end_date": end.isoformat(),

        # Financial summary
        "total_invoiced": total_invoiced,

        "total_collected": total_collected,

        "total_outstanding": total_outstanding,

        # Compatibility
        "outstanding_amount": outstanding_amount,

        # Invoice counts
        "total_invoices": total_invoices,

        "paid_invoices": paid_invoices,

        "pending_invoices": pending_invoices,

        "generated_invoices": generated_invoices,

        # Tables
        "tenant_outstanding": tenant_outstanding,

        "renter_outstanding": tenant_outstanding,

        "property_collection": property_collection,

        "recent_payments": recent_payments,
    }

    return render(
        request,
        "core/financial_report.html",
        context,
    )

    today = date.today()

    start_date = request.GET.get(
        "start_date",
        today.replace(day=1).isoformat(),
    )

    end_date = request.GET.get(
        "end_date",
        today.isoformat(),
    )

    start = parse_date(
        start_date,
        today.replace(day=1),
    )

    end = parse_date(
        end_date,
        today,
    )

    # =========================================================
    # INVOICES
    # =========================================================

    invoices = (
        Invoice.objects
        .select_related(
            "tenant",
            "rental_agreement",
        )
        .filter(
            invoice_date__gte=start,
            invoice_date__lte=end,
        )
        .order_by(
            "-invoice_date",
            "-invoice_number",
        )
    )

    # =========================================================
    # TOTAL INVOICED
    # =========================================================

    total_invoiced = (
        invoices
        .aggregate(
            total=Sum("total_amount")
        )["total"]
        or ZERO
    )

    # =========================================================
    # INVOICE IDs
    # =========================================================

    invoice_ids = invoices.values_list(
        "invoice_number",
        flat=True,
    )

    # =========================================================
    # TOTAL COLLECTED
    # =========================================================

    total_collected = (
        Payment.objects
        .filter(
            invoice_id__in=invoice_ids
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or ZERO
    )

    # =========================================================
    # OUTSTANDING
    # =========================================================

    outstanding_amount = max(
        total_invoiced - total_collected,
        ZERO,
    )

    # =========================================================
    # TENANT OUTSTANDING
    # =========================================================

    tenant_outstanding = []

    for invoice in invoices:

        invoice_paid = (
            Payment.objects
            .filter(
                invoice=invoice
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or ZERO
        )

        invoice_balance = max(
            invoice.total_amount - invoice_paid,
            ZERO,
        )

        tenant_outstanding.append(
            {
                "tenant_name": invoice.tenant_name,

                "invoice_number": invoice.invoice_number,

                "invoice_amount": invoice.total_amount,

                "paid_amount": invoice_paid,

                "outstanding": invoice_balance,
            }
        )

    # =========================================================
    # CONTEXT
    # =========================================================

    context = {

        "start_date":
            start.isoformat(),

        "end_date":
            end.isoformat(),

        "total_invoiced":
            total_invoiced,

        "total_collected":
            total_collected,

        "outstanding_amount":
            outstanding_amount,

        "total_invoices":
            invoices.count(),

        "tenant_outstanding":
            tenant_outstanding,

        # Compatibility with old template
        "renter_outstanding":
            tenant_outstanding,
    }

    return render(
        request,
        "core/financial_report.html",
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

            # Delete payment records first
            Payment.objects.all().delete()

            # Delete invoice line items
            InvoiceItem.objects.all().delete()

            # Delete invoices
            Invoice.objects.all().delete()

            # Delete rental agreements
            # Related RentHistory records are deleted automatically
            RentalAgreement.objects.all().delete()

            # Delete tenants
            Tenant.objects.all().delete()

            # Owners and Properties are preserved
            # They are master data

        # Reset invoice numbering for SQLite
        try:

            if connection.vendor == "sqlite":

                with connection.cursor() as cursor:

                    cursor.execute(
                        "DELETE FROM sqlite_sequence "
                        "WHERE name = %s",
                        ["core_invoice"],
                    )

        except Exception:
            pass

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