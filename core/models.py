import builtins

from decimal import Decimal, ROUND_HALF_UP

from django.db import models




# =========================================================
# OWNER
# =========================================================

class Owner(models.Model):

    owner_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        null=True,
    )

    name = models.CharField(
        max_length=200,
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    mobile = models.CharField(
        max_length=15,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    pan = models.CharField(
        max_length=20,
        blank=True,
    )

    gst_haryana = models.CharField(
        max_length=20,
        blank=True,
    )

    gst_delhi = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# =========================================================
# PROPERTY
# =========================================================

class Property(models.Model):

    PROPERTY_STATUS = [
        ("active", "Active"),
        ("sold_out", "Sold-out"),
        ("inactive", "Inactive"),
    ]

    owner = models.ForeignKey(
        Owner,
        on_delete=models.PROTECT,
        related_name="properties",
        null=True,
        blank=True,
    )

    # -----------------------------------------------------
    # BASIC PROPERTY DETAILS
    # -----------------------------------------------------

    name = models.CharField(
        max_length=200,
        verbose_name="Property Description",
    )

    address = models.TextField(
        verbose_name="Property Address",
    )

    unit_no = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Unit No",
    )

    tower = models.CharField(
        max_length=100,
        blank=True,
    )

    city = models.CharField(
        max_length=100,
        blank=True,
    )

    state = models.CharField(
        max_length=100,
        blank=True,
    )

    pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    # -----------------------------------------------------
    # PURCHASE DETAILS
    # -----------------------------------------------------

    purchased_on = models.DateField(
        null=True,
        blank=True,
    )

    total_area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Total Area (sq. ft.)",
    )

    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    per_sqft_rate = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    stamp_duty = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    total_purchase_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    # -----------------------------------------------------
    # GST
    # -----------------------------------------------------

    gst_number = models.CharField(
        max_length=20,
        blank=True,
    )

    # -----------------------------------------------------
    # LOAN AGAINST PROPERTY
    # -----------------------------------------------------

    lap_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="LAP Amount",
    )

    monthly_installment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
    )

    lap_maturity = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------
    # PARKING
    # -----------------------------------------------------

    parking_slot = models.CharField(
        max_length=100,
        blank=True,
    )

    # -----------------------------------------------------
    # STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=PROPERTY_STATUS,
        default="active",
    )

    # -----------------------------------------------------
    # TIMESTAMPS
    # -----------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PropertyDocument(models.Model):

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="documents",
    )

    document_name = models.CharField(
        max_length=200,
        verbose_name="Document Name",
    )

    document = models.FileField(
        upload_to="property_documents/",
        verbose_name="Scanned PDF",
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.property.name} - {self.document_name}"



