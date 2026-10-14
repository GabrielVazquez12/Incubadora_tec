const concepts = { a: { file: 'editorial.html', name: 'A · Editorial institucional' }, b: { file: 'innovacion.html', name: 'B · Red de innovación' } };
const params = new URLSearchParams(location.search);
let concept = Object.hasOwn(concepts, params.get('concept')) ? params.get('concept') : 'a';
let size = ['mobile', 'desktop'].includes(params.get('size')) ? params.get('size') : (matchMedia('(max-width: 767px)').matches ? 'mobile' : 'desktop');
const frame = document.querySelector('#preview-frame');
const stage = document.querySelector('.preview-stage');
let availableWidth = 0;
function fitPreview() {
  if (availableWidth) stage.style.setProperty('--preview-scale', Math.min(1, availableWidth / (size === 'mobile' ? 390 : 1280)));
}
new ResizeObserver(entries => { availableWidth = entries[0].contentRect.width; fitPreview(); }).observe(stage);
function render() {
  const selected = concepts[concept];
  if (frame.getAttribute('src') !== selected.file) frame.src = selected.file;
  frame.title = 'Propuesta ' + selected.name;
  document.querySelector('#preview-name').textContent = selected.name;
  document.querySelector('#preview-status').textContent = size === 'mobile' ? 'Vista móvil · hasta 390 px' : 'Vista de escritorio';
  document.querySelector('#open-proposal').href = selected.file;
  stage.dataset.size = size; fitPreview();
  document.querySelectorAll('[data-concept]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.concept === concept)));
  document.querySelectorAll('[data-size]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.size === size)));
  const url = new URL(location.href); url.searchParams.set('concept', concept); url.searchParams.set('size', size);
  history.replaceState(null, '', url);
}
document.querySelectorAll('[data-concept]').forEach(button => button.addEventListener('click', () => { concept = button.dataset.concept; render(); }));
document.querySelectorAll('[data-size]').forEach(button => button.addEventListener('click', () => { size = button.dataset.size; render(); }));
render();
