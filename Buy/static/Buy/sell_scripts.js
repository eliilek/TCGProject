var buyer_id;
var index=0;

function check_card_name() {
	if ($(this).val() == ""){
		return -1;
	}
  //clear out non-default expansions, remove change functions from expansion, condition
  $(this).data("expansion").children('option:not(:first)').remove();
  $(this).data("expansion").off('change');
  $(this).data("condition").children('option:not(:first)').remove();
  $(this).data("condition").off('change');
	//Disable critical components - submit button, other inputs in this line
  $("#submitbtn").prop("disabled", true);
  $(this).data("expansion").prop("disabled", true);
  $(this).data("condition").prop("disabled", true);
  $(this).data("trash_button").prop("disabled", true);

	$.ajax({
		"headers":{"Authorization": "bearer " + bearer},
		"url":"http://api.tcgplayer.com/stores/" + store_key + "/inventory/products",
		"data":{'categoryId':1, 'productName':$(this).val(), 'skuLimit':10, 'limit':50},
    "context":this,
		"success":function(data, textStatus, jqXHR){
      console.log(data);
      $("#submitbtn").prop("disabled", false);
      $(this).data("expansion").prop("disabled", false);
      $(this).data("condition").prop("disabled", false);
      $(this).data("trash_button").prop("disabled", false);
      if(data['totalItems'] == 0){
        alert("No cards found - check spelling?");
        return -1;
      }
      var inventory = {};
      var productIdString = "";
      for(var i=0;i<data['results'].length;i++){
        if (data['results'][i]['skuCount'] != 0){
          var product_dict = {'group':data['results'][i]['group'], 'productId':data['results'][i]['productId'], 'skus':[]};
					var char_code = char_code_dict[data['results'][i]['group']];
					console.log(char_code);
					if(char_code == undefined){
						char_code = "";
					} else {
						char_code = char_code['char_code'].replace("\\", "&#x");
					}
          for(var j=0; j<data['results'][i]['skuCount'];j++){
            product_dict['skus'].push({'sku':data['results'][i]['skus'][j]['skuId'],
                                       'price':data['results'][i]['skus'][j]['price'],
                                       'quantity':data['results'][i]['skus'][j]['quantity'],
                                       'condition':data['results'][i]['skus'][j]['condition']['name'],
                                       'foil':data['results'][i]['skus'][j]['foil']
                                     });
            }
          inventory[data['results'][i]['productId']] = product_dict;
					if (data['results'].length == 1){
						new_option = $("<option selected></option>").attr({'value':data['results'][i]['group']}).html(data['results'][i]['group'] + " " + char_code).data("product_id", data['results'][i]['productId']);
					} else {
						new_option = $("<option></option>").attr({'value':data['results'][i]['group']}).html(data['results'][i]['group'] + " " + char_code).data("product_id", data['results'][i]['productId']);
					}
					$(this).data("expansion").append(new_option);
					if (data['results'].length == 1){
						$(this).data("expansion").data("inventory", inventory);
						$(this).data("expansion").change(create_conditions);
						expansion.trigger("change");
					}
        }
			}
			$(this).data("expansion").change(create_conditions);
			console.log(Object.keys(inventory).length);
      if (Object.keys(inventory).length == 0){
        alert("No cards of that name in stock");
        return -1;
      }
			$(this).data("expansion").data("inventory", inventory);
		},
    "error":function(data, textStatus, jqXHR){
      $("#submitbtn").prop("disabled", false);
      $(this).data("expansion").prop("disabled", false);
      $(this).data("condition").prop("disabled", false);
      $(this).data("trash_button").prop("disabled", false);
      alert("Request failed");
    }
	});
	console.log("Requested");
}

function create_conditions(){
  var product = $(this).data("inventory")[$(this).find(":selected").data("product_id")];
	if (product['skus'].length == 1){
		var matches = product['skus'][0]['condition'].match(/\b(\w)/g);
		var short = matches.join('');
		$(this).data("condition").children('option:not(:first)').remove();
		$(this).data("condition").append($("<option selected></option>").val(product['skus'][0]['condition']).html(short).data("sku", product['skus'][0]));
		$(this).data("condition").off('change');
		$(this).data("condition").change(set_price);
		$(this).data("condition").trigger("change");
	} else {
		$(this).data("condition").children('option:not(:first)').remove();
		for (var i=0; i<product['skus'].length; i++){
			var matches = product['skus'][0]['condition'].match(/\b(\w)/g);
			var short = matches.join('');
			$(this).data("condition").append($("<option></option>").val(product['skus'][1]['condition']).html(short).data("sku", product['skus'][i]));
		}
		$(this).data("condition").off('change');
		$(this).data("condition").change(set_price);
	}
  console.log(product);
}

function set_price(){
	var sku = $(this).find(":selected").data("sku");
	$(this).data("price").val(sku['price']);
	if ($(this).data("quantity").val() > sku['quantity']){
		$(this).data("quantity").val(sku['quantity']);
	}
	$(this).data("quantity").attr({'max':sku['quantity']});
	$(this).data("tcgplayer_card_id").val(sku['sku']);
	sumprice();
}

