function copyClipboard() {
  /* Get the text field */
  var copyText = document.getElementById("myInput");

  /* Select the text field */
  copyText.select();
  copyText.setSelectionRange(0, 99999); /*For mobile devices*/

  /* Copy the text inside the text field */
  document.execCommand("copy");

  /* Alert the copied text */
  alert("Texto copiado: " + copyText.value);
}

function process_once() {

  var msg = document.getElementById('msg');
        msg.innerHTML = 'Boton desabilitado, la data se está procesando';
  document.getElementById('buttom_process').disabled = true;
  document.getElementById('buttom_process').innerHTML = 'Procesando...'

}

function pop_up(){

  // Get the modal
  var modal = document.getElementById("all");

  // Get the button that opens the modal
  var btn = document.getElementById("buttom_process");

  // Get the <span> element that closes the modal
  var span = document.getElementsByClassName("close")[0];

  // When the user clicks the button,   open the modal
  window.onload = function(){
     setTimeout(display, 1000)
  };

  function display() {
    modal.style.display = "block";
  }

  // When the user clicks on <span> (x), close the modal
  span.onclick = function() {
    modal.style.display = "none";
  }

  // When the user clicks anywhere outside of the modal, close it
  window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
  }

}
