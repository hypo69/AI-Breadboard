// News Tab Controller
class NewsTabController {
  constructor() {
    this.articles = [];
    this.profile = null;
    this.currentDigest = null;
    this.isLoading = false;
  }

  async init() {
    console.log('[NewsTab] Initializing Smart News Feed...');
    await this.loadProfile();
    await this.refreshNews(false);
  }

  async loadProfile() {
    try {
      const res = await fetch('/api/news/profile');
      if (res.ok) {
        this.profile = await res.json();
        this.renderProfileModal();
      }
    } catch (e) {
      console.error('[NewsTab] Error loading profile:', e);
    }
  }

  renderProfileModal() {
    if (!this.profile) return;
    const container = document.getElementById('news-learned-tags-container');
    if (container) {
      container.innerHTML = '';
      const weights = this.profile.topic_weights || {};
      const sorted = Object.entries(weights).sort((a, b) => b[1] - a[1]);
      if (sorted.length === 0) {
        container.innerHTML = '<span class="text-muted small">Пока нет накопленных весов. Оценивайте новости кнопками 👍 и 👎!</span>';
      } else {
        for (const [kw, w] of sorted) {
          const badge = document.createElement('span');
          badge.className = 'badge bg-secondary border border-secondary text-light d-flex align-items-center gap-1';
          badge.innerHTML = `<span>${kw}</span> <span class="badge bg-primary text-white">${w}</span>`;
          container.appendChild(badge);
        }
      }
    }

    const countLabel = document.getElementById('news-interactions-count-label');
    if (countLabel) {
      countLabel.textContent = `Обработано реакций обучения: ${this.profile.interaction_count || 0}`;
    }

    const negInput = document.getElementById('news-neg-topics-input');
    if (negInput && this.profile.negative_keywords) {
      negInput.value = this.profile.negative_keywords.join(', ');
    }
  }

  async refreshNews(force = false) {
    if (this.isLoading) return;
    this.isLoading = true;
    const container = document.getElementById('news-articles-container');
    const spinner = document.getElementById('news-loading-spinner');
    if (spinner) spinner.classList.remove('d-none');

    try {
      const url = `/api/news/feed?force_refresh=${force}&limit=35`;
      const res = await fetch(url);
      if (res.ok) {
        this.articles = await res.json();
        this.renderArticles();
        const totalBadge = document.getElementById('news-total-badge');
        if (totalBadge) totalBadge.textContent = this.articles.length;
      }
    } catch (e) {
      console.error('[NewsTab] Error fetching feed:', e);
      if (container) {
        container.innerHTML = `<div class="col-12 alert alert-danger">Ошибка загрузки новостей: ${e.message}</div>`;
      }
    } finally {
      this.isLoading = false;
    }
  }

