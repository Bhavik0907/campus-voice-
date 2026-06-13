/* Campus Voice – Main JS */

// ── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = { success: 'bi-check-circle-fill', danger: 'bi-x-circle-fill',
                  warning: 'bi-exclamation-triangle-fill', info: 'bi-info-circle-fill' };

  const toast = document.createElement('div');
  toast.className = `toast-item toast-${type}`;
  toast.innerHTML = `
    <i class="bi ${icons[type] || icons.info}"></i>
    <span>${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">
      <i class="bi bi-x"></i>
    </button>`;
  container.appendChild(toast);

  setTimeout(() => { toast.style.opacity = '0'; toast.style.transform = 'translateX(30px)';
    toast.style.transition = '.3s'; setTimeout(() => toast.remove(), 300); }, 4000);
}

// ── Flash messages → toasts ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-flash]').forEach(el => {
    showToast(el.dataset.flashMsg, el.dataset.flash);
  });

  // Sidebar toggle
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const menuBtn  = document.getElementById('menu-toggle');

  if (menuBtn) {
    menuBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      overlay.classList.toggle('show');
    });
  }
  if (overlay) {
    overlay.addEventListener('click', () => {
      sidebar.classList.remove('open');
      overlay.classList.remove('show');
    });
  }

  // File upload drag-and-drop
  const uploadArea = document.querySelector('.upload-area');
  const fileInput  = document.getElementById('image');
  const fileLabel  = document.getElementById('file-label');

  if (uploadArea && fileInput) {
    uploadArea.addEventListener('click', () => fileInput.click());

    ['dragover','dragenter'].forEach(e =>
      uploadArea.addEventListener(e, ev => { ev.preventDefault(); uploadArea.classList.add('dragover'); }));
    ['dragleave','drop'].forEach(e =>
      uploadArea.addEventListener(e, ev => { ev.preventDefault(); uploadArea.classList.remove('dragover'); }));

    uploadArea.addEventListener('drop', e => {
      const files = e.dataTransfer.files;
      if (files.length) { fileInput.files = files; updateFileLabel(files[0]); }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length) updateFileLabel(fileInput.files[0]);
    });

    function updateFileLabel(file) {
      if (fileLabel) fileLabel.textContent = `✓ ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
      showToast('Image selected: ' + file.name, 'success');
    }
  }

  // Admin: complaint detail modal
  document.querySelectorAll('[data-complaint-id]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const id = btn.dataset.complaintId;
      try {
        const res  = await fetch(`/api/complaint/${id}`);
        const data = await res.json();
        populateModal(data);
        const modal = new bootstrap.Modal(document.getElementById('complaintModal'));
        modal.show();
      } catch (e) { showToast('Failed to load complaint details.', 'danger'); }
    });
  });

  // Confirm delete
  document.querySelectorAll('.delete-btn').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm('Delete this complaint? This cannot be undone.')) e.preventDefault();
    });
  });

  // Admin: inline status/priority update
  document.querySelectorAll('.quick-update').forEach(form => {
    form.querySelectorAll('select').forEach(sel => {
      sel.addEventListener('change', () => form.submit());
    });
  });

  // Search debounce
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    let timer;
    searchInput.addEventListener('input', () => {
      clearTimeout(timer);
      timer = setTimeout(() => searchInput.form.submit(), 600);
    });
  }
});

// ── Populate modal with complaint data ────────────────────────────────────
function populateModal(d) {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val || '—'; };
  set('m-id',          '#' + d.id);
  set('m-title',       d.title);
  set('m-student',     d.student_name + ' (' + d.student_email + ')');
  set('m-category',    d.category);
  set('m-status',      d.status);
  set('m-priority',    d.priority);
  set('m-created',     d.created_at);
  set('m-description', d.description);

  const img = document.getElementById('m-image');
  if (img) {
    if (d.image) { img.src = '/static/uploads/' + d.image; img.style.display = 'block'; }
    else         { img.style.display = 'none'; }
  }
}

// ── Password toggle ───────────────────────────────────────────────────────
function togglePassword(inputId, iconId) {
  const input = document.getElementById(inputId);
  const icon  = document.getElementById(iconId);
  if (!input || !icon) return;
  if (input.type === 'password') {
    input.type = 'text'; icon.className = 'bi bi-eye-slash';
  } else {
    input.type = 'password'; icon.className = 'bi bi-eye';
  }
}

// ── Status badge helper ───────────────────────────────────────────────────
function statusClass(s) {
  const map = { 'Pending': 'badge-pending', 'Assigned': 'badge-assigned',
                'In Progress': 'badge-inprogress', 'Resolved': 'badge-resolved' };
  return map[s] || 'badge-pending';
}
