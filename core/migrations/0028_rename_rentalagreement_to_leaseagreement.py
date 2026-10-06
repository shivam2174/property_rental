from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0027_tenantcontactperson"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="RentalAgreement",
            new_name="LeaseAgreement",
        ),

        migrations.RenameField(
            model_name="invoice",
            old_name="rental_agreement",
            new_name="lease_agreement",
        ),

        migrations.RenameField(
            model_name="renthistory",
            old_name="rental_agreement",
            new_name="lease_agreement",
        ),
    ]