class PropertyTax(models.Model):
    STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("paid", "Paid"),
    ]

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name="property_taxes"
    )
    tax_year = models.CharField(
        max_length=20,
        help_text="Example: 2026-27"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="unpaid"
    )
    paid_on = models.DateField(
        blank=True,
        null=True
    )
    notes = models.TextField(
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-tax_year", "-id"]
        unique_together = ("property", "tax_year")

    def __str__(self):
        return f"{self.property} - {self.tax_year}"


# =========================================================
# TENANT — MASTER DATA
# =========================================================

class Tenant(models.Model):

    TENANT_STATUS = [
        ("active", "Active"),
        ("inactive", "Inactive"),
    ]

    ID_TYPE = [
        ("aadhaar", "Aadhaar"),
        ("pan", "PAN"),
        ("passport", "Passport"),
        ("driving_license", "Driving License"),
        ("voter_id", "Voter ID"),
        ("other", "Other"),
    ]

    full_name = models.CharField(
        max_length=200,
    )

    father_name = models.CharField(
        max_length=200,
        blank=True,
    )

    mobile = models.CharField(
        max_length=15,
        blank=True,
    )

    email = models.EmailField(
        blank=True,
    )

    permanent_address = models.TextField(
        blank=True,
    )

    # NEW — Tenant GST Number
    gst_number = models.CharField(
        max_length=20,
        blank=True,
    )

    # Kept temporarily for compatibility
    # with existing database records.
    id_type = models.CharField(
        max_length=30,
        choices=ID_TYPE,
        default="aadhaar",
    )

    id_type_1 = models.CharField(
        max_length=50,
        blank=True,
    )

    id_number_1 = models.CharField(
        max_length=100,
        blank=True,
    )

    id_type_2 = models.CharField(
        max_length=50,
        blank=True,
    )

    id_number_2 = models.CharField(
        max_length=100,
        blank=True,
    )

    id_type_3 = models.CharField(
        max_length=50,
        blank=True,
    )

    id_number_3 = models.CharField(
        max_length=100,
        blank=True,
    )

    # Kept temporarily for compatibility
    # with existing database records.
    security_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=TENANT_STATUS,
        default="active",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return self.full_name

class TenantContactPerson(models.Model):

    ID_TYPE = [
        ("aadhaar", "Aadhaar"),
        ("pan", "PAN"),
        ("passport", "Passport"),
        ("driving_license", "Driving License"),
        ("voter_id", "Voter ID"),
        ("other", "Other"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="contact_persons",
    )

    designation = models.CharField(
        max_length=100,
        blank=True,
    )

    name = models.CharField(
        max_length=200,
    )

    email = models.EmailField(
        blank=True,
    )

    phone = models.CharField(
        max_length=15,
        blank=True,
    )

    id_type = models.CharField(
        max_length=30,
        choices=ID_TYPE,
        blank=True,
    )

    id_number = models.CharField(
        max_length=100,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} - {self.tenant.full_name}"

# =========================================================
# LEASE AGREEMENT
# =========================================================

class LeaseAgreement(models.Model):

    AGREEMENT_STATUS = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ]

    # =====================================================
    # MASTER DATA
    # =====================================================

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="lease_agreements",
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name="lease_agreements",
    )

    # =====================================================
    # LEASE DATES
    # =====================================================

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    # =====================================================
    # MONTHLY RENT
    # =====================================================

    monthly_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Monthly rent for this lease agreement.",
    )

    # =====================================================
    # LOCK-IN
    # =====================================================

    lock_in_months = models.PositiveIntegerField(
        default=36,
        help_text="Lock-in period in months.",
    )

    # =====================================================
    # RENT-FREE PERIOD
    # =====================================================

    rent_free_months = models.PositiveIntegerField(
        default=0,
        help_text="Number of rent-free months.",
    )

    # =====================================================
    # PARKING
    # =====================================================

    parking_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Monthly parking charge.",
    )

    free_parking_spaces = models.PositiveIntegerField(
        default=0,
        help_text="Number of free parking spaces.",
    )
    paid_parking_spaces = models.PositiveIntegerField(
    default=0,
    help_text="Number of paid parking spaces.",
    )

    # =====================================================
    # SECURITY DEPOSIT
    # =====================================================

    security_deposit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Security deposit for this lease agreement.",
    )
        # =====================================================
    # LEASE EXTENSION 1
    # =====================================================

    extension_1_start_date = models.DateField(
        null=True,
        blank=True,
    )

    extension_1_end_date = models.DateField(
        null=True,
        blank=True,
    )

    extension_1_monthly_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    extension_1_security_deposit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    # =====================================================
    # LEASE EXTENSION 2
    # =====================================================

    extension_2_start_date = models.DateField(
        null=True,
        blank=True,
    )

    extension_2_end_date = models.DateField(
        null=True,
        blank=True,
    )

    extension_2_monthly_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    extension_2_security_deposit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
    )

    rental_area = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    default=0,
    verbose_name="Rental Area (sq. ft.)",
   )


    # =====================================================
    # GST
    # =====================================================

    cgst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    sgst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    # =====================================================
    # PAYMENT
    # =====================================================

    rent_due_day = models.PositiveSmallIntegerField(
        default=5,
    )

    # =====================================================
    # STATUS
    # =====================================================

    status = models.CharField(
        max_length=20,
        choices=AGREEMENT_STATUS,
        default="active",
    )

    # =====================================================
    # TERMINATION
    # =====================================================

    termination_date = models.DateField(
        null=True,
        blank=True,
    )

    termination_reason = models.TextField(
        blank=True,
    )

    # =====================================================
    # NOTES
    # =====================================================

    notes = models.TextField(
        blank=True,
    )

    # =====================================================
    # SYSTEM DATES
    # =====================================================

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    # =====================================================
    # META
    # =====================================================

    class Meta:
        ordering = ["-start_date"]

    # =====================================================
    # MONTHLY RENT + PARKING
    # =====================================================

    @builtins.property
    def total_monthly_amount(self):
        return (
            self.monthly_rent + self.parking_charge
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # CGST
    # =====================================================

    @builtins.property
    def current_cgst_amount(self):
        return (
            self.total_monthly_amount
            * self.cgst_rate
            / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # SGST
    # =====================================================

    @builtins.property
    def current_sgst_amount(self):
        return (
            self.total_monthly_amount
            * self.sgst_rate
            / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # TOTAL INCLUDING GST
    # =====================================================

    @builtins.property
    def current_total_with_gst(self):
        return (
            self.total_monthly_amount
            + self.current_cgst_amount
            + self.current_sgst_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # LOCK-IN END DATE
    # =====================================================

    @builtins.property
    def lock_in_end_date(self):

        if not self.start_date:
            return None

        if self.lock_in_months <= 0:
            return None

        from dateutil.relativedelta import relativedelta

        return (
            self.start_date
            + relativedelta(months=self.lock_in_months)
            - relativedelta(days=1)
        )

    # =====================================================
    # RENT-FREE END DATE
    # =====================================================

    @builtins.property
    def rent_free_end_date(self):

        if not self.start_date:
            return None

        if self.rent_free_months <= 0:
            return None

        from dateutil.relativedelta import relativedelta

        return (
            self.start_date
            + relativedelta(months=self.rent_free_months)
            - relativedelta(days=1)
        )

    # =====================================================
    # RENT-FREE STATUS
    # =====================================================

    def is_rent_free(self, check_date=None):

        if self.rent_free_months <= 0:
            return False

        if check_date is None:
            from datetime import date
            check_date = date.today()

        if not self.start_date:
            return False

        if self.rent_free_end_date is None:
            return False

        return (
            self.start_date
            <= check_date
            <= self.rent_free_end_date
        )

    # =====================================================
    # LOCK-IN STATUS
    # =====================================================

    def is_lock_in(self, check_date=None):

        if self.lock_in_months <= 0:
            return False

        if check_date is None:
            from datetime import date
            check_date = date.today()

        if not self.start_date:
            return False

        if self.lock_in_end_date is None:
            return False

        return (
            self.start_date
            <= check_date
            <= self.lock_in_end_date
        )

    # =====================================================
    # STRING
    # =====================================================

    def __str__(self):
        return (
            f"{self.tenant.full_name} - "
            f"{self.start_date}"
        )

   
# =========================================================
# RENT HISTORY
# =========================================================

class RentHistory(models.Model):

    lease_agreement = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="rent_history",
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    monthly_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
    )

    increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    increase_accepted = models.BooleanField(
        default=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["effective_from"]

    def __str__(self):
        return (
            f"{self.lease_agreement.tenant.full_name} - "
            f"₹{self.monthly_rent} - "
            f"{self.effective_from}"
        )


# =========================================================
# LEASE RENEWAL REMINDERS
# =========================================================

class RenewalReminder(models.Model):

    REMINDER_TYPES = [
        ("six_months", "Six Months Before Expiry"),
        ("monthly", "Monthly Renewal Reminder"),
        ("expiry", "Lease Expiry"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("cancelled", "Cancelled"),
        ("failed", "Failed"),
    ]

    lease_agreement = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="renewal_reminders",
    )

    # The lease term this reminder applies to.
    lease_end_date = models.DateField()

    reminder_date = models.DateField()

    reminder_type = models.CharField(
        max_length=20,
        choices=REMINDER_TYPES,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
    )

    email_sent = models.BooleanField(default=False)

    in_app_created = models.BooleanField(default=False)

    sent_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["reminder_date", "lease_end_date"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "lease_agreement",
                    "lease_end_date",
                    "reminder_date",
                    "reminder_type",
                ],
                name="unique_lease_renewal_reminder",
            ),
        ]

    def __str__(self):
        return (
            f"{self.lease_agreement} - "
            f"{self.reminder_type} - "
            f"{self.reminder_date}"
        )


# =========================================================
# IN-APP NOTIFICATIONS
# =========================================================

class LeaseNotification(models.Model):

    lease_agreement = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    reminder = models.OneToOneField(
        RenewalReminder,
        on_delete=models.CASCADE,
        related_name="notification",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# =========================================================
# INVOICE
# =========================================================

class Invoice(models.Model):

    STATUS_CHOICES = [
        ("generated", "Generated"),
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
    ]

    invoice_number = models.BigAutoField(
        primary_key=True,
    )

    # -----------------------------------------------------
    # TENANT + AGREEMENT
    # -----------------------------------------------------

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    lease_agreement = models.ForeignKey(
        LeaseAgreement,
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    invoice_date = models.DateField()

    billing_from = models.DateField()

    billing_to = models.DateField()

    payment_due_date = models.DateField(
        null=True,
        blank=True,
    )

    payment_date = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------
    # FINANCIAL VALUES
    # -----------------------------------------------------

    taxable_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    cgst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    cgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    sgst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
    )

    sgst_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="generated",
    )

    # =====================================================
    # TENANT SNAPSHOT
    # =====================================================

    tenant_name = models.CharField(
        max_length=200,
        blank=True,
    )

    tenant_gst = models.CharField(
        max_length=20,
        blank=True,
    )

    tenant_pan = models.CharField(
        max_length=20,
        blank=True,
    )

    tenant_mobile = models.CharField(
        max_length=15,
        blank=True,
    )

    tenant_email = models.EmailField(
        blank=True,
    )

    billing_address = models.TextField(
        blank=True,
    )

    # =====================================================
    # PROPERTY SNAPSHOT
    # =====================================================

    property_name = models.CharField(
        max_length=200,
        blank=True,
    )

    property_address = models.TextField(
        blank=True,
    )

    unit_number = models.CharField(
        max_length=50,
        blank=True,
    )

    # =====================================================
    # OWNER SNAPSHOT
    # =====================================================

    owner_name = models.CharField(
        max_length=200,
        blank=True,
    )

    owner_company_name = models.CharField(
        max_length=200,
        blank=True,
    )

    owner_address = models.TextField(
        blank=True,
    )

    owner_city = models.CharField(
        max_length=100,
        blank=True,
    )

    owner_state = models.CharField(
        max_length=100,
        blank=True,
    )

    owner_pincode = models.CharField(
        max_length=10,
        blank=True,
    )

    owner_mobile = models.CharField(
        max_length=15,
        blank=True,
    )

    owner_email = models.EmailField(
        blank=True,
    )

    owner_gstin = models.CharField(
        max_length=20,
        blank=True,
    )

    owner_pan = models.CharField(
        max_length=20,
        blank=True,
    )

    # -----------------------------------------------------
    # SYSTEM DATES
    # -----------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-invoice_number"]

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

# =========================================================
# INVOICE ITEM
# =========================================================

class InvoiceItem(models.Model):

    ITEM_TYPES = [
        ("rent", "Rent"),
        ("parking", "Parking"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    item_type = models.CharField(
        max_length=20,
        choices=ITEM_TYPES,
    )

    description = models.CharField(
        max_length=255,
    )

    unit_number = models.CharField(
        max_length=50,
        blank=True,
    )

    area = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    slots = models.PositiveIntegerField(
        default=1,
    )

    bill_days = models.PositiveIntegerField(
        default=0,
    )

    available_days = models.PositiveIntegerField(
        default=0,
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):

        return (
            f"{self.description} - "
            f"Invoice #{self.invoice.invoice_number}"
        )


# =========================================================
# PAYMENT
# =========================================================

class Payment(models.Model):

    PAYMENT_METHODS = [
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("upi", "UPI"),
        ("cheque", "Cheque"),
        ("other", "Other"),
    ]

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    payment_date = models.DateField()

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHODS,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-payment_date",
            "-id",
        ]

    def __str__(self):

        return (
            f"Payment ₹{self.amount} - "
            f"Invoice #{self.invoice.invoice_number}"
        )