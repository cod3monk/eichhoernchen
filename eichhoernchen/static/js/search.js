$(function() {
	// ensure the search box is focused on load
	$('#q').focus();
	// run queries
	var lastKeyUpEvent = 0;
	$('#q').keyup(function (event) {
		lastKeyUpEvent = event.timeStamp;
		window.setTimeout(handleSearchChange, 250, event, $(this));
	});

	function handleSearchChange(event, qField) {
		if (lastKeyUpEvent != event.timeStamp) {
			// there was another keyup event, skip handling this one
			return;
		}

		var queryString = qField.val().trim();
		if (queryString == '') {
			// don't send a request if the query is empty
			$('#result_list').text('');
			return;
		}

		$.getJSON('db/obj/search', {
			q: queryString
		}, function(data, textStatus, jqXHR) {
			$('#result_list').html('<pre>' + JSON.stringify(data) + '</pre>');
		});
	}
})
