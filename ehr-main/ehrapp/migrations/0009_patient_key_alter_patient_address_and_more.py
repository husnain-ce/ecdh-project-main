# Generated by Django 4.2.3 on 2023-08-07 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ehrapp', '0008_patient_last_updated_patient_updated_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='patient',
            name='key',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AlterField(
            model_name='patient',
            name='address',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='patient',
            name='admitDate',
            field=models.TextField(blank=True, default='2023-08-07 13:03:51'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='assignedDoctorId',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='patient',
            name='bp_1s',
            field=models.TextField(blank=True, default='0'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='cholesterol_level',
            field=models.TextField(blank=True, default='0'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='last_updated',
            field=models.TextField(blank=True, default='2023-08-07 13:03:51'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='patient',
            name='status',
            field=models.TextField(blank=True, default='True'),
        ),
        migrations.AlterField(
            model_name='patient',
            name='treatment_type',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='patient',
            name='weight_lb',
            field=models.TextField(blank=True, default='0'),
        ),
    ]
