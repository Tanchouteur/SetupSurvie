/* Classic stays an explicit, stable choice with the same server-side profiles. */
(() => {
  function mark(){for(const a of document.querySelectorAll('a[href^="/pdf.html"],a[href^="/cartes.html"]')){const u=new URL(a.href);u.searchParams.set('interface','classique');a.href=u.href;}}
  document.addEventListener('survie:results',mark);document.addEventListener('survie:source',mark);
  window.addEventListener('DOMContentLoaded',mark);
})();
