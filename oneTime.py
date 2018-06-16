import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TCGProject.settings")
django.setup()

from Buy.models import *
import requests
import datetime
from Buy.views import update_bearer
from dateutil.parser import parse

bearer = "bearer " + update_bearer().bearer
store_key = os.environ['store_key']

cards = SingleCardPurchase.objects.filter(tcgplayer_card_id=None)
for card in cards:
    card.sold_on = datetime.datetime.now()
    card.save()

cards = SingleCardPurchase.objects.exclude(tcgplayer_card_id=None).filter(sold_on=None).order_by("tcgplayer_card_id")
current_sku = None
quantity = 0
for card in cards:
    if card.tcgplayer_card_id != current_sku:
        current_sku = card.tcgplayer_card_id
        response = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/inventory/skus/" + str(card.tcgplayer_card_id) + "/quantity", headers={"Authorization":bearer})
        if response.json()['success']:
            quantity = response.json()['results'][0]['quantity']
        else:
            quantity = 0
    if quantity > 0:
        quantity = quantity - 1
    else:
        card.sold_on = datetime.datetime.now()
        card.save()
