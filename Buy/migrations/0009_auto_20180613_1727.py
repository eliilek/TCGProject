# Generated by Django 2.0.3 on 2018-06-13 22:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Buy', '0008_singlecardpurchase_base_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='singlecardpurchase',
            name='tcgplayer_LP_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='singlecardpurchase',
            name='tcgplayer_NM_id',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
