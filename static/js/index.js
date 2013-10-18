$(document).ready(function() {
	var tables = $("#tables");
	tables.html("Loading...");
	$.getJSON("/api/tables/list", function(data) {
		if (data.success == true) {
			tables.html(JSON.stringify(data.list));
		}
	});
});