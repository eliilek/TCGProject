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
from math import ceil
from django.utils import timezone
import csv

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
    return render(request, 'sell.html', {'bearer':bearer_token.bearer, 'store_key':os.environ['store_key']})

def trade(request):
    return HttpResponse("Oops! This isn't implemented yet.")

def seller_info(request):
    if request.method != "GET":
        return redirect("/")
    name = request.GET["name"]
    try:
        seller = Seller.objects.get(name=name)
        return JsonResponse({'found':True, 'email':seller.email, 'phone':seller.phone, 'notes':seller.notes, 'id':seller.id})
    except:
        return JsonResponse({'found':False})

def query_price(request):
    if request.method != "GET":
        return redirect("/")
    card = {'name':request.GET['name'], 'tcgplayer_NM_id':request.GET['NM_id'], 'tcgplayer_LP_id':request.GET['LP_id'], 'tcgplayer_card_id':request.GET['card_id']}
    results = price_check(card)
    results['context'] = request.GET['context']
    return JsonResponse(results)

def report_buy(request):
    if request.method != "POST":
        return redirect("/")
    print(request.POST)
    try:
        if 'seller_id' in request.POST.keys():
            seller = Seller.objects.get(pk=request.POST['seller_id'])
        else:
            name_search = Seller.objects.filter(name=request.POST['seller_name'])
            if len(name_search) == 1:
                seller = name_search[0]
            else:
                seller = Seller(
                    name = request.POST['seller_name'],
                    email = request.POST['seller_email'],
                    phone = request.POST['seller_phone']
                )
                seller.save()
        if 'seller_notes' in request.POST.keys() and request.POST['seller_notes'] != "":
            seller.notes = request.POST['seller_notes']
        if 'seller_email' in request.POST.keys() and request.POST['seller_email'] != "":
            seller.email = request.POST['seller_email']
        if 'seller_phone' in request.POST.keys() and request.POST['seller_phone'] != "":
            seller.phone = request.POST['seller_phone']
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
                    try:
                        for i in range(0, int(request.POST['quantity_'+str(index)])):
                            single = SingleCardPurchase(
                                block = block,
                                name = request.POST['card_name_'+str(index)],
                                expansion = request.POST['expansion_'+str(index)],
                                tcgplayer_card_id = request.POST['tcgplayer_card_id_'+str(index)],
                                tcgplayer_NM_id = request.POST['tcgplayer_nm_id_'+str(index)],
                                tcgplayer_LP_id = request.POST['tcgplayer_lp_id_'+str(index)],
                                buy_price = float(request.POST['price_'+str(index)]),
                                initial_sell_price = float(request.POST['sell_price_'+str(index)]),
                                base_price = float(request.POST['sell_price_'+str(index)]),
                                lowest_listing_at_buy = float(request.POST['lowest_listing_at_buy_'+str(index)]),
                                lowest_direct_at_buy = float(request.POST['lowest_direct_at_buy_'+str(index)]),
                                market_price_at_buy = float(request.POST['market_price_'+str(index)])
                            )
                            single.save()
                            total_buy += float(request.POST['price_'+str(index)])
                    except:
                        errors += single.name + " not auto-listed<br>"
                        continue
                    if ('auto_list_'+str(index) in request.POST.keys() and request.POST['auto_list_'+str(index)] == "on"):
                        old_quantity = 0
                        r = requests.get("http://api.tcgplayer.com/v1.10.0/stores/"+os.environ['store_key']+"/inventory/skus/"+single.tcgplayer_card_id+"/quantity", headers={'Authorization':bearer})
                        if (r.status_code == 200 and r.json()['success']):
                            old_quantity = int(r.json()['results'][0]['quantity'])
                        quantity = old_quantity + int(request.POST['quantity_'+str(index)])
                        r = requests.put("http://api.tcgplayer.com/v1.10.0/stores/"+os.environ['store_key']+"/inventory/skus/"+single.tcgplayer_card_id, headers={'Authorization':bearer, 'Content-Type':'application/json'}, json={'price':(single.initial_sell_price * 1.1 if single.initial_sell_price * 1.1 <= single.initial_sell_price + 5 else single.initial_sell_price + 5), 'quantity':quantity, 'channelId':0})
                        if (r.status_code != 200):
                            errors += single.name + " price/quantity not updated<br>"
                        else:
                            if single.initial_sell_price > 1:
                                errors += single.name + " to case<br>"
                            else:
                                errors += single.name + " to box<br>"
                    else:
                        errors += single.name + " not auto-listed<br>"
    except Exception as e:
        print(e)

    if request.POST['paymentmethod'] == 'Store Credit':
        errors += "<br>Give " + seller.name + " $" + str(total_buy) + " Store Credit"
    else:
        errors += "<br>Give " + seller.name + " $" + str(total_buy) + " Cash"

    return render(request, 'post.html', {'message':errors})

