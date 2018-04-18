var seller_id;
var index = 0;
var group_id_table = {};

//Disable enter key from submitting form when entering text
$(document).on('keyup keypress', 'form input[type="text"]', function(e) {
  if(e.which == 13) {
    e.preventDefault();
    return false;
  }
});

//Disable enter key from submitting form when entering numbers
$(document).on('keyup keypress', 'form input[type="number"]', function(e) {
  if(e.which == 13) {
    e.preventDefault();
    return false;
  }
});

// Delete the X buttons parent element - and confirm - These nodes are the current Node path from the X delete button object
function robodelete(){
	var message = "Remove line?";
	if($(this).data("confirm-name").val() != ""){
		message = "Remove " + $(this).data("confirm-name").val() + "?"
	}
	if(confirm(message)){
		this.parentNode.remove();
    sumbuyprice();
	}
}

function sumbuyprice() {
  console.log("Sum");
	var total = 0;
	$(".buyitem").each(function(){
		price = parseFloat($(this).val());
		quantity = parseFloat($(this).data("quantity").val());
		total += price * quantity;
	});
	var rounded = Math.ceil(total * 100)/100;
	$(".totalbuyitem").val(rounded);
}

function back_check_seller() {
	check_seller($(this).val(), process_seller_response);
}

function check_card_name() {
	if ($(this).val() == ""){
		return -1;
	}
  //clear out non-default expansions, remove change functions from expansion, condition, foil
  $(this).data("expansion").children('option:not(:first)').remove();
  $(this).data("expansion").off('change');
  $(this).data("condition").off('change');
  $(this).data("foil").off('change');
	//Disable critical components - submit button, other inputs in this line
  $("#submitbtn").prop("disabled", true);
  $(this).data("expansion").prop("disabled", true);
  $(this).data("condition").prop("disabled", true);
  $(this).data("foil").prop("disabled", true);
  $(this).data("trash_button").prop("disabled", true);

  $(this).data("standard", false);

	$.ajax({
		"headers":{"Authorization": "bearer " + bearer},
		"url":"http://api.tcgplayer.com/catalog/products",
		"data":{'categoryId':1, 'productName':$(this).val(), 'limit':50},
    "context":this,
		"success":function(data, textStatus, jqXHR){
			//Scrape set names, populate dropdown
			if (data['success']){
				var group_id_string = "";
				var group_id_dict = {};
				for(var i=0;i<data['results'].length;i++){
					group_id_string += data['results'][i]['groupId'] + ",";
					group_id_dict[data['results'][i]['groupId']] = data['results'][i]['productConditions'];
				}
				group_id_table[data['results'][0]['productName']] = group_id_dict;
				$.ajax({
					"headers":{"Authorization": "bearer " + bearer},
					"url":"http://api.tcgplayer.com/catalog/groups/" + group_id_string,
          "context":this,
					"success":function(data, textStatus, jqXHR){
						if (data['success']){
              console.log($(this));
							var expansion = $(this).data("expansion");
							for (var i=0;i<data['results'].length;i++){
								new_option = $("<option></option>").attr({'value':data['results'][i]['name']}).html(data['results'][i]['name']).data("group_id", data['results'][i]['groupId']);
                expansion.append(new_option);
                for (var j=0;j<standard_list.length;j++){
                  if (data['results'][i]['name'] == standard_list[j].name){
                    $(this).data('standard', true);
                  }
                }
							}
							//reenable disabled fields
              $("#submitbtn").prop("disabled", false);
              $(this).data("expansion").prop("disabled", false);
              $(this).data("condition").prop("disabled", false);
              $(this).data("foil").prop("disabled", false);
              $(this).data("trash_button").prop("disabled", false);
							//Set change functions on expansion, condition
              expansion.change(price_pull);
              $(this).data("condition").change(price_pull);
              $(this).data("foil").change(price_pull);
						} else {
              //reenable disabled fields
              $("#submitbtn").prop("disabled", false);
              $(this).data("expansion").prop("disabled", false);
              $(this).data("condition").prop("disabled", false);
              $(this).data("foil").prop("disabled", false);
              $(this).data("trash_button").prop("disabled", false);
              alert("Request failed");
						}
					}
				})
			} else {
        //reenable disabled fields
        $("#submitbtn").prop("disabled", false);
        $(this).data("expansion").prop("disabled", false);
        $(this).data("condition").prop("disabled", false);
        $(this).data("foil").prop("disabled", false);
        $(this).data("trash_button").prop("disabled", false);
        alert("Request failed");
			}
		}
	});
	console.log("Requested");
}

