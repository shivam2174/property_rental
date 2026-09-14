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

    # Kept for compatibility with your existing database.
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


# =========================================================
# RENTAL AGREEMENT
# =========================================================

class RentalAgreement(models.Model):

    AGREEMENT_STATUS = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("terminated", "Terminated"),
    ]

    # -----------------------------------------------------
    # MASTER DATA CONNECTIONS
    # -----------------------------------------------------

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="rental_agreements",
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name="rental_agreements",
    )

    # -----------------------------------------------------
    # AGREEMENT PERIOD
    # -----------------------------------------------------

    start_date = models.DateField()

    end_date = models.DateField(
        null=True,
        blank=True,
    )

    # -----------------------------------------------------
    # BASE MONTHLY RENT
    # -----------------------------------------------------

    monthly_rent = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Base monthly rent before term increases.",
    )

    # =====================================================
    # 5 TERM RENT ESCALATION
    # =====================================================

    term1_increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("5.00"),
        help_text="Rent increase percentage for Term 1.",
    )

    term2_increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("10.00"),
        help_text="Rent increase percentage for Term 2.",
    )

    term3_increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("15.00"),
        help_text="Rent increase percentage for Term 3.",
    )

    term4_increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("20.00"),
        help_text="Rent increase percentage for Term 4.",
    )

    term5_increase_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("25.00"),
        help_text="Rent increase percentage for Term 5.",
    )

    # -----------------------------------------------------
    # NEXT TERM INFORMATION
    # -----------------------------------------------------

    next_increase_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when the next rent term starts.",
    )

    # Kept for database compatibility.
    # Automatic invoice generation does not use this field.
    rent_increase_pending = models.BooleanField(
        default=False,
        help_text="Legacy field. Automatic term escalation does not require approval.",
    )

    # -----------------------------------------------------
    # PARKING
    # -----------------------------------------------------

    parking_charge = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # -----------------------------------------------------
    # SECURITY DEPOSIT
    # -----------------------------------------------------

    security_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    # -----------------------------------------------------
    # GST
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------

    rent_due_day = models.PositiveSmallIntegerField(
        default=5,
    )

    # -----------------------------------------------------
    # AGREEMENT STATUS
    # -----------------------------------------------------

    status = models.CharField(
        max_length=20,
        choices=AGREEMENT_STATUS,
        default="active",
    )

    # -----------------------------------------------------
    # TERMINATION
    # -----------------------------------------------------

    termination_date = models.DateField(
        null=True,
        blank=True,
    )

    termination_reason = models.TextField(
        blank=True,
    )

    # -----------------------------------------------------
    # NOTES
    # -----------------------------------------------------

    notes = models.TextField(
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
        ordering = ["-start_date"]

    # =====================================================
    # TERM DATES
    # =====================================================

    @builtins.property
    def term1_start_date(self):
        return self.start_date

    @builtins.property
    def term2_start_date(self):
        return self._add_years(
            self.start_date,
            1,
        )

    @builtins.property
    def term3_start_date(self):
        return self._add_years(
            self.start_date,
            2,
        )

    @builtins.property
    def term4_start_date(self):
        return self._add_years(
            self.start_date,
            3,
        )

    @builtins.property
    def term5_start_date(self):
        return self._add_years(
            self.start_date,
            4,
        )

    # =====================================================
    # ADD YEARS SAFELY
    # =====================================================

    @staticmethod
    def _add_years(date_value, years):
        """
        Add years safely.
        Handles February 29.
        """

        from datetime import date

        try:
            return date(
                date_value.year + years,
                date_value.month,
                date_value.day,
            )

        except ValueError:
            return date(
                date_value.year + years,
                2,
                28,
            )

    # =====================================================
    # TERM 1 RENT
    # =====================================================

    @builtins.property
    def term1_rent(self):

        increase = (
            self.monthly_rent
            * self.term1_increase_percent
        ) / Decimal("100")

        return (
            self.monthly_rent + increase
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # TERM 2 RENT
    # =====================================================

    @builtins.property
    def term2_rent(self):

        increase = (
            self.term1_rent
            * self.term2_increase_percent
        ) / Decimal("100")

        return (
            self.term1_rent + increase
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # TERM 3 RENT
    # =====================================================

    @builtins.property
    def term3_rent(self):

        increase = (
            self.term2_rent
            * self.term3_increase_percent
        ) / Decimal("100")

        return (
            self.term2_rent + increase
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # TERM 4 RENT
    # =====================================================

    @builtins.property
    def term4_rent(self):

        increase = (
            self.term3_rent
            * self.term4_increase_percent
        ) / Decimal("100")

        return (
            self.term3_rent + increase
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # TERM 5 RENT
    # =====================================================

    @builtins.property
    def term5_rent(self):

        increase = (
            self.term4_rent
            * self.term5_increase_percent
        ) / Decimal("100")

        return (
            self.term4_rent + increase
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # GET CURRENT TERM
    # =====================================================

    def get_current_term(self, on_date=None):

        from datetime import date

        if on_date is None:
            on_date = date.today()

        if on_date < self.term2_start_date:
            return 1

        if on_date < self.term3_start_date:
            return 2

        if on_date < self.term4_start_date:
            return 3

        if on_date < self.term5_start_date:
            return 4

        return 5

    # =====================================================
    # GET RENT FOR TERM
    # =====================================================

    def get_term_rent(self, term_number):

        if term_number == 1:
            return self.term1_rent

        if term_number == 2:
            return self.term2_rent

        if term_number == 3:
            return self.term3_rent

        if term_number == 4:
            return self.term4_rent

        if term_number == 5:
            return self.term5_rent

        return self.monthly_rent

    # =====================================================
    # CURRENT AUTOMATIC RENT
    # =====================================================

    def get_current_rent(self, on_date=None):

        term = self.get_current_term(
            on_date
        )

        return self.get_term_rent(
            term
        )

    # =====================================================
    # CURRENT TERM PERCENT
    # =====================================================

    def get_current_increase_percent(
        self,
        on_date=None,
    ):

        term = self.get_current_term(
            on_date
        )

        if term == 1:
            return self.term1_increase_percent

        if term == 2:
            return self.term2_increase_percent

        if term == 3:
            return self.term3_increase_percent

        if term == 4:
            return self.term4_increase_percent

        return self.term5_increase_percent

    # =====================================================
    # CURRENT TOTAL
    # =====================================================

    @builtins.property
    def total_monthly_amount(self):

        current_rent = self.get_current_rent()

        return (
            current_rent
            + self.parking_charge
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # PROPOSED NEXT RENT
    # =====================================================

    @builtins.property
    def proposed_rent(self):

        current_term = self.get_current_term()

        next_term = current_term + 1

        if next_term > 5:
            return self.get_current_rent()

        return self.get_term_rent(
            next_term
        )

    # =====================================================
    # PROPOSED INCREASE AMOUNT
    # =====================================================

    @builtins.property
    def proposed_increase_amount(self):

        return (
            self.proposed_rent
            - self.get_current_rent()
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # PROPOSED TOTAL INCLUDING PARKING
    # =====================================================

    @builtins.property
    def proposed_total_monthly_amount(self):

        return (
            self.proposed_rent
            + self.parking_charge
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # CURRENT GST
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
    # PROPOSED GST
    # =====================================================

    @builtins.property
    def proposed_cgst_amount(self):

        return (
            self.proposed_total_monthly_amount
            * self.cgst_rate
            / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    @builtins.property
    def proposed_sgst_amount(self):

        return (
            self.proposed_total_monthly_amount
            * self.sgst_rate
            / Decimal("100")
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

    # =====================================================
    # CURRENT TOTAL INCLUDING GST
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
    # PROPOSED TOTAL INCLUDING GST
    # =====================================================

    @builtins.property
    def proposed_total_with_gst(self):

        return (
            self.proposed_total_monthly_amount
            + self.proposed_cgst_amount
            + self.proposed_sgst_amount
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
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

    rental_agreement = models.ForeignKey(
        RentalAgreement,
        on_delete=models.CASCADE,
        related_name="rent_history",
    )

    effective_from = models.DateField()

    effective_to = models.DateField(
        null=True,
        blank=True,
    )

    monthly_rent = models.DecimalField(
        max_digits=12,
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
            f"{self.rental_agreement.tenant.full_name} - "
            f"₹{self.monthly_rent} - "
            f"{self.effective_from}"
        )


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

    rental_agreement = models.ForeignKey(
        RentalAgreement,
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