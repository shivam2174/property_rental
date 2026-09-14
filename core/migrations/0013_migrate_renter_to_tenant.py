from django.db import migrations


def migrate_renter_to_tenant(apps, schema_editor):
    Renter = apps.get_model("core", "Renter")
    Tenant = apps.get_model("core", "Tenant")
    RentalAgreement = apps.get_model("core", "RentalAgreement")
    Invoice = apps.get_model("core", "Invoice")

    # =====================================================
    # 1. CREATE TENANTS FROM EXISTING RENTERS
    # =====================================================

    renter_to_tenant = {}

    for renter in Renter.objects.all().order_by("id"):

        tenant = Tenant.objects.create(
            full_name=renter.full_name,
            father_name=renter.father_name,
            mobile=renter.mobile,
            email=renter.email,
            permanent_address=renter.permanent_address,
            id_type=renter.id_type,
            id_number=renter.id_number,
            move_in_date=renter.move_in_date,
            security_deposit=renter.security_deposit,
            status=renter.status,
        )

        renter_to_tenant[renter.id] = tenant

    # =====================================================
    # 2. MIGRATE RENTAL AGREEMENTS
    # =====================================================
    #
    # Old structure:
    #
    # RentalAgreement -> Renter -> Unit -> Property
    #
    # New structure:
    #
    # RentalAgreement -> Tenant
    #                  -> Unit
    #                  -> Property
    #
    # =====================================================

    for agreement in RentalAgreement.objects.select_related(
        "renter",
        "renter__unit",
        "renter__unit__property",
    ).all():

        if agreement.renter_id is None:
            raise RuntimeError(
                f"RentalAgreement #{agreement.id} has no Renter."
            )

        tenant = renter_to_tenant.get(agreement.renter_id)

        if tenant is None:
            raise RuntimeError(
                f"Could not find Tenant for Renter "
                f"#{agreement.renter_id}."
            )

        old_unit = agreement.renter.unit

        if old_unit is None:
            raise RuntimeError(
                f"RentalAgreement #{agreement.id} has no Unit "
                f"through its Renter."
            )

        old_property = old_unit.property

        if old_property is None:
            raise RuntimeError(
                f"RentalAgreement #{agreement.id} has no Property "
                f"through its Unit."
            )

        agreement.tenant = tenant
        agreement.unit = old_unit
        agreement.property = old_property

        agreement.save(
            update_fields=[
                "tenant",
                "unit",
                "property",
            ]
        )

    # =====================================================
    # 3. MIGRATE INVOICES
    # =====================================================
    #
    # Existing Invoice -> Renter
    #
    # becomes
    #
    # Invoice -> Tenant
    #
    # Existing invoice snapshot fields are NOT changed.
    # This is important for historical records.
    # =====================================================

    for invoice in Invoice.objects.select_related(
        "renter"
    ).all():

        if invoice.renter_id is None:
            raise RuntimeError(
                f"Invoice #{invoice.invoice_number} has no Renter."
            )

        tenant = renter_to_tenant.get(invoice.renter_id)

        if tenant is None:
            raise RuntimeError(
                f"Could not find Tenant for Invoice "
                f"#{invoice.invoice_number}."
            )

        invoice.tenant = tenant

        invoice.save(
            update_fields=[
                "tenant",
            ]
        )


def reverse_migration(apps, schema_editor):
    """
    Reverse the Tenant links without deleting Tenant records.

    This keeps the migration reversible without risking
    accidental deletion of migrated tenant data.
    """

    RentalAgreement = apps.get_model("core", "RentalAgreement")
    Invoice = apps.get_model("core", "Invoice")

    RentalAgreement.objects.all().update(
        tenant=None
    )

    Invoice.objects.all().update(
        tenant=None
    )


class Migration(migrations.Migration):

    dependencies = [
        (
            "core",
            "0012_tenant_remove_unit_unique_unit_per_property_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            migrate_renter_to_tenant,
            reverse_migration,
        ),
    ]