$(document).ready(function() {
  function completePost() {
    var submitForm = $("#submitForm");
    submitForm.off('submit');
    submitForm.submit();
  }

  $("#finish").click(function(event) {
    event.preventDefault();
    var selectedButton = $("#submitForm input[name=answer]:checked");
    if (selectedButton.length == 0) {
      alert("Must select a button!");
      return;
    }
    $.post("/", 
           {answer: selectedButton.val(),
            cmp_key: $("#cmp_key").val()},
	    completePost);
  });
});
