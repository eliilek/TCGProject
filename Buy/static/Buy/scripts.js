$("#addbtn").click(roboclone);
$(".trashbtn").click(robodelete);
$(".robocontainer").toggle();
var index = 0;
$("#addbtn").click();



function roboclone (){
	console.log(index);
	// Grab the last Div on the page - Clone it
	// Make sure the event listeners and children's event listeners are cloned also (true true)
	// Append it to the Form element, then Show it.
	// console.log($("input[name='cardname"+index+"']").attr("name", "cardname"+index));
	// $("input[name='cardname']").attr("name", );
	var clone = $(".robocontainer:first").clone(true, true);
	clone.find("input[name='cardname']").name="cardname"+index;
	clone.find("input[name='expansion']").name="expansion"+index;
	clone.find("input[name='quantity']").name="quantity"+index;
	clone.find("input[name='condition']").name="condition"+index;
	clone.find("input[name='buyprice']").name="buyprice"+index;
	clone.find("input[name='autolist']").name="autolist"+index;
	clone.appendTo($(".roboform"));
	$(".robocontainer:last").toggle();
	// $("input[name='cardname""']").attr("name", function(index) {
	// 	return "cardname"+index;
	// });
	//This code grabs all divs, sets the Div ID's to div-id0, div-id1 .. etc, then sets the innerhtml inside the spans to be the div-idX.
// 	$( "div" )
//   .attr( "id", function( arr ) {
//     return "div-id" + arr;
//   })
//   .each(function() {
//     $( "span", this ).html( "(id = '<b>" + this.id + "</b>')" );
// });
}


// Delete the X buttons parent element - and confirm - These nodes are the current Node path from the X delete button object
function robodelete (){
	if (confirm("Remove " + this.parentNode.childNodes[3].childNodes[1].childNodes[1].value + "?")){
		this.parentNode.remove();
	}
}
