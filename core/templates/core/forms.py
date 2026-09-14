from django import forms
from .models import Tenant, RentalAgreement, Property


# =========================================================
# TENANT FORM
# =========================================================

class TenantForm(forms.ModelForm):

    class Meta:
        model = Tenant

        fields = [
            "full_name",
            "father_name",
            "mobile",
            "email",
            "permanent_address",
            "id_type",
            "id_number",
            "move_in_date",
            "security_deposit",
            "status",
        ]

        labels = {
            "full_name": "Full Name",
            "father_name": "Father Name",
            "mobile": "Mobile Number",
            "email": "Email",
            "permanent_address": "Permanent Address",
            "id_type": "ID Type",
            "id_number": "ID Number",
            "move_in_date": "Move-in Date",
            "security_deposit": "Security Deposit",
            "status": "Status",
        }

        widgets = {

            "full_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter tenant full name",
                }
            ),

            "father_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter father's name",
                }
            ),

            "mobile": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter mobile number",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter email address",
                }
            ),

            "permanent_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter permanent address",
                    "rows": 3,
                }
            ),

            "id_type": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "id_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter ID number",
                }
            ),

            "move_in_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "security_deposit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter security deposit",
                    "step": "0.01",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
        }


# =========================================================
# RENTAL AGREEMENT FORM
# =========================================================

class AgreementForm(forms.ModelForm):

    class Meta:
        model = RentalAgreement

        fields = [
            # Master data
            "tenant",
            "property",

            # Agreement period
            "start_date",
            "end_date",

            # Base rent
            "monthly_rent",

            # 5 term increases
            "term1_increase_percent",
            "term2_increase_percent",
            "term3_increase_percent",
            "term4_increase_percent",
            "term5_increase_percent",

            # Next term
            "next_increase_date",

            # Parking
            "parking_charge",

            # Security
            "security_deposit",

            # GST
            "cgst_rate",
            "sgst_rate",

            # Payment
            "rent_due_day",

            # Status
            "status",

            # Notes
            "notes",
        ]

        labels = {
            "tenant": "Tenant",
            "property": "Property",

            "start_date": "Agreement Start Date",
            "end_date": "Agreement End Date",

            "monthly_rent": "Base Monthly Rent",

            "term1_increase_percent": "Term 1 Increase (%)",
            "term2_increase_percent": "Term 2 Increase (%)",
            "term3_increase_percent": "Term 3 Increase (%)",
            "term4_increase_percent": "Term 4 Increase (%)",
            "term5_increase_percent": "Term 5 Increase (%)",

            "next_increase_date": "Next Increase Date",

            "parking_charge": "Parking Charge",

            "security_deposit": "Security Deposit",

            "cgst_rate": "CGST Rate (%)",
            "sgst_rate": "SGST Rate (%)",

            "rent_due_day": "Rent Due Day",

            "status": "Agreement Status",

            "notes": "Notes",
        }

        widgets = {

            # -------------------------------------------------
            # TENANT
            # -------------------------------------------------

            "tenant": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            # -------------------------------------------------
            # PROPERTY
            # -------------------------------------------------

            "property": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            # -------------------------------------------------
            # AGREEMENT PERIOD
            # -------------------------------------------------

            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            # -------------------------------------------------
            # BASE RENT
            # -------------------------------------------------

            "monthly_rent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter base monthly rent",
                    "step": "0.01",
                }
            ),

            # -------------------------------------------------
            # TERM 1
            # -------------------------------------------------

            "term1_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 5",
                }
            ),

            # -------------------------------------------------
            # TERM 2
            # -------------------------------------------------

            "term2_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 10",
                }
            ),

            # -------------------------------------------------
            # TERM 3
            # -------------------------------------------------

            "term3_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 15",
                }
            ),

            # -------------------------------------------------
            # TERM 4
            # -------------------------------------------------

            "term4_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 20",
                }
            ),

            # -------------------------------------------------
            # TERM 5
            # -------------------------------------------------

            "term5_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 25",
                }
            ),

            # -------------------------------------------------
            # NEXT INCREASE
            # -------------------------------------------------

            "next_increase_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            # -------------------------------------------------
            # PARKING
            # -------------------------------------------------

            "parking_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter parking charge",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            # -------------------------------------------------
            # SECURITY DEPOSIT
            # -------------------------------------------------

            "security_deposit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter security deposit",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            # -------------------------------------------------
            # GST
            # -------------------------------------------------

            "cgst_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 9",
                }
            ),

            "sgst_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 9",
                }
            ),

            # -------------------------------------------------
            # RENT DUE DAY
            # -------------------------------------------------

            "rent_due_day": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "31",
                    "placeholder": "Example: 5",
                }
            ),

            # -------------------------------------------------
            # STATUS
            # -------------------------------------------------

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            # -------------------------------------------------
            # NOTES
            # -------------------------------------------------

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter agreement notes",
                }
            ),
        }

    def clean_rent_due_day(self):
        value = self.cleaned_data["rent_due_day"]

        if value < 1 or value > 31:
            raise forms.ValidationError(
                "Rent due day must be between 1 and 31."
            )

        return value