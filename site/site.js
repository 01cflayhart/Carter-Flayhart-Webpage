// Keep the sticky navigation aligned even when fonts, zoom, or text size change.
const profile = document.querySelector('.profile-header');
if (profile) new ResizeObserver(() => {
  document.documentElement.style.setProperty('--profile-height', profile.offsetHeight + 'px');
}).observe(profile);

// Real hash links keep sections shareable. Without JS, all sections remain readable.
const sections = [...document.querySelectorAll('.content-section[id]')];
const links = [...document.querySelectorAll('.section-nav a[href^="#"]')];

const publicationList = document.querySelector('.publication-list');
if (publicationList) {
  const papers = [...publicationList.querySelectorAll('.publication')];
  const buttons = [...document.querySelectorAll('[data-publication-filter]')];
  const sort = document.querySelector('#publication-sort');
  const status = document.querySelector('.publication-status');
  let filter = 'all';
  function updatePublications() {
    papers.sort((a, b) => {
      const date = b.dataset.date.localeCompare(a.dataset.date);
      if (sort.value === 'newest') return date || a.dataset.bibcode.localeCompare(b.dataset.bibcode);
      if (sort.value === 'oldest') return -date || a.dataset.bibcode.localeCompare(b.dataset.bibcode);
      if (sort.value === 'title') return a.querySelector('h3').textContent.localeCompare(b.querySelector('h3').textContent);
      return Number(b.dataset.citations) - Number(a.dataset.citations) || date || a.dataset.bibcode.localeCompare(b.dataset.bibcode);
    });
    let count = 0;
    for (const paper of papers) {
      paper.hidden = !(filter === 'all' || (filter === 'first' && paper.dataset.firstAuthor === 'true') || (filter === 'refereed' && paper.dataset.refereed === 'true') || (filter === 'non-refereed' && paper.dataset.refereed === 'false'));
      if (!paper.hidden) count++;
      publicationList.append(paper);
    }
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.publicationFilter === filter));
    status.textContent = count ? `${count} ${count === 1 ? 'paper' : 'papers'}` : 'No papers in this selection yet.';
  }
  document.querySelector('.publication-controls').hidden = false;
  status.hidden = false;
  for (const button of buttons) button.addEventListener('click', () => { filter = button.dataset.publicationFilter; updatePublications(); });
  sort.addEventListener('change', updatePublications);
  updatePublications();
}

const talkList = document.querySelector('.talk-list');
if (talkList) [...talkList.children].sort((a, b) => b.dataset.date.localeCompare(a.dataset.date)).forEach(talk => talkList.append(talk));

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
