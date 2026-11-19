/* Navigation commune, sans modifier les outils de la carte. */
(() => {
  const header = document.createElement('header');
  header.className = 'map-site-nav';
  const brand = document.createElement('a');
  brand.className = 'map-site-brand'; brand.href = '/#/accueil';
  const logo = document.createElement('img');
  logo.src = '/branding/logo.png';
  logo.alt = '';
  logo.width = 36;
  logo.height = 40;
  brand.append(logo, 'SetupSurvie');
  const nav = document.createElement('nav'); nav.setAttribute('aria-label', 'Navigation principale');
  for (const [label, route] of [['Accueil','accueil'],['Bibliothèque','bibliotheque'],['Assistant','assistant'],['Cartes','cartes'],['Mon appareil','appareil/ensemble']]) {
    const link = document.createElement('a'); link.href = '/#/' + route; link.textContent = label;
    if (route === 'cartes') { link.href = '/cartes.html'; link.setAttribute('aria-current','page'); }
    nav.append(link);
  }
  header.append(brand, nav);
  const controls=document.querySelector('.map-header');
  if(controls)header.append(controls);
  document.body.prepend(header); document.body.classList.add('has-map-site-nav');
})();