function price_pull(){
  var group_dict = group_id_table[$(this).data('name').val()];
  var sku_dicts = group_dict[$(this).data('name').data('expansion').children(':selected').data('group_id')];
  var foil = $(this).data('name').data('foil').prop('checked');
  var sku_id = $.grep(sku_dicts, function(sku){
    return (sku['name'].includes("Near Mint") || sku['name'].includes("Lightly Played")) && sku['language'] == "English" && sku['isFoil'] == foil;
  });
  if (sku_id.length > 0){
    $.ajax({
      "headers":{"Authorization": "bearer " + bearer},
		  "url":"http://api.tcgplayer.com/pricing/sku/" + sku_id[0]['productConditionId'].toString() + "," + sku_id[1]['productConditionId'].toString(),
      "context":this,
      "success":function(data, textStatus, jqXHR){
        //The Algorithm

        var premium = 1;
        var base = 0;
        var market = 0;
        var avg_count = 0;
        console.log(data);
        if (data['results'][0]['directLowPrice']){
          base += data['results'][0]['directLowPrice'];
          avg_count += 1;
        } else if (data['results'][0]['lowestListingPrice']){
          base += data['results'][0]['lowestListingPrice'];
          avg_count += 1;
        }
        if (data['results'][1]['directLowPrice']){
          base += data['results'][1]['directLowPrice'];
          avg_count += 1;
        } else if (data['results'][1]['lowestListingPrice']){
          base += data['results'][1]['lowestListingPrice'];
          avg_count += 1;
        }
        if (avg_count > 0){
          base = base / avg_count;
          avg_count = 0;
        }
        if (base == 0){
          alert("Cannot auto-price");
          return 0;
        }
        //Check if standard
        if ($(this).data('name').data('standard') == false){
          premium += 0.1;
          console.log("Not Standard");
        }
        if (data['results'][0]['marketPrice']){
          market += data['results'][0]['marketPrice'];
          avg_count += 1;
        }
        if (data['results'][1]['marketPrice']){
          market += data['results'][1]['marketPrice'];
          avg_count += 1;
        }
        if (avg_count > 0){
          market = market / avg_count;
          avg_count = 0;
        }
        //High Velocity
        if (market >= base * 1.1){
          premium += .05;
        //Low Velocity
        } else if (market <= base * 0.9){
          premium -= .05;
        }
        //Foil change
        if (foil){
          premium -= .075;
        }
        //Condition check
        if ($(this).data('condition').val() == "Moderately Played"){
          base = base * 0.9;
        } else if ($(this).data('condition').val() == "Heavily Played"){
          base = base * 0.8;
        } else if ($(this).data('condition').val() == "Damaged"){
          base = base * 0.6;
        }

        //TODO investigate adding 10% to premium if base between $2 and $5, adding more or locking to steps below $2
        //Cut to 40% if base is under $2, 30% if base is under $1, flag as bulk below $0.5
        var final_price = Math.ceil(base * premium * 100)/100;
        var condition = $(this).data("name").data("condition").val();
        var sku_id = $.grep(sku_dicts, function(sku){
          return (sku['name'].includes(condition) && sku['language'] == "English" && sku['isFoil'] == foil;
        });
        if(sku_id.length > 0){
          //Save the pricing info at the time of purchase
          $(this).data("tcgplayer_card_id").val(sku_id[0]['productConditionId']);
          $.ajax({
            "headers":{"Authorization": "bearer " + bearer},
      		  "url":"http://api.tcgplayer.com/pricing/sku/" + sku_id[0]['productConditionId'].toString(),
            "context":this,
            "success":function(data, textStatus, jqXHR){
              if(data['results'][0]['marketPrice'] != null){
                $(this).data("market_price").val(data['results'][0]['marketPrice']);
              } else {
                $(this).data("market_price").val(0);
              }
              if(data['results'][0]['directLowPrice'] != null){
                $(this).data("lowest_direct").val(data['results'][0]['directLowPrice']);
              } else {
                $(this).data("lowest_direct").val(0);
              }
              if(data['results'][0]['lowestListingPrice'] != null){
                $(this).data("lowest_listing").val(data['results'][0]['lowestListingPrice']);
              } else {
                $(this).data("lowest_listing").val(0);
              }
            }
          })
        }

        var final_buy = 0;
        if (final_price < 0.5){
          alert("Bulk - tell customer");
          final_buy = 0;
          if (final_price < 0.25){
            final_price = 0.25;
          }
        } else if (final_price < 1){
          final_buy = final_price * 0.3;
        } else if (final_price < 2){
          final_buy = final_price * 0.4;
        } else {
          final_buy = final_price * 0.5;
        }
        console.log(final_price);
        final_buy = Math.ceil(final_buy * 100)/100;
        $(this).data('price').val(final_buy).trigger("change");
        $(this).data("sell_price").val(final_price);
      },
      "error":function(data, textStatus, jqXHR){
        console.log("Error");
        console.log(data);
      }
    });
  } else {
    alert("No SKUs found - is foil incorrect?");
  }
}

function process_seller_response(data){
	if(data['found']){
    console.log(data);
		$("#seller_email").val(data['email']);
		$("#seller_phone").val(data['phone']);
		$("#seller_notes").val(data['notes']);
		seller_id = data['id'];
	} else {
		alert("Seller not found - Please get phone # and email");
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
	var expansion = $("<select></select>").attr({'name':'expansion_'+index.toString(), 'id':'expansion_'+index.toString()});
	var expansion_default_option = $("<option></option>").attr({'value':0, 'selected':true}).html("None");
	card_name.data("expansion", expansion);
  expansion.data("name", card_name);
	expansion.append(expansion_default_option);
	expansion_div.append(expansion_label, expansion);
	var quantity_div = $("<div></div>").attr({'class':'roboitem', 'id':'quantity_container_'+index.toString()});
	form_group.append(quantity_div);
	var quantity_label = $("<label></label>").attr({'for':'quantity_'+index.toString()}).html("Quantity:");
	var quantity = $("<input></input>").attr({'name':'quantity_'+index.toString(), 'id':'quantity_'+index.toString(), 'type':'number', 'value':0});
	quantity.change(sumbuyprice);
	quantity_div.append(quantity_label, quantity);
	var condition_div = $("<div></div>").attr({'class':'roboitem', 'id':'condition_container_'+index.toString()});
	form_group.append(condition_div);
	var condition_label = $("<label></label>").attr({'for':'condition_'+index.toString()}).html("Condition:");
	var condition = $("<select></select>").attr({'name':'condition_'+index.toString(), 'id':'condition_'+index.toString()});
	condition.append($("<option></option>").val("Near Mint").html("NM"));
	condition.append($("<option></option>").val("Lightly Played").html("LP"));
	condition.append($("<option></option>").val("Moderately Played").html("MP"));
	condition.append($("<option></option>").val("Heavily Played").html("HP"));
	condition.append($("<option></option>").val("Damaged").html("DAM"));
	condition_div.append(condition_label, condition);
  card_name.data("condition", condition);
  condition.data("name", card_name);
	var price_div = $("<div></div>").attr({'class':'roboitem', 'id':'price_div_'+index.toString()});
	form_group.append(price_div);
	var price_label = $("<label></label>").attr({'for':'price_'+index.toString()}).html("Buy Price: $");
	var price = $("<input></input>").attr({'class':'buyitem', 'name':'price_'+index.toString(), 'type':'number', 'step':'0.01', 'min':0, 'value':0});
	price.data("quantity", quantity);
	price.change(sumbuyprice);
  expansion.data("price", price);
  condition.data("price", price);
	price_div.append(price_label, price);
  var foil_div = $("<div></div>").attr({'class':'roboitem', 'id':'foil_div_' + index.toString()});
  form_group.append(foil_div);
  var foil_label = $("<label></label>").attr({'for':'foil_'+index.toString()}).html("Foil?");
  var foil = $("<input></input>").attr({'type':'checkbox', 'name':'foil_'+index.toString(), 'id':'foil_'+index.toString()}).prop({'checked':false});
  foil_div.append(foil_label, foil);
  card_name.data("foil", foil);
  foil.data("name", card_name);
  foil.data("price", price);
	var auto_list_div = $("<div></div>").attr({'class':'roboitem', 'id':'auto_list_div_'+index.toString()});
	form_group.append(auto_list_div);
	var auto_list_label = $("<label></label>").attr({'for':'auto_list_'+index.toString()}).html("List?");
	var auto_list = $("<input></input>").attr({'type':'checkbox', 'checked':'true', 'name':'auto_list_'+index.toString(), 'id':'auto_list_'+index.toString()});
  auto_list_div.append(auto_list_label, auto_list);
  var sell_price = $("<input></input>").attr({'type':'hidden', 'name':'sell_price_'+index.toString(), 'id':'sell_price_'+index.toString()});
  form_group.append(sell_price);
  var tcgplayer_card_id = $('<input></input>').attr({'type':'hidden', 'name':'tcgplayer_card_id_'+index.toString(), 'id':'tcgplayer_card_id_'+index.toString()});
  form_group.append(tcgplayer_card_id);
  foil.data("sell_price", sell_price);
  foil.data("tcgplayer_card_id", tcgplayer_card_id);
  expansion.data("sell_price", sell_price);
  expansion.data("tcgplayer_card_id", tcgplayer_card_id);
  condition.data("sell_price", sell_price);
  condition.data("tcgplayer_card_id", tcgplayer_card_id);
  var lowest_listing = $('<input></input>').attr({'type':'hidden', 'name':'lowest_listing_at_buy_'+index.toString(), 'id':'lowest_listing_at_buy_'+index.toString()});
  form_group.append(lowest_listing);
  expansion.data("lowest_listing", lowest_listing);
  condition.data("lowest_listing", lowest_listing);
  foil.data("lowest_listing", lowest_listing);
  var lowest_direct = $('<input></input>').attr({'type':'hidden', 'name':'lowest_direct_at_buy_'+index.toString(), 'id':'lowest_direct_at_buy_'+index.toString()});
  form_group.append(lowest_direct);
  expansion.data("lowest_direct", lowest_direct);
  condition.data("lowest_direct", lowest_direct);
  foil.data("lowest_direct", lowest_direct);
  var market_price = $('<input></input>').attr({'type':'hidden', 'name':'market_price_'+index.toString(), 'id':'market_price_'+index.toString()});
  form_group.append(market_price);
  expansion.data("market_price", market_price);
  condition.data("market_price", market_price);
  foil.data("market_price", market_price);

	index++;
}

$(document).ready(function(){
	create_line();
	$("#addbtn").click(create_line);
	$("#seller_name").change(back_check_seller);
})
