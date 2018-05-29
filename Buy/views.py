from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from Buy.models import *
import json
import datetime
import requests
import os
from dateutil.parser import parse
from django.forms.models import model_to_dict
import re

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
    standard_list = []
    for standard_set in StandardSet.objects.all():
        standard_list.append({'name':standard_set.name, 'abbreviation':standard_set.abbreviation})
    return render(request, 'buy.html', {'bearer':bearer_token.bearer, 'standard_list':standard_list})

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
    print(request.POST)
    if 'seller_id' in request.POST.keys():
        seller = Seller.objects.get(pk=request.POST['seller_id'])
    else:
        seller = Seller(
            name = request.POST['seller_name'],
            email = request.POST['seller_email'],
            phone = request.POST['seller_phone']
        )
        seller.save()
    if 'seller_notes' in request.POST.keys() and request.POST['seller_notes'] != "":
        seller.notes = request.POST['seller_notes']
        seller.save()
    block = CardPurchaseBlock(seller=seller, payment_method=request.POST['paymentmethod'])
    block.save()
    index = 0
    errors = ""
    total_buy = 0
    bearer = "bearer " + update_bearer().bearer
    #Regex parse each key named 'card_name_/d', use those indices, catch specific errors

    for key in request.POST.keys():
        match = re.match(r'card_name_(\d+)', key)
        if match:
            index = match.group(1)
            if (request.POST['card_name_'+str(index)] != "") and (int(request.POST['quantity_'+str(index)]) > 0):
                for i in range(0, int(request.POST['quantity_'+str(index)])):
                    single = SingleCardPurchase(
                        block = block,
                        name = request.POST['card_name_'+str(index)],
                        expansion = request.POST['expansion_'+str(index)],
                        tcgplayer_card_id = request.POST['tcgplayer_card_id_'+str(index)],
                        buy_price = float(request.POST['price_'+str(index)]),
                        initial_sell_price = float(request.POST['sell_price_'+str(index)]),
                        lowest_listing_at_buy = float(request.POST['lowest_listing_at_buy_'+str(index)]),
                        lowest_direct_at_buy = float(request.POST['lowest_direct_at_buy_'+str(index)]),
                        market_price_at_buy = float(request.POST['market_price_'+str(index)])
                    )
                    single.save()
                    total_buy += float(request.POST['price_'+str(index)])
                if ('auto_list_'+str(index) in request.POST.keys() and request.POST['auto_list_'+str(index)] == "on"):
                    old_quantity = 0
                    r = requests.get("http://api.tcgplayer.com/stores/"+os.environ['store_key']+"/inventory/skus/"+single.tcgplayer_card_id+"/quantity", headers={'Authorization':bearer})
                    if (r.status_code == 200 and r.json()['success']):
                        old_quantity = int(r.json()['results'][0]['quantity'])
                    quantity = old_quantity + int(request.POST['quantity_'+str(index)])
                    r = requests.put("http://api.tcgplayer.com/stores/"+os.environ['store_key']+"/inventory/skus/"+single.tcgplayer_card_id, headers={'Authorization':bearer, 'Content-Type':'application/json'}, json={'price':single.initial_sell_price, 'quantity':quantity, 'channelId':0})
                    if (r.status_code != 200):
                        errors += single.name + " price/quantity not updated<br>"
                    else:
                        if single.initial_sell_price > 1:
                            errors += single.name + " to case<br>"
                        else:
                            errors += single.name + " to box<br>"
                else:
                    errors += single.name + " not auto-listed<br>"

    if request.POST['paymentmethod'] == 'Store Credit':
        errors += "<br>Give " + seller.name + " $" + total_buy + " Store Credit"
    else:
        errors += "<br>Give " + seller.name + " $" + total_buy + " Cash"

    return HttpResponse(errors)
    return render(request, 'post.html', {'message':errors})
