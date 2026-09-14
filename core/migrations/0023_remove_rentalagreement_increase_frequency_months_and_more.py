

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_rentalagreement_term1_increase_percent_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rentalagreement',
            name='increase_frequency_months',
        ),
        migrations.RemoveField(
            model_name='rentalagreement',
            name='rent_increase_percent',
        ),
        migrations.AlterField(
            model_name='rentalagreement',
            name='monthly_rent',
            field=models.DecimalField(decimal_places=2, default=0, help_text='Base monthly rent before term increases.', max_digits=12),
        ),
        migrations.AlterField(
            model_name='rentalagreement',
            name='next_increase_date',
            field=models.DateField(blank=True, help_text='Date when the next rent term starts.', null=True),
        ),
        migrations.AlterField(
            model_name='rentalagreement',
            name='rent_increase_pending',
            field=models.BooleanField(default=False, help_text='Legacy field. Automatic term escalation does not require approval.'),
        ),
    ]
