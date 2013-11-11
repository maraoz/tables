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
		var load_table = function() {
			var seats = $("#seats");
			seats.html("");
			alert(JSON.stringify(tables[id].seats[0]));
			var data = tables[id].seats;
			var items = [];
			$.each(data, function(key, s) {
				alert(key + " "+s);
				items.push(
						"<tr> \
						<td>"+s.number+"</td> \
						<td>"+status_str[s.state]+"</td> \
						<td>"+s.owner+"</td> \
					</tr>"		
				);
			});
			seats.html(items.join(""));
		};
		setTimeout(load_table, 100);
		
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