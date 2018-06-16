# Generated by Django 2.0.3 on 2018-06-09 22:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Buy', '0006_salescheckdatetime'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlecardpurchase',
            name='lowest_direct_at_sell',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
