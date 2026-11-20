/* En-tête des cartes : le balisage est dans cartes.html, comme dans le portail.
   Ce script garde seulement l'initiale de la pastille de profil à jour. */
(() => {
  const label = document.getElementById('map-account-label');
  const avatar = document.querySelector('#map-account .avatar');
  if (!label || !avatar) return;
  const sync = () => {
    const name = label.textContent.trim();
    avatar.textContent = name && name !== 'Choisir un profil' ? Array.from(name)[0].toLocaleUpperCase('fr') : '○';
  };
  new MutationObserver(sync).observe(label, {childList: true, characterData: true, subtree: true});
  sync();
})();
