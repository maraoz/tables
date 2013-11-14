$(document).ready(function() {
	
	var status_str = {
			0: "Empty",
			1: "Reserved",
			2: "Occupied"
	};
	
	var home_tab = $("#home_tab");
	var home_content = $("#tab_content").html();
	home_tab.click(function() {
		$(".current").toggleClass("current");
		$(this).toggleClass("current");
		$("#tab_content").empty();
		$("#tab_content").html(home_content);
	});
	
	var tables = {};
	
	
	var open_tab = function(id) {
		$(".current").toggleClass("current");
		$("#tab_content").empty();
		$("#tab_content").load("/room", function() {
			$("#room_price").html(tables[id].price_btc);
		});
		
		cufon_replace();
		var load_table = null;
		load_table = function() {
			var seats = $("#seats");
			seats.html("");
			var data = tables[id].seats;
			var items = [];
			data.sort(function(a,b){return a.number-b.number});
			$.each(data, function(key, s) {
			    var row = $('<tr></tr>').appendTo(seats);
			    $('<td></td>').text("#"+(s.number+1)).appendTo(row);
			    $('<td></td>').text(status_str[s.state]).appendTo(row);  
			    var play = $('<td></td>').appendTo(row);
			    if (s.state == 0) {
			    	var link = play.append($('<a></a>').text("Take"));
			    	link.click(function(){
			    		$.getJSON("/api/seat/reserve", {
			    			price: tables[id].price,
			    			n: s.number
			    		},
			    		function(data) {
			    			if (data.success == true) {
			    				var answer=window.prompt("Seat reserved. To take the seat, please send "+
					    				tables[id].price/100000000+" BTC to "+s.purchase_addr+
					    				" and press OK when done. Your seat will be reserved for " +
					    				"5 minutes.", s.purchase_addr);
			    				s.state = 1;
			    				load_table();
			    			}
			    		});
			    		
			    	});
			    }
			    //.prepend($('<a></a>').attr({ href: "#" }).text("LINK"))
			});
		};
		setTimeout(load_table, 200);
		
	}
	
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
					$(this).toggleClass("current");
					open_tab(id);
				});
			}
			cufon_replace();
		}
	});
	
	Cufon.now(); 
	cufon_replace();
	
});