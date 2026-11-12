/* ============================================================
   Equipment Borrowing & Return System — interaction layer
   Progressive enhancement only: works against the markup the
   Jinja templates already render, no template changes needed.
   ============================================================ */

const FX = { cursorTrail: true, floatingDecor: true, sparkles: true, tilt: true, scrollBar: true };

document.addEventListener('DOMContentLoaded', () => {
  guardDueDateMin();
  autoDismissAlerts();
  markScrollableTables();
  guardBorrowQuantity();
  initAuthToggle();
  initAnimatedStats();
  initTableRowReveal();
  initBadgeStamps();
  initFormFieldMotion();
  initButtonFeedback();
  initSubmitButtonLoading();
  initHoverCards();
  initRowHighlightAfterAction();
  initLogoutModal();
  initSuccessSparkles();
  initTitleBounces();
  initMascotLife();
  initEmptyStateMascot();
  initHoverTilt();
  initScrollProgressBar();
  initFloatingDecor();
  initCursorTrail();
});

/* Due date can't be set before today. */
function guardDueDateMin() {
  const today = new Date().toISOString().split('T')[0];
  const dueInput = document.getElementById('due_on');
  if (dueInput) {
    dueInput.setAttribute('min', today);
  }
}

/* Auto-dismiss flash messages after a pause. Uses Bootstrap's own
   Alert API when available so the element is actually removed from
   the DOM afterward, not just left invisible taking up space. */
function autoDismissAlerts() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach((alert, index) => {
    requestAnimationFrame(() => alert.classList.add('alert-animate-in'));

    setTimeout(() => {
      if (!document.body.contains(alert)) return;
      alert.classList.add('is-dismissing');

      if (window.bootstrap && window.bootstrap.Alert) {
        const instance = window.bootstrap.Alert.getOrCreateInstance(alert);
        instance.close();
      } else {
        setTimeout(() => alert.remove(), 220);
      }
    }, 5000 + index * 150);
  });
}

/* Adds a right-edge fade indicator on tables that overflow
   horizontally, so a scrollable table doesn't look cut off on
   narrow screens. Re-checks on scroll and on resize. */
function markScrollableTables() {
  const wrappers = document.querySelectorAll('.table-responsive');
  wrappers.forEach((wrapper) => {
    const update = () => {
      const overflowing = wrapper.scrollWidth > wrapper.clientWidth + 1;
      const atEnd = wrapper.scrollLeft + wrapper.clientWidth >= wrapper.scrollWidth - 1;
      wrapper.classList.toggle('has-scroll', overflowing && !atEnd);
    };
    update();
    wrapper.addEventListener('scroll', update);
    window.addEventListener('resize', update);
  });
}

/* On the "new borrowing" form, read the available-quantity figure
   straight out of the equipment dropdown's own option text
   (e.g. "Hammer (4 available)") and warn before submit if the
   requested quantity would exceed it. Mirrors the server-side rule
   in borrowings.py — doesn't replace it, the server still validates. */
function guardBorrowQuantity() {
  const equipmentSelect = document.getElementById('equipment_id');
  const quantityInput = document.getElementById('quantity');
  if (!equipmentSelect || !quantityInput) return;

  const warning = document.createElement('small');
  warning.className = 'text-danger d-block mt-1';
  warning.style.display = 'none';
  quantityInput.insertAdjacentElement('afterend', warning);

  const availableFor = (option) => {
    const match = option ? option.textContent.match(/\((\d+)\s+available\)/) : null;
    return match ? parseInt(match[1], 10) : null;
  };

  const check = () => {
    const option = equipmentSelect.options[equipmentSelect.selectedIndex];
    const available = availableFor(option);
    const requested = parseInt(quantityInput.value, 10);

    if (available !== null && requested > available) {
      warning.textContent = `Only ${available} unit(s) available.`;
      warning.style.display = 'block';
      quantityInput.setCustomValidity('Quantity exceeds available units.');
    } else {
      warning.style.display = 'none';
      quantityInput.setCustomValidity('');
    }
  };

  equipmentSelect.addEventListener('change', check);
  quantityInput.addEventListener('input', check);
}

/* On the sign-in/sign-up page, flip the container's mode class and let
   the CSS morph the panel. Both forms are already in the DOM, so this
   never navigates; only a real submit does. */
