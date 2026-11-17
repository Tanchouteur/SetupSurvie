/* Navigation commune, sans modifier les outils de la carte. */
(() => {
  const header = document.createElement('header');
  header.className = 'map-site-nav';
  const brand = document.createElement('a');
  brand.className = 'map-site-brand'; brand.href = '/nouveau/#/accueil'; brand.textContent = 'SetupSurvie';
  const nav = document.createElement('nav'); nav.setAttribute('aria-label', 'Navigation principale');
  for (const [label, route] of [['Accueil','accueil'],['Bibliothèque','bibliotheque'],['Assistant','assistant'],['Cartes','cartes'],['Mon appareil','appareil/ensemble']]) {
    const link = document.createElement('a'); link.href = '/nouveau/#/' + route; link.textContent = label;
    if (route === 'cartes') { link.href = '/cartes.html?interface=nouveau'; link.setAttribute('aria-current','page'); }
    nav.append(link);
  }
  header.append(brand, nav); document.body.prepend(header); document.body.classList.add('has-map-site-nav');
})();
