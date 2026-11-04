// Keep the sticky navigation aligned even when fonts, zoom, or text size change.
const profile = document.querySelector('.profile-header');
if (profile) new ResizeObserver(() => {
  document.documentElement.style.setProperty('--profile-height', profile.offsetHeight + 'px');
}).observe(profile);

// Real hash links keep sections shareable. Without JS, all sections remain readable.
const sections = [...document.querySelectorAll('.content-section[id]')];
const links = [...document.querySelectorAll('.section-nav a[href^="#"]')];

function showSection(focus = false) {
  const selected = sections.find(section => '#' + section.id === location.hash) || sections[0];
  for (const section of sections) section.hidden = section !== selected;
  for (const link of links) {
    if (link.hash === '#' + selected.id) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  }
  document.title = selected.querySelector('h2').textContent + ' — Carter Flayhart';
  if (focus) selected.querySelector('h2').focus({ preventScroll: true });
}

function resetSectionScroll() {
  requestAnimationFrame(() => requestAnimationFrame(() => window.scrollTo(0, 0)));
}

if (sections.length) {
  document.body.classList.add('enhanced');
  showSection();
  // Native initial fragment scrolling would hide the shared profile on phones.
  window.addEventListener('load', () => {
    if (sections.some(section => '#' + section.id === location.hash)) {
      resetSectionScroll();
    }
  }, { once: true });
  for (const link of links) link.addEventListener('click', event => {
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    if (location.hash !== link.hash) history.pushState(null, '', link.hash);
    showSection(true);
    window.scrollTo(0, 0);
  });
  window.addEventListener('popstate', () => { showSection(true); resetSectionScroll(); });
  window.addEventListener('hashchange', () => {
    showSection();
    if (sections.some(section => '#' + section.id === location.hash)) resetSectionScroll();
  });
}