  renderArticles() {
    const container = document.getElementById('news-articles-container');
    if (!container) return;
    container.innerHTML = '';

    const query = (document.getElementById('news-search-input')?.value || '').toLowerCase().trim();
    const cat = document.getElementById('news-category-filter')?.value || 'all';
    const minScore = parseFloat(document.getElementById('news-min-score')?.value || '0');

    const filtered = this.articles.filter((a) => {
      if (cat !== 'all' && a.category !== cat) return false;
      if (a.relevance_score < minScore) return false;
      if (query) {
        const text = `${a.title} ${a.summary} ${a.source_name}`.toLowerCase();
        if (!text.includes(query)) return false;
      }
      return true;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="col-12 text-center text-muted p-5">
          <i class="bi bi-inbox fs-1 mb-2 d-block"></i>
          <h6>Нет новостей, подходящих под выбранные фильтры</h6>
          <small>Попробуйте уменьшить порог минимального совпадения или обновить ленту.</small>
        </div>
      `;
      return;
    }

    filtered.forEach((art) => {
      const col = document.createElement('div');
      col.className = 'col-md-6 col-lg-4';

      const matchPercent = Math.round((art.relevance_score || 0.5) * 100);
      let matchBadgeClass = 'bg-secondary';
      if (matchPercent >= 70) matchBadgeClass = 'bg-success';
      else if (matchPercent >= 45) matchBadgeClass = 'bg-primary';
      else if (matchPercent >= 25) matchBadgeClass = 'bg-info text-dark';

      const isLiked = art.user_interaction === 'like';
      const isDisliked = art.user_interaction === 'dislike';
      const isBookmarked = art.user_interaction === 'bookmark';

      col.innerHTML = `
        <div class="card h-100 bg-dark border-secondary text-white shadow-sm d-flex flex-column" id="news-card-${art.id}">
          <div class="card-header bg-black d-flex justify-content-between align-items-center py-2 border-secondary">
            <span class="badge bg-dark border border-secondary text-info small text-truncate" style="max-width: 130px;">
              ${art.source_name}
            </span>
            <span class="badge ${matchBadgeClass} rounded-pill small" title="Персональная релевантность">
              ${matchPercent}% match
            </span>
          </div>
          <div class="card-body p-3 d-flex flex-column flex-grow-1">
            <h6 class="card-title fw-bold mb-2">
              <a href="${art.link}" target="_blank" rel="noopener noreferrer" class="text-light text-decoration-none hover-primary" onclick="window.newsTab?.onArticleRead('${art.id}', '${encodeURIComponent(art.title)}')">
                ${art.title}
              </a>
            </h6>
            <p class="card-text small text-muted flex-grow-1 mb-3">
              ${art.ai_summary || art.summary || ''}
            </p>
            <div class="d-flex align-items-center justify-content-between mt-auto pt-2 border-top border-secondary-subtle">
              <small class="text-secondary" style="font-size: 0.75rem;">
                <i class="bi bi-clock me-1"></i>${art.published_at || ''}
              </small>
              <div class="btn-group btn-group-sm" role="group">
                <button type="button" class="btn ${isLiked ? 'btn-success' : 'btn-outline-secondary'} py-0 px-2" title="Полезно (обучить алгоритм)" onclick="window.newsTab?.sendFeedback('${art.id}', 'like', '${encodeURIComponent(art.title)}', '${art.category}')">
                  <i class="bi bi-hand-thumbs-up"></i>
                </button>
                <button type="button" class="btn ${isDisliked ? 'btn-danger' : 'btn-outline-secondary'} py-0 px-2" title="Не интересно (понизить тему)" onclick="window.newsTab?.sendFeedback('${art.id}', 'dislike', '${encodeURIComponent(art.title)}', '${art.category}')">
                  <i class="bi bi-hand-thumbs-down"></i>
                </button>
                <button type="button" class="btn ${isBookmarked ? 'btn-warning text-dark' : 'btn-outline-secondary'} py-0 px-2" title="Сохранить в закладки" onclick="window.newsTab?.sendFeedback('${art.id}', 'bookmark', '${encodeURIComponent(art.title)}', '${art.category}')">
                  <i class="bi bi-bookmark"></i>
                </button>
                <button type="button" class="btn btn-outline-info py-0 px-2" title="Сгенерировать AI-выжимку" onclick="window.newsTab?.summarizeArticle('${art.id}')">
                  <i class="bi bi-magic"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
      container.appendChild(col);
    });
  }

  filterNews() {
    this.renderArticles();
  }