function initAuthToggle() {
  const container = document.getElementById('authContainer');
  if (!container) return;

  const toLogin = document.getElementById('flipToLogin');
  const toRegister = document.getElementById('flipToRegister');
  const signinForm = container.querySelector('.flip-auth__form-container--signin form');
  const signupForm = container.querySelector('.flip-auth__form-container--signup form');
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const setMode = (mode) => {
    if (container.dataset.mode === mode) return;

    const isRegister = mode === 'register';
    const form = isRegister ? signupForm : signinForm;

    container.classList.toggle('flip-auth--active', isRegister);
    container.dataset.mode = mode;
    document.title = isRegister ? 'Sign Up' : 'Sign In';

    history.replaceState({ mode }, '', form.getAttribute('action'));

    setTimeout(() => {
      const first = form.querySelector('input');
      if (first) first.focus({ preventScroll: true });
    }, reduceMotion.matches ? 0 : 450);
  };

  if (toRegister) toRegister.addEventListener('click', () => setMode('register'));
  if (toLogin) toLogin.addEventListener('click', () => setMode('login'));
}

function initAnimatedStats() {
  const statNodes = document.querySelectorAll('.row.g-3 .card-body h3');
  if (!statNodes.length) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const animate = (node) => {
    const raw = node.textContent.trim();
    const value = Number.parseInt(raw.replace(/[^0-9-]/g, ''), 10);
    if (!Number.isFinite(value)) return;

    node.dataset.targetValue = String(value);
    node.textContent = '0';

    if (reduceMotion.matches) {
      node.textContent = String(value);
      return;
    }

    const duration = 900;
    const start = performance.now();

    const tick = (time) => {
      const progress = Math.min((time - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(value * eased);
      node.textContent = String(current);

      if (progress < 1) {
        requestAnimationFrame(tick);
      } else {
        node.textContent = String(value);
      }
    };

    requestAnimationFrame(tick);
  };

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      if (entry.target.dataset.counted === 'true') {
        obs.unobserve(entry.target);
        return;
      }

      entry.target.dataset.counted = 'true';
      animate(entry.target);
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.35 });

  statNodes.forEach((node) => observer.observe(node));
}

function initTableRowReveal() {
  const rows = document.querySelectorAll('.table tbody tr');
  if (!rows.length) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  rows.forEach((row, index) => {
    row.style.setProperty('--row-delay', `${Math.min(index * 70, 420)}ms`);
    row.classList.add('table-row-reveal');
  });

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('is-visible');
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.15 });

  rows.forEach((row) => {
    if (reduceMotion.matches) {
      row.classList.add('is-visible');
      return;
    }
    observer.observe(row);
  });
}

function initBadgeStamps() {
  const badges = document.querySelectorAll('.badge');
  if (!badges.length) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      entry.target.classList.add('badge-stamped');
      obs.unobserve(entry.target);
    });
  }, { threshold: 0.8 });

  badges.forEach((badge) => {
    if (reduceMotion.matches) {
      badge.classList.add('badge-stamped');
      return;
    }
    observer.observe(badge);
  });
}

function initFormFieldMotion() {
  const inputs = document.querySelectorAll('input, select, textarea');

  inputs.forEach((field) => {
    if (field.dataset.fieldMotionReady === 'true') return;
    field.dataset.fieldMotionReady = 'true';

    field.addEventListener('focus', () => field.classList.add('field-focused'));
    field.addEventListener('blur', () => field.classList.remove('field-focused'));

    field.addEventListener('invalid', () => {
      field.classList.remove('field-shake');
      void field.offsetWidth;
      field.classList.add('field-shake');
    });
  });
}

function initButtonFeedback() {
  const buttons = document.querySelectorAll('.btn');

  buttons.forEach((button) => {
    button.addEventListener('pointerdown', () => button.classList.add('btn-pressed'));
    button.addEventListener('pointerup', () => button.classList.remove('btn-pressed'));
    button.addEventListener('pointerleave', () => button.classList.remove('btn-pressed'));
    button.addEventListener('pointercancel', () => button.classList.remove('btn-pressed'));

    if (FX.sparkles && button.classList.contains('btn-primary')) {
      button.addEventListener('pointerdown', (event) => {
        createSparkleBurstAt(event.clientX, event.clientY, button, 5);
      });
    }
  });
}

function initSubmitButtonLoading() {
  const forms = document.querySelectorAll('form');
  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      const submitter = event.submitter || form.querySelector('button[type="submit"]') || form.querySelector('input[type="submit"]');
      if (!submitter) return;

      if (submitter.dataset.loading === 'true') {
        event.preventDefault();
        return;
      }

      submitter.dataset.loading = 'true';
      submitter.classList.add('is-loading');
      submitter.setAttribute('aria-busy', 'true');
      submitter.disabled = true;

      const label = submitter.dataset.originalText || submitter.textContent.trim() || 'Submit';
      submitter.dataset.originalText = label;
      submitter.innerHTML = '<span class="btn-loader" aria-hidden="true"></span><span class="btn-text">Submitting…</span>';
    });
  });

  window.addEventListener('pageshow', () => {
    document.querySelectorAll('.btn.is-loading').forEach((button) => {
      button.classList.remove('is-loading');
      button.removeAttribute('aria-busy');
      button.disabled = false;
      const label = button.dataset.originalText || 'Submit';
      button.innerHTML = label;
      button.dataset.loading = 'false';
    });
  });
}

