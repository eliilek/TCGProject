from django.shortcuts import render, redirect
from django.http import HttpResponse
from models import *
import json
import datetime

# Create your views here.
def index(request):
    return render(request, 'buy.html')

def report_buy(request):
    if request.method != "POST":
        return redirect("/")
    json_object = json.loads(request.body)
    if 'seller_id' in json_object.keys():
        seller = Seller.objects.get(pk=json_object['seller_id'])
    else:
        seller = Seller(
            name = json_object['seller_name'],
            email = json_object['seller_email'],
            phone = json_object['seller_phone']
        )
        seller.save()
    if 'notes' in json_object.keys():
        seller.notes += json_object['notes']
    block = CardPurchaseBlock(seller=seller)
    block.save()
    for card in json_object:
        single = SingleCardPurchase(
            block = block,
            name = json_object[card]['name'],
            expansion = json_object[card]['expansion'],
            tcgplayer_card_id = json_object[card]['card_id'],
            buy_price = json_object[card]['buy_price'],
            lowest_listing_at_buy = json_object[card]['lowest_listing'],
            market_price_at_buy = json_object[card]['market_price']
        )
        single.save()
    return HttpResponse("You shouldn't see this")
