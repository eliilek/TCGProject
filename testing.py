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

bearer = "bearer " + update_bearer().bearer
store_key = os.environ['store_key']

remaining_cards = SingleCardPurchase.objects.filter(sold_on=None).order_by("tcgplayer_card_id", "block__bought_on")
previous_id = ""
checked_remaining = {}
batch = []
testing_index = 1
for card in remaining_cards:
    if card.tcgplayer_card_id != previous_id:
        checked_remaining[card.tcgplayer_card_id] = [card,]
        print(testing_index)
        testing_index = 1
    else:
        checked_remaining[card.tcgplayer_card_id].append(card)
        testing_index = testing_index + 1
print(testing_index)

#Checked remaining are in order from oldest to newest within each ID
new_block = CardPurchaseBlock(seller=Seller.objects.get(name="Eli Klein"))
new_block.save()
for tcgplayer_id in checked_remaining:
    value = price_check(checked_remaining[tcgplayer_id][0])
    if "error" in value:
    #    print(value['error'])
        continue
    r = requests.get("http://api.tcgplayer.com/stores/"+os.environ['store_key']+"/inventory/skus/"+str(tcgplayer_id)+"/quantity", headers={'Authorization':bearer})
    if (r.status_code == 200 and r.json()['success']):
        print(tcgplayer_id)
        difference = r.json()['results'][0]['quantity'] - len(checked_remaining[tcgplayer_id])
        print(checked_remaining[tcgplayer_id][0].name + " " + str(difference))
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
                print(new_record.tcgplayer_card_id)
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
