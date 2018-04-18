from django.db import models
from django.utils import timezone

class StandardSet(models.Model):
    abbreviation = models.CharField(max_length=5, blank=True, default="")
    name = models.CharField(max_length=200)

class Token(models.Model):
    bearer = models.CharField(max_length=1000, blank=True, default="")
    expires = models.DateTimeField(blank=True, null=True)

class Seller(models.Model):
    name = models.CharField(max_length=100, unique=True)
    email = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    notes = models.CharField(max_length=500, default="")

    def __unicode__(self):
        return self.name

# Create your models here.
class CardPurchaseBlock(models.Model):
    seller = models.ForeignKey(Seller, on_delete=models.SET_NULL, null=True)
    bought_on = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if not self.id:
            self.bought_on = timezone.now()
        return super(SingleCardPurchase, self).save(*args, **kwargs)

class SingleCardPurchase(models.Model):
    block = models.ForeignKey(CardPurchaseBlock, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100)
    expansion = models.CharField(max_length=100)
    tcgplayer_card_id = models.PositiveIntegerField(blank=True, null=True)
    buy_price = models.DecimalField(editable=False, decimal_places=2, max_digits=6)
    lowest_listing_at_buy = models.DecimalField(editable=False, decimal_places=2, max_digits=6)
    market_price_at_buy = models.DecimalField(decimal_places=2, max_digits=6)
    initial_sell_price = models.DecimalField(decimal_places=2, max_digits=6)
    sold_on = models.DateTimeField(blank=True, null=True)
    sell_price = models.DecimalField(decimal_places=2, blank=True, null=True, max_digits=6)
    market_price_at_sell = models.DecimalField(decimal_places=2, blank=True, null=True, max_digits=6)
    lowest_listing_at_sell = models.DecimalField(decimal_places=2, blank=True, null=True, max_digits=6)

class SpecialCard(models.Model):
    name = models.CharField(max_length=100)
    percent_modifier = models.DecimalField(decimal_places=1, max_digits=4)
    list_for_sale = models.BooleanField(default=True)
