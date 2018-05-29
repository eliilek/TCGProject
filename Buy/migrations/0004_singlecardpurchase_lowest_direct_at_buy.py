# Generated by Django 2.0.3 on 2018-04-18 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Buy', '0003_singlecardpurchase_initial_sell_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlecardpurchase',
            name='lowest_direct_at_buy',
            field=models.DecimalField(decimal_places=2, default=0, editable=False, max_digits=6),
            preserve_default=False,
        ),
    ]
