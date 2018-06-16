import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TCGProject.settings")
django.setup()

from Buy.models import *
import requests
import datetime
from Buy.views import update_bearer, price_check
from dateutil.parser import parse

if SalesCheckDateTime.objects.count() == 0:
    dateTime = SalesCheckDateTime(last_check=datetime.datetime.now() - datetime.timedelta(days=1), last_sale_id="")
    dateTime.save()
else:
    dateTime = SalesCheckDateTime.objects.latest('last_check')

bearer = "bearer " + update_bearer().bearer
store_key = os.environ['store_key']

r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, data={"sort":"OrderDate Desc"})
#Keep pulling orders until we find one too early
if (r.json()['success'] and dateTime.last_sale_id == ""):
    another=True
    orders=[]
    offset=10
    while (another):
        for order_id in r.json()['results']:
            spec = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders/" + order_id, headers={"Authorization":bearer})
            if (spec.json()['success'] and parse(spec.json()['results'][0]['orderedOn']) >= dateTime.last_check):
                orders.append(spec.json()['results'][0]['orderNumber'])
            else:
                another=False
                break
        if another:
            r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, data={"sort":"OrderDate Desc", "offset":offset})
            offset += 10
            if not r.json()['success']:
                another=False
#Keep pulling orders until we find the last order recorded
elif (r.json()['success']):
    another=True
    orders=[]
    offset=10
    while (another):
        for order_id in r.json()['results']:
            if (r.json()['results'][order_id] == dateTime.last_sale_id):
                another=False
                break
            else:
                orders.append(spec.json()['results'][0]['orderNumber'])
        if another:
            r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, data={"sort":"OrderDate Desc", "offset":offset})
            offset += 10
            if not r.json()['success']:
                another=False

#Handle items in orders
for item in orders:
    r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders/" + orders[item] + "/items", headers={"Authorization":bearer})
    if (r.json()['success']):
        for item in r.json()['results']:
            #For each quantity, check if we have one of that SKUID in database
            sku = r.json()['results'][item]['skuId']
            pricing = None
            for i in range(r.json()['results'][item]['quantity']):
                cards = SingleCardPurchase.objects.filter(tcgplayer_card_id=sku, sold_on=None)
                if len(cards) > 0:
                    if pricing == None:
                        pricing = requests.get("http://api.tcgplayer.com/pricing/sku/" + sku, headers={"Authorization":bearer})
                    card_sold = cards.earliest('block__bought_on')
                    card_sold['sold_on'] = datetime.datetime.now()
                    card_sold['sell_price'] = r.json()['results'][item]['price']
                    if pricing.json()['success']:
                        card_sold['market_price_at_sell'] = pricing.json()['results'][0]['marketPrice']
                        card_sold['lowest_listing_at_sell'] = pricing.json()['results'][0]['directLowPrice']
                        card_sold['lowest_direct_at_sell'] = pricing.json()['results'][0]['lowestListingPrice']
                    card_sold.save()

#Check if items have been listed too long, depreciate
remaining_cards = SingleCardPurchase.objects.filter(sold_on=None).order_by("block__bought_on", "tcgplayer_card_id")
previous_id = ""
batch = {}
for card in remaining_cards:
    if card.tcgplayer_card_id != previous_id:
        previous_id = card.tcgplayer_card_id
        value = price_check(card)
        if "error" in value:
            print(value['error'])
            continue
        card.base_price = value['price']
        card.save()

        delta = datetime.datetime.today - card.bought_on
        if delta.days <= 8:
            price = card.base_price * (1.1 - (delta.days * 0.0125))
        elif delta.days <= 15:
            price = card.base_price
        elif delta.days <= 30:
            price = card.base_price * (1 - ((delta.days - 15) * .0166))
        else:
            price = card.base_price * 0.75
        if price > card.base_price + 5:
            price = card.base_price + 5
        elif price < card.base_price - 5:
            price = card.base_price - 5

        if price < 0.2:
            price = 0.2

        batch[card.tcgplayer_card_id] = price

#TODO send the batch prices to api