def report_sell(request):
    if request.method != "POST":
        return redirect("/")
    print(request.POST)
    if 'buyer_id' in request.POST.keys():
        buyer = Seller.objects.get(pk=request.POST['buyer_id'])
    else:
        buyer = Seller(
            name = request.POST['buyer_name'],
            email = request.POST['buyer_email'],
            phone = request.POST['buyer_phone']
        )
        buyer.save()
    if 'buyer_notes' in request.POST.keys() and request.POST['buyer_notes'] != "":
        buyer.notes = request.POST['buyer_notes']
    if 'buyer_email' in request.POST.keys() and request.POST['buyer_email'] != "":
        buyer.email = request.POST['buyer_email']
    if 'buyer_phone' in request.POST.keys() and request.POST['buyer_phone'] != "":
        buyer.phone = request.POST['buyer_phone']
    buyer.save()

    bearer = "bearer " + update_bearer().bearer

    errors = ""
    total_price = 0
    for key in request.POST.keys():
        match = re.match(r'card_name_(\d+)', key)
        if match:
            index = match.group(1)
            if (request.POST['card_name_'+str(index)] != "") and (int(request.POST['quantity_'+str(index)]) > 0):
                r = requests.get("http://api.tcgplayer.com/v1.10.0/stores/"+os.environ['store_key']+"/inventory/skus/"+request.POST['tcgplayer_card_id_'+str(index)]+"/quantity", headers={"Authorization":bearer})
                try:
                    print(r.json())
                    inStock = r.json()['results'][0]['quantity']
                    foil_cond_name = request.POST['condition_'+str(index)] + " " + request.POST['card_name_'+str(index)]
                    if inStock < int(request.POST['quantity_'+str(index)]):
                        new_quantity = 0
                        errors += "Only have " + inStock + " " + foil_cond_name + " from " + request.POST['expansion_'+str(index)] + " available to sell<br>"
                        total_price += inStock * float(request.POST['price_'+str(index)])
                    else:
                        new_quantity = inStock - int(request.POST['quantity_'+str(index)])
                        errors += "Sold " + request.POST['quantity_'+str(index)] + " " + foil_cond_name + " from " + request.POST['expansion_'+str(index)] + "<br>"
                        total_price += int(request.POST['quantity_'+str(index)]) * float(request.POST['price_'+str(index)])
                    update = requests.post("http://api.tcgplayer.com/v1.10.0/stores/" + os.environ['store_key'] + "/inventory/skus/" + request.POST['tcgplayer_card_id_'+str(index)] + "/quantity", headers={"Authorization":bearer}, json={"quantity":new_quantity - inStock})
                    #update = requests.put("http://api.tcgplayer.com/v1.10.0/stores/" + os.environ['store_key'] +"/inventory/skus/" + request.POST['tcgplayer_card_id_'+str(index)], headers={"Authorization":bearer, 'Content-Type':'application/json'}, json={'quantity':new_quantity, 'price':float(request.POST['price_'+str(index)]), 'channelId':0})
                    singles = SingleCardPurchase.objects.filter(tcgplayer_card_id=int(request.POST['tcgplayer_card_id_'+str(index)]), sold_on=None)
                    spec = requests.get("http://api.tcgplayer.com/v1.10.0/pricing/sku/" + request.POST['tcgplayer_card_id_'+str(index)], headers={"Authorization":bearer})
                    for i in range(min(inStock, int(request.POST['quantity_'+str(index)]))):
                        if len(singles) > i:
                            singles[i].sold_on = timezone.now()
                            singles[i].sell_price = float(request.POST['price_'+str(index)])
                            if spec.json()['success']:
                                if spec.json()['results'][0]['marketPrice'] != None:
                                    singles[i].market_price_at_sell = spec.json()['results'][0]['marketPrice']
                                else:
                                    singles[i].market_price_at_sell = 0
                                if spec.json()['results'][0]['directLowPrice'] != None:
                                    singles[i].lowest_direct_at_sell = spec.json()['results'][0]['directLowPrice']
                                else:
                                    singles[i].lowest_direct_at_sell = 0
                                if spec.json()['results'][0]['lowestListingPrice'] != None:
                                    singles[i].lowest_listing_at_sell = spec.json()['results'][0]['lowestListingPrice']
                                else:
                                    singles[i].lowest_listing_at_sell = 0
                            singles[i].in_house_sale = True
                            singles[i].save()
                        else:
                            sale = UntrackedCardSale(   name = request.POST['card_name_'+str(index)],
                                                        expansion = request.POST['expansion_'+str(index)],
                                                        tcgplayer_card_id = int(request.POST['tcgplayer_card_id_'+str(index)]),
                                                        sold_on = timezone.now(),
                                                        sell_price = float(request.POST['price_'+str(index)]),
                                                        in_house_sale = True)
                            if spec.json()['success']:
                                if spec.json()['results'][0]['marketPrice'] != None:
                                    sale.market_price_at_sell = spec.json()['results'][0]['marketPrice']
                                else:
                                    sale.market_price_at_sell = 0
                                if spec.json()['results'][0]['directLowPrice'] != None:
                                    sale.lowest_direct_at_sell = spec.json()['results'][0]['directLowPrice']
                                else:
                                    sale.lowest_direct_at_sell = 0
                                if spec.json()['results'][0]['lowestListingPrice'] != None:
                                    sale.lowest_listing_at_sell = spec.json()['results'][0]['lowestListingPrice']
                                else:
                                    sale.lowest_listing_at_sell = 0
                            sale.save()
                except Exception as e:
                    errors += request.POST['card_name_'+str(index)] + " not sold<br>"
                    print(e)

    errors += "<br>Ring up " + str(total_price) + " in Crystal Commerce (under Roboklein Magic Singles)"

    return render(request, 'post.html', {'message':errors})