function robodelete(){
	var message = "Remove line?";
	if($(this).data("confirm-name").val() != ""){
		message = "Remove " + $(this).data("confirm-name").val() + "?"
	}
	if(confirm(message)){
		this.parentNode.remove();
    sumprice();
	}
}

function create_line(){
	var form_group = $("<div></div>").attr({'class':'robocontainer form-group', 'id':'robocontainer_'+index.toString()});
	$("#roboform").append(form_group);
	var trash_button = $("<button></button>").attr({'type':'button', 'class':'btn btn-warning trashbtn roboitem', 'id':'trash_button_'+index.toString()}).html("X");
	form_group.append(trash_button);
	var card_name_div = $("<div></div>").attr({'class':'roboitem', 'id':'name_container_'+index.toString()});
	form_group.append(card_name_div);
	var card_name_label = $("<label></label>").attr({'for':'card_name_'+index.toString()}).html("Card Name:");
	var card_name = $("<input></input>").attr({'type':'text', 'placeholder':'Card Name', 'name':'card_name_'+index.toString(), 'id':'card_name_'+index.toString()});
	trash_button.data("confirm-name", card_name);
  card_name.data("trash_button", trash_button);
	trash_button.click(robodelete);
	card_name.change(check_card_name);
	card_name_div.append(card_name_label, card_name);
	var expansion_div = $("<div></div>").attr({'class':'roboitem', 'id':'expansion_container_'+index.toString()});
	form_group.append(expansion_div);
	var expansion_label = $("<label></label>").attr({'for':'expansion_'+index.toString()}).html("Expansion:");
	var expansion = $("<select></select>").attr({'name':'expansion_'+index.toString(), 'id':'expansion_'+index.toString(), 'class':'ss'});
	var expansion_default_option = $("<option></option>").attr({'value':0, 'selected':true}).html("None");
	card_name.data("expansion", expansion);
  expansion.data("name", card_name);
	expansion.append(expansion_default_option);
	expansion_div.append(expansion_label, expansion);
	var quantity_div = $("<div></div>").attr({'class':'roboitem', 'id':'quantity_container_'+index.toString()});
	form_group.append(quantity_div);
	var quantity_label = $("<label></label>").attr({'for':'quantity_'+index.toString()}).html("Quantity:");
	var quantity = $("<input></input>").attr({'class':'roboquantity', 'name':'quantity_'+index.toString(), 'id':'quantity_'+index.toString(), 'type':'number', 'value':0});
	quantity.change(qty_change);
	quantity_div.append(quantity_label, quantity);
	var condition_div = $("<div></div>").attr({'class':'roboitem', 'id':'condition_container_'+index.toString()});
	form_group.append(condition_div);
	var condition_label = $("<label></label>").attr({'for':'condition_'+index.toString()}).html("Condition:");
	var condition = $("<select></select>").attr({'name':'condition_'+index.toString(), 'id':'condition_'+index.toString()});
	condition.append($("<option></option>").val("None").html("None"));
	condition_div.append(condition_label, condition);
  card_name.data("condition", condition);
  condition.data("name", card_name);
	condition.data("quantity", quantity);
	var price_div = $("<div></div>").attr({'class':'roboitem', 'id':'price_div_'+index.toString()});
	form_group.append(price_div);
	var price_label = $("<label></label>").attr({'for':'price_'+index.toString()}).html("Card Price: $");
	var price = $("<input></input>").attr({'class':'buyitem', 'name':'price_'+index.toString(), 'type':'number', 'step':'0.01', 'min':0, 'value':0});
	price.data("quantity", quantity);
	price.change(sumprice);
  expansion.data("price", price);
  condition.data("price", price);
	price_div.append(price_label, price);
  var tcgplayer_card_id = $('<input></input>').attr({'type':'hidden', 'name':'tcgplayer_card_id_'+index.toString(), 'id':'tcgplayer_card_id_'+index.toString()});
  form_group.append(tcgplayer_card_id);
  expansion.data("tcgplayer_card_id", tcgplayer_card_id);
  condition.data("tcgplayer_card_id", tcgplayer_card_id);
  expansion.data("condition", condition);
  condition.data("condition", condition);

	index++;
}

function qty_change(){
	if ($(this).val() > $(this).attr('max')){
		$(this).val($(this).attr('max'));
	} else if ($(this).val() < 0){
		$(this).val(0);
	}
	sumprice();
}

function sumprice() {
	var total = 0;
	$(".buyitem").each(function(){
		price = parseFloat($(this).val());
		quantity = parseFloat($(this).data("quantity").val());
		total += price * quantity;
	});
	var rounded = Math.ceil(total * 100)/100;
	$(".totalsellitem").val(rounded);
}

function process_buyer_response(data){
	if(data['found']){
		$("#buyer_email").val(data['email']);
		$("#buyer_phone").val(data['phone']);
		$("#buyer_notes").val(data['notes']);
		buyer_id = data['id'];
	}
}

function back_check_buyer() {
	check_buyer($(this).val(), process_buyer_response);
}

$(document).ready(function(){
	create_line();
	$("#addbtn").click(create_line);
	$("#buyer_name").change(back_check_buyer);
})
