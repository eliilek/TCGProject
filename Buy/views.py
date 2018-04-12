from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from Buy.models import *
import json
import datetime
import requests
import os
from dateutil.parser import parse

def update_bearer():
    if Token.objects.all().exists():
        if Token.objects.latest('expires').expires.date() > datetime.datetime.today().date():
            return Token.objects.latest('expires')
    r = requests.get('https://api.tcgplayer.com/token', headers={'Content-Type':'application/x-www-form-urlencoded', 'X-Tcg-Access-Token':os.environ['access_token']}, data={'grant_type':'client_credentials', 'client_id':os.environ['public_key'], 'client_secret':os.environ['private_key']})
    response_dict = r.json()
    print(response_dict)
    token = Token(bearer=response_dict['access_token'], expires=parse(response_dict['.expires']))
    token.save()
    return token

# Create your views here.
def index(request):
    return render(request, 'index.html')

def buy(request):
    #Ensure TCGPlayer bearer token is valid
    bearer_token = update_bearer()
    return render(request, 'buy.html', {'bearer':bearer_token.bearer})

def sell(request):
    #Ensure TCGPlayer bearer token is valid
    bearer_token = update_bearer()
    return render(request, 'sell.html', {'bearer':bearer_token.bearer})

def seller_info(request):
    if request.method != "GET":
        return redirect("/")
    name = request.GET["name"]
    try:
        seller = Seller.objects.get(name=name)
        return JsonResponse({'found':True, 'email':seller.email, 'phone':seller.phone, 'notes':seller.notes, 'id':seller.id})
    except:
        return JsonResponse({'found':False})

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
        #Query API via requests, add card to inventory at price
    return HttpResponse("You shouldn't see this")
