/* ============================================================
   Equipment Borrowing & Return System — interaction layer
   Progressive enhancement only: works against the markup the
   Jinja templates already render, no template changes needed.
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {
  guardDueDateMin();
  autoDismissAlerts();
  markScrollableTables();
  guardBorrowQuantity();
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
    setTimeout(() => {
      if (!document.body.contains(alert)) return;
      if (window.bootstrap && window.bootstrap.Alert) {
        window.bootstrap.Alert.getOrCreateInstance(alert).close();
      } else {
        alert.classList.add('is-dismissing');
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