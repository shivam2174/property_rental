from django import forms
from .models import Tenant, LeaseAgreement, Property, PropertyTax, PropertyDocument


class TenantForm(forms.ModelForm):

    class Meta:
        model = Tenant
        fields = [
            "full_name",
            "father_name",
            "mobile",
            "email",
            "permanent_address",
            "gst_number",
            "status",
        ]

        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter tenant full name",
                }
            ),

            "father_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter father name",
                }
            ),

            "mobile": forms.TextInput(
                attrs={
                    "placeholder": "Enter mobile number",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email address",
                }
            ),

            "permanent_address": forms.Textarea(
                attrs={
                    "placeholder": "Enter permanent address",
                    "rows": 3,
                }
            ),

            "gst_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter GST number",
                }
            ),

            "status": forms.Select(),
        }
        
# =========================================================
# RENTAL AGREEMENT FORM
# =========================================================
class AgreementForm(forms.ModelForm):

    rental_area = forms.DecimalField(
        label="Rental Area (sq. ft.)",
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "step": "0.01",
            "placeholder": "Enter rental area",
            "min": "0",
        }),
    )

    class Meta:
        model = LeaseAgreement

        fields = [
            "tenant",
            "property",
            "start_date",
            "end_date",
            "monthly_rent",
            "lock_in_months",
            "rent_free_months",
            "parking_charge",
            "free_parking_spaces",
            "paid_parking_spaces",
            "security_deposit",
            "extension_1_start_date",
            "extension_1_end_date",
            "extension_1_monthly_rent",
            "extension_1_security_deposit",
            "extension_2_start_date",
            "extension_2_end_date",
            "extension_2_monthly_rent",
            "extension_2_security_deposit",
            "cgst_rate",
            "sgst_rate",
            "rental_area",
            "rent_due_day",
            "status",
            "termination_date",
            "termination_reason",
            "notes",
        ]

        labels = {
            "tenant": "Tenant",
            "property": "Property",
            "start_date": "Lease Start Date",
            "end_date": "Lease End Date",
            "monthly_rent": "Monthly Rent",
            "lock_in_months": "Lock-in Period (Months)",
            "rent_free_months": "Rent-Free Period (Months)",
            "parking_charge": "Monthly Parking Charge",
            "free_parking_spaces": "Free Parking Spaces",
            "paid_parking_spaces": "Paid Parking Spaces",
            "security_deposit": "Security Deposit",
            "extension_1_start_date": "Extension 1 Start Date",
            "extension_1_end_date": "Extension 1 End Date",
            "extension_1_monthly_rent": "Extension 1 Monthly Rent",
            "extension_1_security_deposit": "Extension 1 Security Deposit",
            "extension_2_start_date": "Extension 2 Start Date",
            "extension_2_end_date": "Extension 2 End Date",
            "extension_2_monthly_rent": "Extension 2 Monthly Rent",
            "extension_2_security_deposit": "Extension 2 Security Deposit",
            "cgst_rate": "CGST Rate (%)",
            "sgst_rate": "SGST Rate (%)",
            "rental_area": "Rental Area (sq. ft.)",
            "rent_due_day": "Rent Due Day",
            "status": "Lease Status",
            "termination_date": "Termination Date",
            "termination_reason": "Termination Reason",
            "notes": "Notes",
        }

        widgets = {
            "tenant": forms.Select(attrs={"class": "form-control"}),
            "property": forms.Select(attrs={"class": "form-control"}),

            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),

            "monthly_rent": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter monthly rent",
                "step": "0.01",
                "min": "0",
            }),
            "lock_in_months": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": "Example: 36",
            }),
            "rent_free_months": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": "Example: 2",
            }),
            "parking_charge": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter monthly parking charge",
                "step": "0.01",
                "min": "0",
            }),
            "free_parking_spaces": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": "Example: 11",
            }),
            "paid_parking_spaces": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": "Example: 1",
            }),
            "security_deposit": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter security deposit",
                "step": "0.01",
                "min": "0",
            }),

            "extension_1_start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "extension_1_end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "extension_1_monthly_rent": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "Enter Extension 1 monthly rent",
            }),
            "extension_1_security_deposit": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "Enter Extension 1 security deposit",
            }),

            "extension_2_start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "extension_2_end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "extension_2_monthly_rent": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "Enter Extension 2 monthly rent",
            }),
            "extension_2_security_deposit": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "Enter Extension 2 security deposit",
            }),

            "cgst_rate": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),
            "sgst_rate": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
            }),

            "rent_due_day": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "31",
            }),
            "status": forms.Select(attrs={"class": "form-control"}),
            "termination_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date",
            }),
            "termination_reason": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
            }),
        }


# =========================================================
# PROPERTY TAX FORM
# =========================================================

class PropertyTaxForm(forms.ModelForm):

    class Meta:
        model = PropertyTax

        fields = [
            "tax_year",
            "tax_amount",
            "status",
            "paid_on",
            "notes",
        ]

        widgets = {
            "tax_year": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 2026-27",
                }
            ),

            "tax_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "Enter tax amount",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "paid_on": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Optional notes",
                }
            ),
        }





# =========================================================
# PROPERTY DOCUMENT FORM
# =========================================================

class PropertyDocumentForm(forms.ModelForm):

    class Meta:
        model = PropertyDocument

        fields = [
            "document_name",
            "document",
        ]

        widgets = {
            "document_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Sale Deed",
                }
            ),

            "document": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "application/pdf",
                }
            ),
        }

        labels = {
            "document_name": "Document Name",
            "document": "Scanned PDF",
        }

    def clean_document(self):
        document = self.cleaned_data.get("document")

        if document:
            if not document.name.lower().endswith(".pdf"):
                raise forms.ValidationError(
                    "Only PDF files are allowed."
                )

            if document.content_type != "application/pdf":
                raise forms.ValidationError(
                    "Please upload a valid PDF file."
                )

        return document

