if (window.frameElement) document.documentElement.dataset.embedded = 'true';
document.addEventListener('keydown', event => {
  if (event.key !== 'Escape') return;
  const menu = document.querySelector('.mobile-menu[open]');
  if (menu) { menu.open = false; menu.querySelector('summary').focus(); }
});

const newsSearch = document.querySelector('#news-search');
if (newsSearch) {
  const cards = Array.from(document.querySelectorAll('.bulletin-card'));
  const buttons = Array.from(document.querySelectorAll('[data-news-filter]'));
  let category = 'Todo';
  const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es-MX');
  function filterNews() {
    const query = normalize(newsSearch.value.trim());
    let count = 0;
    for (const card of cards) {
      card.hidden = !(category === 'Todo' || card.dataset.category === category) || !normalize(card.textContent).includes(query);
      if (!card.hidden) count++;
    }
    document.querySelector('#news-result').textContent = count ? `${count} publicaciones disponibles.` : 'No hay publicaciones que coincidan con tu búsqueda.';
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.newsFilter;
    buttons.forEach(item => item.setAttribute('aria-pressed', String(item === button)));
    filterNews();
  }));
  newsSearch.addEventListener('input', filterNews);
  filterNews();
}
