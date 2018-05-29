from Buy.models import *
import requests
import datetime
from Buy.views import update_bearer
import os
from dateutil.parser import parse

if SalesCheckDateTime.objects.count() == 0:
    dateTime = SalesCheckDateTime(last_check=datetime.datetime.now() - datetime.timedelta(days=1), last_sale_id="")
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
            spec = requests.get("http://api.tcgplayer.com/stores/" + store_key + "/orders/" + r.json()['results'][order_id])
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
            for i in range(r.json()['results'][item]['quantity']):
                cards = SingleCardPurchase.objects.filter(tcgplayer_card_id=sku, sold_on=None)
                if len(cards) > 0:
                    card_sold = cards.earliest('block__bought_on')
                    card_sold['sold_on'] = datetime.datetime.now()
                    card_sold['sell_price'] = r.json()['results'][item]['price']
                    #This is not very efficient doing for each quantity, fix?
                    pricing = requests.get("http://api.tcgplayer.com/pricing/sku/" + sku, headers={"Authorization":bearer})
                    if pricing.json()['success']:
                        card_sold['market_price_at_sell'] = pricing.json()['results'][0]['marketPrice']
                        if pricing.json()['results'][0]['directLowPrice']:
                            card_sold['lowest_listing_at_sell'] = pricing.json()['results'][0]['directLowPrice']
                        else:
                            card_sold['lowest_listing_at_sell'] = pricing.json()['results'][0]['lowestListingPrice']

#Check if items have been listed too long, depreciate
