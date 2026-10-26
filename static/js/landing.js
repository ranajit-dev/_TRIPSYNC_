/* Progressive-enhancement behaviors for the public TripSync homepage.
   No Firebase calls are made here; protected routes remain server gated. */
(() => {
  'use strict';
  const header = document.getElementById('site-header');
  const nav = document.getElementById('site-nav');
  const toggle = document.querySelector('.menu-toggle');
  const motionAllowed = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  if (header) {
    const onScroll = () => header.classList.toggle('is-scrolled', window.scrollY > 45);
    onScroll();
    window.addEventListener('scroll', onScroll, {passive: true});
  }

  const closeNav = () => {
    if (!nav || !toggle) return;
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', 'Open navigation');
  };

  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') !== 'true';
      nav.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', closeNav));
    document.addEventListener('keydown', e => { if (e.key === 'Escape') closeNav(); });
    document.addEventListener('click', e => {
      if (!nav.contains(e.target) && !toggle.contains(e.target)) closeNav();
    });
  }

  const revealEls = document.querySelectorAll('.reveal');
  if (motionAllowed && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries, obs) => {
      for (const item of entries) {
        if (item.isIntersecting) {
          item.target.classList.add('is-visible');
          obs.unobserve(item.target);
        }
      }
    }, {threshold: 0.11, rootMargin: '0px 0px -18px 0px'});
    revealEls.forEach(el => observer.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  // A small, pointer-only photo tilt creates depth without causing page movement.
  if (motionAllowed && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
    document.querySelectorAll('[data-tilt]').forEach(tile => {
      tile.addEventListener('pointermove', e => {
        const rect = tile.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        tile.style.setProperty('--pointer-x', `${50 + x * 5}%`);
        tile.style.setProperty('--pointer-y', `${50 + y * 5}%`);
      }, {passive: true});
      tile.addEventListener('pointerleave', () => {
        tile.style.removeProperty('--pointer-x');
        tile.style.removeProperty('--pointer-y');
      });
    });
  }
})();
