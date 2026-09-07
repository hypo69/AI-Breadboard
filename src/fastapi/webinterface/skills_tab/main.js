// Skills Tab Logic for AI Breadboard Admin Interface

class SkillsTabManager {
  constructor() {
    this.skills = [];
    this.filteredSkills = [];
    this.currentSkill = null;
    this.viewMode = 'cards'; // 'cards' | 'table'
    this.searchQuery = '';
    this.activeFilter = 'all'; // 'all' | 'scripts' | 'references' | 'packaged'
    this.isInitialized = false;
  }

  async init() {
    if (this.isInitialized) {
      await this.refresh();
      return;
    }
    this.bindEvents();
    this.isInitialized = true;
    await this.refresh();
  }

  bindEvents() {
    const searchInput = document.getElementById('skills-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.searchQuery = e.target.value.trim().toLowerCase();
        this.applyFilters();
      });
    }

    const nameInput = document.getElementById('new-skill-name');
    if (nameInput) {
      nameInput.addEventListener('input', (e) => {
        const val = e.target.value;
        const normalized = val.toLowerCase().replace(/[^a-z0-9_-]/g, '-');
        if (val !== normalized) {
          e.target.value = normalized;
        }
      });
    }
  }

  async apiFetch(endpoint, options = {}) {
    let url = endpoint;
    let res = await fetch(url, options);
    if (!res.ok && url.startsWith('/api/skills')) {
      const fallbackUrl = url.replace('/api/skills', '/api/admin/skills');
      const fallbackRes = await fetch(fallbackUrl, options);
      if (fallbackRes.ok) {
        return fallbackRes;
      }
    }
    return res;
  }

  async refresh() {
    this.showLoading(true);
    try {
      const response = await this.apiFetch('/api/skills');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.skills = data.skills || [];
      this.updateStats();
      this.applyFilters();
    } catch (err) {
      console.error('[SkillsTab] Load error:', err);
      const cardsContainer = document.getElementById('skills-cards-container');
      if (cardsContainer) {
        cardsContainer.innerHTML = `
          <div class="col-12">
            <div class="alert alert-danger d-flex align-items-center justify-content-between p-3 shadow-sm">
              <div><i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Ошибка загрузки навыков:</strong> ${err.message}</div>
              <button class="btn btn-sm btn-outline-light" onclick="window.skillsTab?.refresh()">Повторить</button>
            </div>
          </div>
        `;
      }
    } finally {
      this.showLoading(false);
    }
  }

  updateStats() {
    const total = this.skills.length;
    const withScripts = this.skills.filter(s => s.has_scripts).length;
    const withRefs = this.skills.filter(s => s.has_references).length;
    const packaged = this.skills.filter(s => s.has_dist).length;

    const setVal = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };

    setVal('skills-total-badge', total);
    setVal('stat-total-skills', total);
    setVal('stat-scripts-skills', withScripts);
    setVal('stat-refs-skills', withRefs);
    setVal('stat-packaged-skills', packaged);
  }

  applyFilters() {
    const filterSelect = document.getElementById('skills-filter-select');
    this.activeFilter = filterSelect ? filterSelect.value : 'all';

    this.filteredSkills = this.skills.filter(skill => {
      // Search text match
      if (this.searchQuery) {
        const nameMatch = (skill.name || '').toLowerCase().includes(this.searchQuery);
        const descMatch = (skill.description || '').toLowerCase().includes(this.searchQuery);
        if (!nameMatch && !descMatch) return false;
      }

      // Feature filter match
      if (this.activeFilter === 'scripts' && !skill.has_scripts) return false;
      if (this.activeFilter === 'references' && !skill.has_references) return false;
      if (this.activeFilter === 'packaged' && !skill.has_dist) return false;

      return true;
    });

    this.render();
  }

  clearSearch() {
    const searchInput = document.getElementById('skills-search-input');
    if (searchInput) searchInput.value = '';
    this.searchQuery = '';
    this.applyFilters();
  }

  setViewMode(mode) {
    this.viewMode = mode;
    const btnCards = document.getElementById('btn-view-cards');
    const btnTable = document.getElementById('btn-view-table');

    if (mode === 'cards') {
      btnCards?.classList.add('active');
      btnTable?.classList.remove('active');
    } else {
      btnCards?.classList.remove('active');
      btnTable?.classList.add('active');
    }
    this.render();
  }

  render() {
    const cardsContainer = document.getElementById('skills-cards-container');
    const tableCard = document.getElementById('skills-table-card');
    const emptyNotice = document.getElementById('skills-empty');

    if (!cardsContainer || !tableCard) return;

    if (this.filteredSkills.length === 0) {
      cardsContainer.innerHTML = '';
      tableCard.classList.add('d-none');
      emptyNotice?.classList.remove('d-none');
      return;
    }

    emptyNotice?.classList.add('d-none');

    if (this.viewMode === 'cards') {
      tableCard.classList.add('d-none');
      cardsContainer.classList.remove('d-none');
      cardsContainer.innerHTML = this.filteredSkills.map(s => this.renderCard(s)).join('');
    } else {
      cardsContainer.classList.add('d-none');
      tableCard.classList.remove('d-none');
      const tableBody = document.getElementById('skills-table-body');
      if (tableBody) {
        tableBody.innerHTML = this.filteredSkills.map(s => this.renderTableRow(s)).join('');
      }
    }
  }

  renderCard(skill) {
    const escapeHtml = str => String(str || '').replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));

    const badges = [];
    if (skill.has_scripts) badges.push('<span class="badge bg-info-subtle text-info border border-info-subtle small me-1"><i class="bi bi-file-earmark-code"></i> scripts</span>');
    if (skill.has_references) badges.push('<span class="badge bg-warning-subtle text-warning border border-warning-subtle small me-1"><i class="bi bi-journal-text"></i> references</span>');
    if (skill.has_assets) badges.push('<span class="badge bg-secondary border border-secondary small me-1"><i class="bi bi-images"></i> assets</span>');
    if (skill.has_dist) badges.push('<span class="badge bg-success-subtle text-success border border-success-subtle small me-1"><i class="bi bi-box-seam"></i> .skill</span>');

    return `
      <div class="col-12 col-md-6 col-lg-4">
        <div class="card bg-dark border-secondary text-white h-100 shadow-sm skill-card">
          <div class="card-header border-secondary d-flex justify-content-between align-items-center bg-black bg-opacity-25 py-2">
            <span class="badge bg-primary font-monospace fs-6 text-truncate" style="max-width: 70%;" title="${escapeHtml(skill.name)}">
              ⚡ ${escapeHtml(skill.name)}
            </span>
            <span class="text-muted small" title="Количество файлов">
              <i class="bi bi-files"></i> ${skill.files_count || 1}
            </span>
          </div>
          <div class="card-body py-2">
            <p class="card-text text-light small mb-2 text-truncate-3" style="min-height: 40px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;" title="${escapeHtml(skill.description)}">
              ${escapeHtml(skill.description || 'Описание отсутствует')}
            </p>
            <div class="mb-2 text-truncate">
              <small class="text-secondary font-monospace"><i class="bi bi-folder"></i> ${escapeHtml(skill.relative_path)}</small>
            </div>
            <div class="d-flex flex-wrap gap-1">
              ${badges.join('')}
            </div>
          </div>
          <div class="card-footer border-secondary bg-black bg-opacity-25 py-2 d-flex justify-content-between align-items-center">
            <button type="button" class="btn btn-sm btn-outline-primary d-flex align-items-center gap-1" onclick="window.skillsTab?.openSkillDetails('${escapeHtml(skill.name)}')">
              <i class="bi bi-pencil-square"></i> Детали
            </button>
            <div class="btn-group btn-group-sm">
              <button type="button" class="btn btn-outline-info" title="Собрать .skill архив" onclick="window.skillsTab?.packageSkill('${escapeHtml(skill.name)}')">
                <i class="bi bi-box-seam"></i>
              </button>
              <button type="button" class="btn btn-outline-danger" title="Удалить навык" onclick="window.skillsTab?.deleteSkill('${escapeHtml(skill.name)}')">
                <i class="bi bi-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  renderTableRow(skill) {
    const escapeHtml = str => String(str || '').replace(/[&<>'"]/g, tag => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
    }[tag] || tag));

    const badges = [];
    if (skill.has_scripts) badges.push('<span class="badge bg-info-subtle text-info border border-info-subtle small me-1">scripts</span>');
    if (skill.has_references) badges.push('<span class="badge bg-warning-subtle text-warning border border-warning-subtle small me-1">refs</span>');
    if (skill.has_dist) badges.push('<span class="badge bg-success-subtle text-success border border-success-subtle small me-1">.skill</span>');

    return `
      <tr>
        <td>
          <span class="badge bg-primary font-monospace fs-6">⚡ ${escapeHtml(skill.name)}</span>
        </td>
        <td>
          <div class="small text-light text-truncate" style="max-width: 350px;" title="${escapeHtml(skill.description)}">
            ${escapeHtml(skill.description || '—')}
          </div>
        </td>
        <td>
          <code class="small text-secondary">${escapeHtml(skill.relative_path)}</code>
        </td>
        <td>
          ${badges.length ? badges.join('') : '<span class="text-muted small">—</span>'}
        </td>
        <td style="text-align: right;">
          <div class="btn-group btn-group-sm">
            <button type="button" class="btn btn-outline-primary" title="Открыть детали" onclick="window.skillsTab?.openSkillDetails('${escapeHtml(skill.name)}')">
              <i class="bi bi-pencil-square"></i> Детали
            </button>
            <button type="button" class="btn btn-outline-info" title="Собрать архив" onclick="window.skillsTab?.packageSkill('${escapeHtml(skill.name)}')">
              <i class="bi bi-box-seam"></i>
            </button>
            <button type="button" class="btn btn-outline-danger" title="Удалить" onclick="window.skillsTab?.deleteSkill('${escapeHtml(skill.name)}')">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }

  async openSkillDetails(name) {
    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}`);
      if (!res.ok) throw new Error(`Failed to load skill details: ${res.statusText}`);
      const data = await res.json();
      this.currentSkill = data.skill;

      // Populate modal fields
      document.getElementById('detail-skill-title').textContent = this.currentSkill.name;
      document.getElementById('detail-skill-path').textContent = this.currentSkill.relative_path;
      document.getElementById('detail-skill-desc-input').value = this.currentSkill.description || '';
      document.getElementById('detail-skill-instructions').value = this.currentSkill.instructions || '';
      document.getElementById('detail-skill-readme').value = this.currentSkill.readme_raw || '';

      // Populate files list
      const filesContainer = document.getElementById('detail-files-list');
      if (filesContainer) {
        if (this.currentSkill.files && this.currentSkill.files.length > 0) {
          filesContainer.innerHTML = this.currentSkill.files.map(f => `
            <div class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center py-1 small">
              <span><i class="bi bi-file-earmark text-secondary"></i> ${f.rel_path}</span>
              <span class="badge bg-secondary font-monospace">${this.formatBytes(f.size)}</span>
            </div>
          `).join('');
        } else {
          filesContainer.innerHTML = '<div class="text-muted small py-2">Файлы отсутствуют</div>';
        }
      }

      // Populate JSON contract
      const contractEl = document.getElementById('detail-json-contract');
      if (contractEl) {
        const contractObj = {
          name: this.currentSkill.name,
          description: this.currentSkill.description,
          metadata: this.currentSkill.metadata,
          manifest: this.currentSkill.manifest,
        };
        contractEl.textContent = JSON.stringify(contractObj, null, 2);
      }

      // Hide alerts
      const alertEl = document.getElementById('detail-skill-alert');
      if (alertEl) alertEl.classList.add('d-none');

      // Show modal
      const modalEl = document.getElementById('skillDetailsModal');
      const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
      modal.show();
    } catch (err) {
      console.error('[SkillsTab] Details error:', err);
      alert(`Ошибка открытия деталей навыка: ${err.message}`);
    }
  }

  async saveCurrentSkill() {
    if (!this.currentSkill) return;
    const spinner = document.getElementById('save-skill-spinner');
    const alertEl = document.getElementById('detail-skill-alert');

    spinner?.classList.remove('d-none');
    try {
      const description = document.getElementById('detail-skill-desc-input').value.trim();
      const instructions = document.getElementById('detail-skill-instructions').value;
      const readme = document.getElementById('detail-skill-readme').value;

      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(this.currentSkill.name)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description, instructions, readme })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      if (alertEl) {
        alertEl.className = 'alert alert-success py-2 mt-3 mb-0';
        alertEl.textContent = '✅ Изменения успешно сохранены';
        alertEl.classList.remove('d-none');
      }

      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Save error:', err);
      if (alertEl) {
        alertEl.className = 'alert alert-danger py-2 mt-3 mb-0';
        alertEl.textContent = `Ошибка сохранения: ${err.message}`;
        alertEl.classList.remove('d-none');
      }
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  async createSkill() {
    const nameInput = document.getElementById('new-skill-name');
    const descInput = document.getElementById('new-skill-desc');
    const dirSelect = document.getElementById('new-skill-dir');
    const instructionsInput = document.getElementById('new-skill-instructions');
    const spinner = document.getElementById('create-skill-spinner');
    const alertEl = document.getElementById('create-skill-alert');

    const name = nameInput?.value.trim().toLowerCase();
    if (!name) {
      if (alertEl) {
        alertEl.className = 'alert alert-danger py-2 mb-0';
        alertEl.textContent = 'Укажите имя навыка';
        alertEl.classList.remove('d-none');
      }
      return;
    }

    spinner?.classList.remove('d-none');
    try {
      const res = await this.apiFetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          description: descInput?.value.trim() || '',
          target_dir: dirSelect?.value || '.agents/skills',
          instructions: instructionsInput?.value.trim() || ''
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      const modalEl = document.getElementById('createSkillModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal?.hide();

      // Reset form
      document.getElementById('create-skill-form')?.reset();
      if (alertEl) alertEl.classList.add('d-none');

      await this.refresh();
      // Open details for the new skill
      await this.openSkillDetails(name);
    } catch (err) {
      console.error('[SkillsTab] Create error:', err);
      if (alertEl) {
        alertEl.className = 'alert alert-danger py-2 mb-0';
        alertEl.textContent = `Ошибка создания навыка: ${err.message}`;
        alertEl.classList.remove('d-none');
      }
    } finally {
      spinner?.classList.add('d-none');
    }
  }

  async packageSkill(name) {
    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}/package`, {
        method: 'POST'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }
      const data = await res.json();
      alert(`✅ Навык '${name}' успешно упакован в архив:\n${data.archive?.path} (${this.formatBytes(data.archive?.size)})`);
      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Package error:', err);
      alert(`Ошибка сборки архива: ${err.message}`);
    }
  }

  async packageCurrentSkill() {
    if (!this.currentSkill) return;
    await this.packageSkill(this.currentSkill.name);
    // Refresh modal details
    await this.openSkillDetails(this.currentSkill.name);
  }

  async deleteSkill(name) {
    if (!confirm(`Вы действительно хотите удалить навык '${name}' и все его файлы? Это действие необратимо.`)) {
      return;
    }

    try {
      const res = await this.apiFetch(`/api/skills/${encodeURIComponent(name)}`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || res.statusText);
      }

      // Close modal if open
      const modalEl = document.getElementById('skillDetailsModal');
      const modal = bootstrap.Modal.getInstance(modalEl);
      modal?.hide();

      await this.refresh();
    } catch (err) {
      console.error('[SkillsTab] Delete error:', err);
      alert(`Ошибка удаления навыка: ${err.message}`);
    }
  }

  async deleteCurrentSkill() {
    if (!this.currentSkill) return;
    await this.deleteSkill(this.currentSkill.name);
  }

  showLoading(show) {
    const loadingEl = document.getElementById('skills-loading');
    if (loadingEl) {
      if (show) loadingEl.classList.remove('d-none');
      else loadingEl.classList.add('d-none');
    }
  }

  showAlert(message, type = 'info') {
    alert(message);
  }

  formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }
}

// Global initialization hook
window.SkillsTabManager = SkillsTabManager;
if (!window.skillsTab) {
  window.skillsTab = new SkillsTabManager();
}
window.initSkillsTab = function() {
  if (window.skillsTab) {
    window.skillsTab.init();
  }
};

// Auto-init on script load if container is present
if (document.getElementById('skills-tab-root')) {
  window.skillsTab.init();
}


