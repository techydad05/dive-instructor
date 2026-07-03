/* ============================================
   Deep Dive - Site JavaScript
   Parallax diver, nav, contact form, reveals
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

  /* ==========================================
     MOBILE NAV TOGGLE
     ========================================== */
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (navToggle) {
    navToggle.addEventListener('click', () => {
      navToggle.classList.toggle('active');
      navLinks.classList.toggle('open');
    });

    document.querySelectorAll('.nav-links a').forEach(link => {
      link.addEventListener('click', () => {
        navToggle.classList.remove('active');
        navLinks.classList.remove('open');
      });
    });
  }

  /* ==========================================
     NAVBAR SCROLL EFFECT
     ========================================== */
  const navbar = document.querySelector('.navbar');
  window.addEventListener('scroll', () => {
    navbar.classList.toggle('scrolled', window.scrollY > 50);
  }, { passive: true });

  /* ==========================================
     ACTIVE NAV LINK ON SCROLL
     ========================================== */
  const sections = document.querySelectorAll('section[id]');
  const navAnchors = document.querySelectorAll('.nav-links a:not(.nav-cta)');

  const navObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navAnchors.forEach(a => a.classList.remove('active'));
        const activeLink = document.querySelector(`.nav-links a[href="#${entry.target.id}"]`);
        if (activeLink) activeLink.classList.add('active');
      }
    });
  }, { rootMargin: '-50% 0px -50% 0px' });

  sections.forEach(s => navObserver.observe(s));

  /* ==========================================
     CONTACT FORM
     ========================================== */
  const contactForm = document.getElementById('contactForm');
  const formStatus = document.getElementById('formStatus');

  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const data = Object.fromEntries(new FormData(contactForm).entries());

      formStatus.className = 'form-status';
      formStatus.textContent = 'Sending...';
      formStatus.style.display = 'block';

      try {
        const res = await fetch('/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        const result = await res.json();

        if (result.success) {
          formStatus.className = 'form-status success';
          formStatus.textContent = '✅ Message sent! I\'ll get back to you soon.';
          contactForm.reset();
        } else {
          formStatus.className = 'form-status error';
          formStatus.textContent = '❌ ' + result.message;
        }
      } catch (err) {
        formStatus.className = 'form-status error';
        formStatus.textContent = '❌ Failed to send: ' + err.message;
      }
    });
  }

  /* ==========================================
     SCROLL REVEAL
     ========================================== */
  const revealEls = document.querySelectorAll('.service-card, .gallery-item, .about-image, .about-text');
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  revealEls.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    revealObserver.observe(el);
  });

  /* ==========================================
     SEA LIFE ZOOM-UP
     Fish, jellyfish, seaweed, and bubbles
     zoom up when their section scrolls into view
     ========================================== */
  const seaLifeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const creatures = entry.target.querySelectorAll('.creature');
        const bubbles = entry.target.querySelectorAll('.bubble');
        creatures.forEach(c => { c.classList.add('zoom'); c.classList.add('drift'); });
        bubbles.forEach(b => b.classList.add('zoom'));
        seaLifeObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('.sea-life').forEach(el => seaLifeObserver.observe(el));

});
