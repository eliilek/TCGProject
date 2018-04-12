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
	}
}

function sumbuyprice() {
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
	//Disable critical components - submit button, other inputs in this line
	//TODO

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
								new_option = $("<option></option>").attr({'value':data['results'][i]['abbreviation']}).html(data['results'][i]['abbreviation']).data("group_id", data['results'][i]['groupId']);
                expansion.append(new_option);
							}
							//TODO reenable disabled fields
							//Set change functions on expansion, condition
              expansion.change(price_pull);
              $(this).data("condition").change(price_pull);
						} else {
							//Failure Behaviour
						}
					}
				})
			} else {
				//Alert failure, determine behaviour
			}
			//Set function call on dropdown change, check pricing
			//Set same function call on condition change
			console.log(data);
		}
	});
	console.log("Requested");
}

function price_pull(){
  console.log($(this));
  console.log($(this).data('name'));
  var sku_id = "";
  var group_dict = group_id_table[$(this).data('name').val()];
  var sku_dicts = group_dict[$(this).data('name').data('expansion').children(':selected').data('group_id')];
  var foil = $(this).data('name').data('foil').prop('checked');
  console.log(sku_dicts);
  var sku_id = $.grep(sku_dicts, function(sku){
    return (sku['name'].includes("Near Mint") || sku['name'].includes("Lightly Played")) && sku['language'] == "English" && sku['isFoil'] == foil;
  });
  console.log(sku_id);
  $.ajax({
    "headers":{"Authorization": "bearer " + bearer},
		"url":"http://api.tcgplayer.com/pricing/sku/" + sku_id[0]['productConditionId'].toString() + "," + sku_id[1]['productConditionId'].toString(),
    "success":function(data, textStatus, jqXHR){
      //The Algorithm TODO
      console.log("Success");
      console.log(data);
    },
    "error":function(data, textStatus, jqXHR){
      console.log("Error");
      console.log(data);
    }
  });
}

function process_seller_response(data){
	if(data['found']){
		$("#selleremail").val(data['email']);
		$("#sellerphone").val(data['phone']);
		$("#sellernotes").val(data['notes']);
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
	var card_name = $("<input></input>").attr({'type':'text', 'placeholder':'Card Name', 'name':'cardname_'+index.toString(), 'id':'card_name_'+index.toString()});
	trash_button.data("confirm-name", card_name);
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
	condition.append($("<option></option>").attr({'value':'Near Mint'}).html("NM"));
	condition.append($("<option></option>").attr({'value':'Lightly Played'}).html("LP"));
	condition.append($("<option></option>").attr({'value':'Moderately Played'}).html("MP"));
	condition.append($("<option></option>").attr({'value':'Heavily Played'}).html("HP"));
	condition.append($("<option></option>").attr({'value':'Damaged'}).html("DAM"));
	condition_div.append(condition_label, condition);
  card_name.data("condition", condition);
  condition.data("name", card_name);
	var price_div = $("<div></div>").attr({'class':'roboitem', 'id':'price_div_'+index.toString()});
	form_group.append(price_div);
	var price_label = $("<label></label>").attr({'for':'price_'+index.toString()}).html("Buy Price: $");
	var price = $("<input></input>").attr({'class':'buyitem', 'name':'price_'+index.toString(), 'type':'number', 'step':'0.01', 'min':0, 'value':0});
	price.data("quantity", quantity);
	price.change(sumbuyprice);
	price_div.append(price_label, price);
  var foil_div = $("<div></div>").attr({'class':'roboitem', 'id':'foil_div_' + index.toString()});
  form_group.append(foil_div);
  var foil_label = $("<label></label>").attr({'for':'foil_'+index.toString()}).html("Foil?");
  var foil = $("<input></input>").attr({'type':'checkbox', 'name':'foil_'+index.toString(), 'id':'foil_'+index.toString()}).prop({'checked':false});
  foil_div.append(foil_label, foil);
  card_name.data("foil", foil);
	var auto_list_div = $("<div></div>").attr({'class':'roboitem', 'id':'auto_list_div_'+index.toString()});
	form_group.append(auto_list_div);
	var auto_list_label = $("<label></label>").attr({'for':'auto_list_'+index.toString()}).html("List?");
	var auto_list = $("<input></input>").attr({'type':'checkbox', 'checked':'true', 'name':'auto_list_'+index.toString(), 'id':'auto_list_'+index.toString()});
  auto_list_div.append(auto_list_label, auto_list);

	index++;
}

$(document).ready(function(){
	create_line();
	$("#addbtn").click(create_line);
	$("#sellername").change(back_check_seller);
})