def download_results(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_' + str(timezone.now()) + '_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Expansion', 'Bought On', 'Buy Price', 'Lowest Listing (buy)', 'Lowest Direct (buy)', 'Market (buy)', 'Initial Sell Price', 'Sold On', 'Final Sell Price', 'Market (sell)', 'Lowest Listing (sell)', 'Lowest Direct (sell)', 'In House'])

    for card in SingleCardPurchase.objects.all():
        writer.writerow([card.name, card.expansion, card.block.bought_on, card.buy_price, card.lowest_listing_at_buy, card.lowest_direct_at_buy, card.market_price_at_buy, card.initial_sell_price, card.sold_on, card.sell_price, card.market_price_at_sell, card.lowest_listing_at_sell, card.lowest_direct_at_sell, card.in_house_sale])

    return response

def price_check(card):
    context = ""
    try:
        card = model_to_dict(card)
    except:
        pass

    bearer = "bearer " + update_bearer().bearer

    if card['tcgplayer_NM_id'] and card['tcgplayer_LP_id']:
        r = requests.get("http://api.tcgplayer.com/v1.10.0/pricing/sku/" + str(card['tcgplayer_NM_id']) + "," + str(card['tcgplayer_LP_id']), headers={"Authorization":bearer})
        if r.json()['success']:
            standard = False
            standard_list = [thing.name for thing in StandardSet.objects.all()]
            card_details = requests.get("http://api.tcgplayer.com/v1.10.0/catalog/products", headers={"Authorization":bearer}, data={'categoryId':1, 'productName':card['name'], 'limit':50})
            if card_details.json()['success']:
                group_id_string = ""
                for data in card_details.json()['results']:
                    group_id_string = group_id_string + "," + str(data['groupId'])
                card_standard = requests.get("http://api.tcgplayer.com/v1.10.0/catalog/groups/" + group_id_string, headers={"Authorization":bearer})
                if card_standard.json()['success']:
                    for group in card_standard.json()['results']:
                        if group['name'] in standard_list:
                            standard = True

            premium = 1
            market = 0
            direct_low = 0
            low = 0
            #TODO make the algorithm happen
            if r.json()['results'][0]['directLowPrice'] and r.json()['results'][1]['directLowPrice']:
                if standard:
                    direct_low = (r.json()['results'][0]['directLowPrice'] + r.json()['results'][1]['directLowPrice'])/2
                    if r.json()['results'][0]['marketPrice'] and r.json()['results'][1]['marketPrice']:
                        market = (r.json()['results'][0]['marketPrice'] + r.json()['results'][1]['marketPrice'])/2
                    elif r.json()['results'][0]['marketPrice']:
                        market = r.json()['results'][0]['marketPrice']
                    else:
                        market = r.json()['results'][1]['marketPrice']
                elif r.json()['results'][0]['directLowPrice'] < r.json()['results'][1]['directLowPrice']:
                    direct_low = r.json()['results'][0]['directLowPrice']
                    market = r.json()['results'][0]['marketPrice']
                else:
                    direct_low = r.json()['results'][1]['directLowPrice']
                    market = r.json()['results'][1]['marketPrice']
            elif r.json()['results'][1]['directLowPrice']:
                direct_low = r.json()['results'][1]['directLowPrice']
                market = r.json()['results'][1]['marketPrice']
            elif r.json()['results'][0]['directLowPrice']:
                direct_low = r.json()['results'][0]['directLowPrice']
                market = r.json()['results'][0]['marketPrice']

            if r.json()['results'][0]['lowestListingPrice'] and r.json()['results'][1]['lowestListingPrice']:
                if standard:
                    low = (r.json()['results'][0]['lowestListingPrice'] + r.json()['results'][1]['lowestListingPrice'])/2
                    if r.json()['results'][0]['marketPrice'] and r.json()['results'][1]['marketPrice']:
                        market = (r.json()['results'][0]['marketPrice'] + r.json()['results'][1]['marketPrice'])/2
                    elif r.json()['results'][0]['marketPrice']:
                        market = r.json()['results'][0]['marketPrice']
                    else:
                        market = r.json()['results'][1]['marketPrice']
                elif r.json()['results'][0]['lowestListingPrice'] < r.json()['results'][1]['lowestListingPrice']:
                    low = r.json()['results'][0]['lowestListingPrice']
                    market = r.json()['results'][0]['marketPrice']
                else:
                    low = r.json()['results'][1]['lowestListingPrice']
                    market = r.json()['results'][1]['marketPrice']
            elif r.json()['results'][0]['lowestListingPrice']:
                low = r.json()['results'][0]['lowestListingPrice']
                market = r.json()['results'][0]['marketPrice']
            elif r.json()['results'][1]['lowestListingPrice']:
                low = r.json()['results'][1]['lowestListingPrice']
                market = r.json()['results'][1]['marketPrice']

            if direct_low == 0 and low == 0:
                return {"error":"Cannot Price "+card['name']}

            if direct_low == None:
                direct_low = 0
            if low == None:
                low = 0
            min_base = max(direct_low, low)
            if abs(direct_low-low)>=5 and direct_low != 0 and low != 0:
                premium = premium - 0.05

            if not standard:
                premium = premium + 0.07

            card_cond = requests.get("http://api.tcgplayer.com/v1.10.0/catalog/skus/" + str(card['tcgplayer_card_id']), headers={"Authorization":bearer})
            if card_cond.json()['success']:
                if card_cond.json()['results'][0]['conditionId'] == 1:
                    min_base = min_base * 1.05
                if card_cond.json()['results'][0]['conditionId'] == 3:
                    min_base = min_base * 0.95
                elif card_cond.json()['results'][0]['conditionId'] == 4:
                    min_base = min_base * 0.75
                elif card_cond.json()['results'][0]['conditionId'] == 5:
                    min_base = min_base * 0.55

                if card_cond.json()['results'][0]['variantId'] == 2:
                    premium = premium - 0.07

            final_price = ceil(min_base * premium * 100)/100.0
            if final_price > min_base + 5:
                final_price = min_base + 5
            elif final_price < min_base - 5:
                final_price = min_base - 5

            return {"price":final_price}
        else:
            return {"error":"Could not connect to pricing data"}
    return {"error":"Insufficient Data"}
