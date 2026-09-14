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

            "id_type_1",
            "id_number_1",
            "id_type_2",
            "id_number_2",
            "id_type_3",
            "id_number_3",

            "security_deposit",
            "status",
        ]

        labels = {
            "full_name": "Full Name",
            "father_name": "Father Name",
            "mobile": "Mobile Number",
            "email": "Email",
            "permanent_address": "Permanent Address",

            "id_type_1": "ID 1 Type",
            "id_number_1": "ID 1 Number",

            "id_type_2": "ID 2 Type",
            "id_number_2": "ID 2 Number",

            "id_type_3": "ID 3 Type",
            "id_number_3": "ID 3 Number",

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

            "id_type_1": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "id_number_1": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter ID 1 number",
                }
            ),

            "id_type_2": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "id_number_2": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter ID 2 number",
                }
            ),

            "id_type_3": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "id_number_3": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter ID 3 number",
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

    def clean(self):
        cleaned_data = super().clean()

        id_type_1 = cleaned_data.get("id_type_1")
        id_number_1 = cleaned_data.get("id_number_1")

        id_type_2 = cleaned_data.get("id_type_2")
        id_number_2 = cleaned_data.get("id_number_2")

        id_type_3 = cleaned_data.get("id_type_3")
        id_number_3 = cleaned_data.get("id_number_3")

        if not id_type_1:
            self.add_error(
                "id_type_1",
                "ID 1 Type is required.",
            )

        if not id_number_1:
            self.add_error(
                "id_number_1",
                "ID 1 Number is required.",
            )

        if not id_type_2:
            self.add_error(
                "id_type_2",
                "ID 2 Type is required.",
            )

        if not id_number_2:
            self.add_error(
                "id_number_2",
                "ID 2 Number is required.",
            )

        if id_type_3 and not id_number_3:
            self.add_error(
                "id_number_3",
                "ID 3 Number is required when ID 3 Type is selected.",
            )

        if id_number_3 and not id_type_3:
            self.add_error(
                "id_type_3",
                "ID 3 Type is required when ID 3 Number is entered.",
            )

        id_types = [
            ("id_type_1", id_type_1),
            ("id_type_2", id_type_2),
            ("id_type_3", id_type_3),
        ]

        seen = set()

        for field_name, id_type in id_types:

            if not id_type:
                continue

            if id_type in seen:
                self.add_error(
                    field_name,
                    "This ID type has already been selected. Please choose a different ID type.",
                )
            else:
                seen.add(id_type)

        return cleaned_data


# =========================================================
# RENTAL AGREEMENT FORM
# =========================================================

class AgreementForm(forms.ModelForm):

    class Meta:
        model = RentalAgreement

        fields = [
            "tenant",
            "property",
            "start_date",
            "end_date",
            "monthly_rent",
            "term1_increase_percent",
            "term2_increase_percent",
            "term3_increase_percent",
            "term4_increase_percent",
            "term5_increase_percent",
            "next_increase_date",
            "parking_charge",
            "security_deposit",
            "cgst_rate",
            "sgst_rate",
            "rent_due_day",
            "status",
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
            "tenant": forms.Select(
                attrs={"class": "form-control"}
            ),

            "property": forms.Select(
                attrs={"class": "form-control"}
            ),

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

            "monthly_rent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Enter base monthly rent",
                    "step": "0.01",
                }
            ),

            "term1_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 5",
                }
            ),

            "term2_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 10",
                }
            ),

            "term3_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 15",
                }
            ),

            "term4_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 20",
                }
            ),

            "term5_increase_percent": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Example: 25",
                }
            ),

            "next_increase_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "parking_charge": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "security_deposit": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "cgst_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "sgst_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),

            "rent_due_day": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "1",
                    "max": "31",
                }
            ),

            "status": forms.Select(
                attrs={"class": "form-control"}
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                }
            ),
        }