function initHoverCards() {
  const cards = document.querySelectorAll('.card');
  cards.forEach((card) => {
    if (card.closest('form')) return;
    card.classList.add('card-lift');
  });
}

function initRowHighlightAfterAction() {
  const forms = document.querySelectorAll('form[action*="approve_borrowing"], form[action*="reject_borrowing"], form[action*="return_borrowing"]');

  forms.forEach((form) => {
    form.addEventListener('submit', () => {
      const row = form.closest('tr');
      if (!row) return;

      row.classList.remove('row-highlight');
      void row.offsetWidth;
      row.classList.add('row-highlight');
      setTimeout(() => row.classList.remove('row-highlight'), 1200);
    });
  });
}

function initSuccessSparkles() {
  if (!FX.sparkles) return;

  document.querySelectorAll('.alert-success').forEach((alert) => {
    if (alert.dataset.sparkleReady === 'true') return;
    alert.dataset.sparkleReady = 'true';
    createSparkleBurstAt(
      alert.getBoundingClientRect().left + alert.offsetWidth * 0.5,
      alert.getBoundingClientRect().top + alert.offsetHeight * 0.5,
      alert,
      6,
      true
    );
  });
}

function initTitleBounces() {
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduceMotion.matches) return;

  document.querySelectorAll('h2').forEach((heading) => {
    const text = heading.textContent.trim();
    if (!text || text.length > 30) return;

    heading.setAttribute('aria-label', text);
    heading.innerHTML = '';

    [...text].forEach((char, index) => {
      const span = document.createElement('span');
      span.className = 'title-letter';
      span.setAttribute('aria-hidden', 'true');
      span.style.setProperty('--letter-delay', `${index * 40}ms`);
      span.textContent = char === ' ' ? '\u00A0' : char;
      heading.appendChild(span);
    });
  });
}

function initMascotLife() {
  const logo = document.querySelector('.navbar-brand img');
  if (!logo) return;

  logo.addEventListener('mouseenter', () => logo.classList.add('usagi-wiggle'));
  logo.addEventListener('mouseleave', () => logo.classList.remove('usagi-wiggle'));
  logo.addEventListener('click', () => {
    logo.classList.remove('usagi-hop');
    void logo.offsetWidth;
    logo.classList.add('usagi-hop');
  });
}

function initEmptyStateMascot() {
  document.querySelectorAll('td[colspan]').forEach((cell) => {
    const text = cell.textContent.trim();
    if (!/^No\s+/i.test(text)) return;

    if (cell.querySelector('.empty-state-mascot')) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'empty-state-mascot';
    wrapper.setAttribute('aria-hidden', 'true');

    const img = document.createElement('img');
    img.src = '/static/images/usagi.png';
    img.alt = '';
    img.width = 34;
    img.height = 34;

    wrapper.appendChild(img);
    cell.insertBefore(wrapper, cell.firstChild);
  });
}

function initHoverTilt() {
  if (!FX.tilt || window.matchMedia('(pointer: fine)').matches === false) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduceMotion.matches) return;

  document.querySelectorAll('.row.g-3 .card').forEach((card) => {
    card.classList.add('tilt-card');

    card.addEventListener('pointermove', (event) => {
      const rect = card.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width;
      const py = (event.clientY - rect.top) / rect.height;
      const rotateY = (px - 0.5) * 12;
      const rotateX = (0.5 - py) * 12;
      card.style.setProperty('--tilt-x', `${rotateX.toFixed(2)}deg`);
      card.style.setProperty('--tilt-y', `${rotateY.toFixed(2)}deg`);
      card.style.setProperty('--glare-x', `${(px * 100).toFixed(0)}%`);
      card.style.setProperty('--glare-y', `${(py * 100).toFixed(0)}%`);
    });

    card.addEventListener('pointerleave', () => {
      card.style.setProperty('--tilt-x', '0deg');
      card.style.setProperty('--tilt-y', '0deg');
    });
  });
}

function initScrollProgressBar() {
  if (!FX.scrollBar) return;

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduceMotion.matches) return;

  const bar = document.createElement('div');
  bar.id = 'scroll-progress-bar';
  bar.setAttribute('aria-hidden', 'true');
  document.body.appendChild(bar);

  const update = () => {
    const maxScroll = document.documentElement.scrollHeight - window.innerHeight;
    const progress = maxScroll > 0 ? (window.scrollY / maxScroll) * 100 : 0;
    bar.style.width = `${Math.min(Math.max(progress, 0), 100)}%`;
  };

  update();
  window.addEventListener('scroll', () => window.requestAnimationFrame(update), { passive: true });
}

