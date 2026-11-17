/* Safe, shared rendering for completed translation passages. */
(() => {
  const escapeHTML = text => String(text).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  function render(target, text) {
    text = String(text ?? '');
    if (!window.marked?.parse || !window.marked.Renderer || !window.DOMPurify?.sanitize) {
      target.classList.add('translation-text-fallback');
      target.textContent = text;
      return;
    }
    target.classList.remove('translation-text-fallback');
    try {
      const renderer = new window.marked.Renderer();
      renderer.html = token => escapeHTML(token.text);
      renderer.image = token => escapeHTML(token.text || '');
      const html = window.marked.parse(text, {gfm:true, breaks:false, renderer});
      const fragment = window.DOMPurify.sanitize(html, {
        RETURN_DOM_FRAGMENT:true,
        ALLOWED_TAGS:['p','br','strong','b','em','i','s','del','h1','h2','h3','h4','h5','h6','ul','ol','li','blockquote','pre','code','hr','table','thead','tbody','tr','th','td','a','sub','sup'],
        ALLOWED_ATTR:['href','title','start','colspan','rowspan'],
        ALLOW_DATA_ATTR:false, ALLOW_ARIA_ATTR:false
      });
      for (const link of fragment.querySelectorAll('a')) {
        const href = link.getAttribute('href') || '';
        if (!/^(https?:|mailto:|\/|#)/i.test(href) || /^\/[\/\\]/.test(href)) link.removeAttribute('href');
        else if (/^https?:/i.test(href)) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
      }
      for (const table of fragment.querySelectorAll('table')) {
        const wrap = document.createElement('div');
        wrap.className = 'translation-table'; wrap.tabIndex = 0;
        wrap.setAttribute('role','region'); wrap.setAttribute('aria-label','Tableau défilant horizontalement');
        table.replaceWith(wrap); wrap.append(table);
      }
      target.replaceChildren(fragment);
    } catch (_) { target.classList.add('translation-text-fallback'); target.textContent = text; }
  }
  window.SurvieTranslationText = {render};
})();
