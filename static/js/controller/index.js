$(document).ready(function() {
	
	var status_str = {
			0: "Empty",
			1: "Reserved",
			2: "Occupied"
	};
	
	$.ajaxSetup({
	    beforeSend:function(){
	        $("#loading").show();
	    },
	    complete:function(){
	        $("#loading").hide();
	    }
	});
	
	var home_tab = $("#home_tab");
	var home_content = $("#tab_content").html();
	home_tab.click(function() {
		$(".current").toggleClass("current");
		$(this).children("a").toggleClass("current");
		$("#tab_content").empty();
		$("#tab_content").html(home_content);
	});
	
	var howto_tab = $("#howto_tab");
	howto_tab.click(function(){
		$(".current").toggleClass("current");
		$(this).children("a").toggleClass("current");
		$("#tab_content").empty();
		$("#tab_content").load("/howtoplay", function() {
			cufon_replace();
		});
	});
	
	var tables = {};
	
	var open_tab = null;
	open_tab = function(id) {
		$("#tab_content").load("/room", function() {
			$("#room_price").html(tables[id].price_btc);
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
			    				if (!answer) {
			    					$.getJSON("/api/seat/cancel", {
						    			price: tables[id].price,
						    			n: s.number
						    		},
						    		function(data) {
						    			if (data.success == true) {
						    				s.state = 0;
						    			}
						    			open_tab(id);
						    		});
			    				}
			    				s.state = 1;
			    				open_tab(id);
			    			}
			    		});
			    		
			    	});
			    }
			});
			cufon_replace();
		});
	};
	
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
					$(this).children("a").toggleClass("current");
					$("#tab_content").empty();
					open_tab(id);
				});
			}
		}
		cufon_replace();
	});
	
	$("#banner_button").click(function(){
		$("#tab_"+1).click();
	});
	
	Cufon.now(); 
	cufon_replace();
	
});