function initFloatingDecor() {
  if (!FX.floatingDecor || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  if (window.innerWidth < 768) return;

  const layer = document.createElement('div');
  layer.className = 'floating-decor-layer';
  layer.setAttribute('aria-hidden', 'true');

  const marks = ['✦', '✧', '✦', '✦', '•', '✦'];
  marks.forEach((symbol, index) => {
    const deco = document.createElement('span');
    deco.className = 'floating-decor';
    deco.textContent = symbol;
    deco.style.setProperty('--deco-left', `${((index + 1) * 15) % 93}%`);
    deco.style.setProperty('--deco-top', `${(index % 3) * 28 + 8}%`);
    deco.style.setProperty('--deco-delay', `${index * 0.8}s`);
    layer.appendChild(deco);
  });

  document.body.appendChild(layer);
}

function initCursorTrail() {
  if (!FX.cursorTrail || window.matchMedia('(pointer: fine)').matches === false) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  let lastTime = 0;
  let active = 0;

  const onMove = (event) => {
    const target = event.target;
    if (target && target.closest('input, textarea, select, .modal, .btn-close')) return;

    const now = performance.now();
    if (now - lastTime < 60) return;
    lastTime = now;
    if (active >= 8) return;

    const spark = document.createElement('span');
    spark.className = 'cursor-sparkle';
    spark.style.left = `${event.clientX}px`;
    spark.style.top = `${event.clientY}px`;
    spark.style.setProperty('--spark-size', `${(Math.random() * 7 + 7).toFixed(0)}px`);
    spark.style.setProperty('--spark-shift-x', `${(Math.random() * 18 - 9).toFixed(0)}px`);
    spark.style.setProperty('--spark-shift-y', `${(Math.random() * 18 - 9).toFixed(0)}px`);
    document.body.appendChild(spark);
    active += 1;

    setTimeout(() => {
      spark.remove();
      active -= 1;
    }, 500);
  };

  document.addEventListener('pointermove', onMove, { passive: true });
}

function createSparkleBurstAt(x, y, host, count, fromCenter) {
  if (!FX.sparkles || !host) return;

  const target = host.ownerDocument || document;
  const burst = target.createElement('span');
  burst.className = 'sparkle-burst';

  const rect = host.getBoundingClientRect();
  const originX = typeof x === 'number' ? x : rect.left + rect.width / 2;
  const originY = typeof y === 'number' ? y : rect.top + rect.height / 2;

  for (let i = 0; i < count; i += 1) {
    const spark = target.createElement('span');
    spark.className = 'sparkle';
    spark.textContent = i % 2 === 0 ? '✦' : '✧';
    const angle = (Math.PI * 2 * i) / count + (fromCenter ? Math.PI / 5 : 0);
    const distance = fromCenter ? 18 + Math.random() * 18 : 12 + Math.random() * 18;
    spark.style.left = `${originX}px`;
    spark.style.top = `${originY}px`;
    spark.style.setProperty('--spark-angle', `${angle}rad`);
    spark.style.setProperty('--spark-distance', `${distance}px`);
    spark.style.setProperty('--spark-delay', `${(i * 30) / 1000}s`);
    target.body.appendChild(spark);
    setTimeout(() => spark.remove(), 600);
  }

  burst.remove();
}

function initLogoutModal() {
  const modalEl = document.getElementById('logoutModal');
  if (!modalEl) return;

  const modal = window.bootstrap ? window.bootstrap.Modal.getOrCreateInstance(modalEl) : null;
  const stayButton = modalEl.querySelector('.logout-stay');
  const form = modalEl.querySelector('form');
  const logoutButton = modalEl.querySelector('.logout-confirm');

  modalEl.addEventListener('shown.bs.modal', () => {
    if (stayButton) stayButton.focus();
    const card = modalEl.querySelector('.logout-modal-card');
    if (card) {
      card.classList.remove('is-closing');
      card.classList.add('is-open');
    }
  });

  modalEl.addEventListener('hide.bs.modal', () => {
    const card = modalEl.querySelector('.logout-modal-card');
    if (card) {
      card.classList.remove('is-open');
      card.classList.add('is-closing');
    }
  });

  if (form && logoutButton) {
    form.addEventListener('submit', () => {
      logoutButton.disabled = true;
      logoutButton.classList.add('is-loading');
      logoutButton.setAttribute('aria-busy', 'true');
      logoutButton.dataset.originalText = logoutButton.dataset.originalText || logoutButton.textContent.trim();
      logoutButton.innerHTML = '<span class="btn-loader" aria-hidden="true"></span><span class="btn-text">Logging out…</span>';
    });
  }

  if (modal && stayButton) {
    stayButton.addEventListener('click', () => modal.hide());
  }
}
