function shipping_method() {
	var shipping_method = $('.shipping:checked').val();
    $('#shipping_method').val(shipping_method);
	if(shipping_method === "Flat Shipping Rate")
    {
        var total = parseFloat($('#sub_total').val()) + 50;
        $('#total').html("$"+total.toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1 "));
    }
    else{
	    $('#total').html("$"+$('#sub_total').val().toString().replace(/(\d)(?=(\d\d\d)+(?!\d))/g, "$1 "));
    }
}
function payment_method() {
	var payment_method = $('.payment:checked').val();
    $('#payment_method').val(payment_method);
}