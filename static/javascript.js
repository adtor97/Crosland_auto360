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