  async sendFeedback(articleId, action, titleEncoded, category) {
    const title = decodeURIComponent(titleEncoded || '');
    try {
      const res = await fetch('/api/news/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_id: articleId,
          action: action,
          article_title: title,
          category: category || 'general'
        })
      });

      if (res.ok) {
        // Optimistic UI update
        const art = this.articles.find((a) => a.id === articleId);
        if (art) {
          art.user_interaction = action;
        }
        this.renderArticles();
        await this.loadProfile();
        if (window.showNotification) {
          const msg = action === 'like' ? 'Алгоритм обучен: тема получила приоритет 👍' :
                      action === 'dislike' ? 'Алгоритм обучен: интерес к теме снижен 👎' :
                      action === 'bookmark' ? 'Добавлено в закладки 🔖' : 'Действие сохранено';
          window.showNotification(msg, 'success');
        }
      }
    } catch (e) {
      console.error('[NewsTab] Error sending feedback:', e);
    }
  }

  async onArticleRead(articleId, titleEncoded) {
    const title = decodeURIComponent(titleEncoded || '');
    try {
      await fetch('/api/news/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          article_id: articleId,
          action: 'read',
          article_title: title
        })
      });
    } catch (_) {}
  }

  async summarizeArticle(articleId) {
    const art = this.articles.find((a) => a.id === articleId);
    if (!art) return;

    const card = document.getElementById(`news-card-${articleId}`);
    if (card) {
      const body = card.querySelector('.card-text');
      if (body) {
        body.innerHTML = '<span class="spinner-border spinner-border-sm text-info me-1"></span> Генерация ИИ-выжимки...';
      }
    }

    try {
      const res = await fetch('/api/news/summarize-article', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(art)
      });
      if (res.ok) {
        const data = await res.json();
        art.ai_summary = data.ai_summary;
        this.renderArticles();
      }
    } catch (e) {
      console.error('[NewsTab] Summarize error:', e);
      this.renderArticles();
    }
  }

  async generateDigest() {
    const digestCard = document.getElementById('news-digest-card');
    const digestContent = document.getElementById('news-digest-content');
    const digestTitle = document.getElementById('news-digest-title');

    if (digestCard) digestCard.classList.remove('d-none');
    if (digestContent) {
      digestContent.innerHTML = '<div class="text-center p-3"><span class="spinner-border spinner-border-sm text-warning me-2"></span>Формирование персонализированного дайджеста ИИ...</div>';
    }

    try {
      const res = await fetch('/api/news/digest', { method: 'POST' });
      if (res.ok) {
        this.currentDigest = await res.json();
        if (digestTitle) digestTitle.textContent = this.currentDigest.title || 'ИИ-Дайджест';
        if (digestContent) {
          if (window.marked) {
            digestContent.innerHTML = window.marked.parse(this.currentDigest.digest_text || '');
          } else {
            digestContent.textContent = this.currentDigest.digest_text || '';
          }
        }
      }
    } catch (e) {
      console.error('[NewsTab] Error generating digest:', e);
      if (digestContent) digestContent.textContent = `Ошибка генерации дайджеста: ${e.message}`;
    }
  }

  speakDigest() {
    if (!this.currentDigest || !this.currentDigest.digest_text) return;
    if (window.chatService && typeof window.chatService.speak === 'function') {
      window.chatService.speak(this.currentDigest.digest_text);
    } else {
      const utterance = new SpeechSynthesisUtterance(this.currentDigest.digest_text);
      utterance.lang = 'ru-RU';
      window.speechSynthesis.speak(utterance);
    }
  }

  async savePreferences() {
    const prefInput = document.getElementById('news-pref-topics-input')?.value || '';
    const negInput = document.getElementById('news-neg-topics-input')?.value || '';

    const preferred = prefInput.split(',').map((s) => s.trim()).filter(Boolean);
    const ignored = negInput.split(',').map((s) => s.trim()).filter(Boolean);

    try {
      const res = await fetch('/api/news/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferred_topics: preferred,
          ignored_topics: ignored
        })
      });
      if (res.ok) {
        await this.loadProfile();
        await this.refreshNews(true);
        if (window.showNotification) window.showNotification('Интересы успешно сохранены!', 'success');
        const modalEl = document.getElementById('newsPreferencesModal');
        if (modalEl && window.bootstrap) {
          const modalInstance = window.bootstrap.Modal.getInstance(modalEl);
          if (modalInstance) modalInstance.hide();
        }
      }
    } catch (e) {
      console.error('[NewsTab] Error saving preferences:', e);
    }
  }

  async resetProfile() {
    if (!confirm('Сбросить накопленные веса интересов и начать обучение с чистого листа?')) return;
    try {
      const res = await fetch('/api/news/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preferred_topics: [],
          ignored_topics: []
        })
      });
      if (res.ok) {
        await this.loadProfile();
        await this.refreshNews(true);
        if (window.showNotification) window.showNotification('Профиль обучения сброшен', 'info');
      }
    } catch (e) {
      console.error('[NewsTab] Error resetting profile:', e);
    }
  }
}

window.newsTab = new NewsTabController();

function initNewsTab() {
  if (window.newsTab) {
    window.newsTab.init();
  }
}

window.initNewsTab = initNewsTab;

if (document.getElementById('news-tab-root')) {
  initNewsTab();
}
