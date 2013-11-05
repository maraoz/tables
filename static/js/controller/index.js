$(document).ready(function() {
	var home_tab = $("#home_tab");
	var home_content = $("#tab_content").html();
	home_tab.click(function() {
		$(".current").toggleClass("current");
		$(this).toggleClass("current");
		$("#tab_content").empty();
		$("#tab_content").html(home_content);
	});
	
	var tables = {};
	
	$.getJSON("/api/tables/list", function(data) {
		if (data.success == true) {
			for (var i=0; i<data.list.length; i++) {
				var table = data.list[i];
				var price_btc = table.price / 100000000;
				tables[i] = table;
				table["price_btc"] = price_btc;
				home_tab.after('<li><a id="tab_'+i+'">Room '+price_btc+'<span></span></a></li>');
				$("#tab_"+i).click(function() {
					var id = $(this).attr("id").split("_")[1];
					$(".current").toggleClass("current");
					$(this).toggleClass("current");
					$("#tab_content").empty();
					$("#tab_content").load("/room", function() {
						$("#room_price").html(tables[id].price_btc);
					});
					
					cufon_replace();
				});
			}
			cufon_replace();
		}
	});
	
	Cufon.now(); 
	cufon_replace();
	
});