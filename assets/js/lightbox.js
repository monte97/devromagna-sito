// Foto della serata e locandina ingrandite in sovrimpressione.
// Senza JavaScript i link aprono comunque l'immagine.
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll('[data-lightbox]'));
  if (!links.length || typeof HTMLDialogElement === 'undefined') return;

  var dlg = document.createElement('dialog');
  dlg.className = 'lightbox';
  dlg.setAttribute('aria-label', 'Foto ingrandita');
  dlg.innerHTML =
    '<img class="lightbox-img" alt="">' +
    '<button type="button" class="lightbox-chiudi" aria-label="Chiudi">×</button>' +
    '<button type="button" class="lightbox-prec" aria-label="Foto precedente">‹</button>' +
    '<button type="button" class="lightbox-succ" aria-label="Foto successiva">›</button>' +
    '<p class="lightbox-conta" aria-live="polite"></p>';
  document.body.appendChild(dlg);

  var img = dlg.querySelector('.lightbox-img');
  var conta = dlg.querySelector('.lightbox-conta');
  var prec = dlg.querySelector('.lightbox-prec');
  var succ = dlg.querySelector('.lightbox-succ');
  var gruppo = [];
  var i = 0;

  function mostra(n) {
    i = (n + gruppo.length) % gruppo.length;
    var a = gruppo[i];
    img.src = a.getAttribute('href');
    var miniatura = a.querySelector('img');
    img.alt = (miniatura && miniatura.alt) || '';
    conta.textContent = gruppo.length > 1 ? (i + 1) + ' / ' + gruppo.length : '';
    prec.hidden = succ.hidden = gruppo.length < 2;
  }

  links.forEach(function (a) {
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var nome = a.getAttribute('data-lightbox');
      gruppo = links.filter(function (l) { return l.getAttribute('data-lightbox') === nome; });
      mostra(gruppo.indexOf(a));
      dlg.showModal();
    });
  });

  prec.addEventListener('click', function () { mostra(i - 1); });
  succ.addEventListener('click', function () { mostra(i + 1); });
  dlg.querySelector('.lightbox-chiudi').addEventListener('click', function () { dlg.close(); });
  // clic sullo sfondo scuro (fuori dalla foto e dai bottoni) chiude
  dlg.addEventListener('click', function (e) { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('keydown', function (e) {
    if (e.key === 'ArrowLeft') mostra(i - 1);
    if (e.key === 'ArrowRight') mostra(i + 1);
  });
  dlg.addEventListener('close', function () { img.removeAttribute('src'); });
})();
