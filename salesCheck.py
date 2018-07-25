import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TCGProject.settings")
django.setup()

from Buy.models import *
import requests
import datetime
from Buy.views import update_bearer, price_check
from dateutil.parser import parse
from django.utils import timezone

if SalesCheckDateTime.objects.count() == 0:
    dateTime = SalesCheckDateTime(last_check=timezone.now() - datetime.timedelta(days=1), last_sale_id="")
    dateTime.save()
else:
    dateTime = SalesCheckDateTime.objects.latest('last_check')

bearer = "bearer " + update_bearer().bearer
store_key = os.environ['store_key']

r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, params={"sort":"OrderDate Desc"})
#Keep pulling orders until we find one too early
last_id = None
if (r.json()['success'] and dateTime.last_sale_id == ""):
    another=True
    orders=[]
    offset=10
    last_id = r.json()['results'][0]
    while (another):
        print(r.text)
        for order_id in r.json()['results']:
            spec = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders/" + order_id, headers={"Authorization":bearer})
            print(spec.text)
            if (spec.json()['success'] and parse(spec.json()['results'][0]['orderedOn'], default=timezone.now()) >= dateTime.last_check):
                orders.append(spec.json()['results'][0]['orderNumber'])
            else:
                another=False
                break
        if another:
            r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, params={"sort":"OrderDate Desc", "offset":offset})
            offset += 10
            if not r.json()['success']:
                another=False
#Keep pulling orders until we find the last order recorded
elif (r.json()['success']):
    print(dateTime.last_sale_id)
    another=True
    orders=[]
    offset=10
    last_id = r.json()['results'][0]
    while (another):
        for order_id in r.json()['results']:
            print(order_id)
            if (not r.json()['success']) or order_id == dateTime.last_sale_id:
                another=False
                break
            else:
                orders.append(order_id)
        if another:
            r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders", headers={"Authorization":bearer}, params={"sort":"OrderDate Desc", "offset":offset})
            offset += 10
            if not r.json()['success']:
                another=False

#Handle items in orders
for item in orders:
    print(item)
    r = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders/" + item + "/items", headers={"Authorization":bearer})
    print(r.text)
    if (r.json()['success']):
        for item in r.json()['results']:
            #For each quantity, check if we have one of that SKUID in database
            sku = item['skuId']
            pricing = None
            for i in range(item['quantity']):
                cards = SingleCardPurchase.objects.filter(tcgplayer_card_id=sku, sold_on=None)
                print(cards)
                if len(cards) > 0:
                    if pricing == None:
                        pricing = requests.get("http://api.tcgplayer.com/pricing/sku/" + str(sku), headers={"Authorization":bearer})
                    card_sold = cards.earliest('block__bought_on')
                    card_sold.sold_on = timezone.now()
                    card_sold.sell_price = item['price']
                    if pricing.json()['success']:
                        card_sold.market_price_at_sell = pricing.json()['results'][0]['marketPrice']
                        card_sold.lowest_listing_at_sell = pricing.json()['results'][0]['directLowPrice']
                        card_sold.lowest_direct_at_sell = pricing.json()['results'][0]['lowestListingPrice']
                    card_sold.save()

#Check if items have been listed too long, depreciate
remaining_cards = SingleCardPurchase.objects.filter(sold_on=None).order_by("tcgplayer_card_id", "block__bought_on")
previous_id = ""
checked_remaining = {}
batch = []
for card in remaining_cards:
    if card.tcgplayer_card_id != previous_id:
        checked_remaining[card.tcgplayer_card_id] = [card,]
        previous_id = card.tcgplayer_card_id
    else:
        checked_remaining[card.tcgplayer_card_id].append(card)

print(remaining_cards)

#Checked remaining are in order from oldest to newest within each ID
new_block = CardPurchaseBlock(seller=Seller.objects.get(name="Eli Klein"))
new_block.save()
for tcgplayer_id in checked_remaining:
    value = price_check(checked_remaining[tcgplayer_id][0])
    if "error" in value:
        print(value['error'])
        continue
    r = requests.get("http://api.tcgplayer.com/stores/"+os.environ['store_key']+"/inventory/skus/"+str(tcgplayer_id)+"/quantity", headers={'Authorization':bearer})
    if (r.status_code == 200 and r.json()['success']):
        difference = r.json()['results'][0]['quantity'] - len(checked_remaining[tcgplayer_id])
        if difference < 0:
            for i in range(-1 * difference):
                checked_remaining[tcgplayer_id][i].sold_on = timezone.now()
        elif difference > 0:
            for i in range(difference):
                new_record = SingleCardPurchase(block=new_block,
                                                name=checked_remaining[tcgplayer_id][0].name,
                                                expansion=checked_remaining[tcgplayer_id][0].expansion,
                                                tcgplayer_card_id=tcgplayer_id,
                                                tcgplayer_NM_id=checked_remaining[tcgplayer_id][0].tcgplayer_NM_id,
                                                tcgplayer_LP_id=checked_remaining[tcgplayer_id][0].tcgplayer_LP_id,
                                                buy_price=0.0,
                                                lowest_listing_at_buy=0.0,
                                                lowest_direct_at_buy=0.0,
                                                market_price_at_buy=0.0,
                                                initial_sell_price=value['price'])
                new_record.save()
        card = checked_remaining[tcgplayer_id][0]
        card.base_price = value['price']
        card.save()
        delta = timezone.now() - card.block.bought_on
        print(card.name + " " + str(delta.days) + " days $" + str(card.base_price))
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

        batch.append({"skuId":card.tcgplayer_card_id, "price":price, "channelId":0})

requests.post("http://api.tcgplayer.com/stores/" + store_key + "/inventory/skus/batch", headers={"Authorization":bearer}, json=batch)

dateTime.delete()
if last_id:
    nextDT = SalesCheckDateTime(last_check=timezone.now(), last_sale_id=last_id)
else:
    nextDT = SalesCheckDateTime(last_check=timezone.now())
nextDT.save()
