/* ============================================================
   HERO ROLE ROTATOR
   ============================================================ */
(function () {
  const el = document.getElementById('roleRotator');
  if (!el) return;

  const roles = ['AI Engineer', 'ML Engineer', 'Software Engineer', 'Data Scientist'];
  let i = 0;

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  setInterval(() => {
    i = (i + 1) % roles.length;
    if (reduced) {
      el.textContent = roles[i];
      return;
    }
    el.classList.add('is-swapping');
    setTimeout(() => {
      el.textContent = roles[i];
      el.classList.remove('is-swapping');
    }, 300);
  }, 2400);
})();


/* ============================================================
   THEME TOGGLE (light ↔ dark, persisted in localStorage)
   ============================================================ */
(function () {
  const html = document.documentElement;
  const btn  = document.getElementById('themeToggle');
  if (!btn) return;

  const saved = localStorage.getItem('theme');
  if (saved === 'dark') html.setAttribute('data-theme', 'dark');

  btn.addEventListener('click', () => {
    const isDark = html.getAttribute('data-theme') === 'dark';
    if (isDark) {
      html.removeAttribute('data-theme');
      localStorage.setItem('theme', 'light');
    } else {
      html.setAttribute('data-theme', 'dark');
      localStorage.setItem('theme', 'dark');
    }
  });
})();


/* ============================================================
   GRAPH-NODE CANVAS ANIMATION
   ============================================================ */
(function () {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const NODE_COUNT   = 60;
  const CONNECT_DIST = 140;
  const NODE_SPEED   = 0.28;
  const NODE_RADIUS  = 2.5;

  function getNodeColor() {
    return (getComputedStyle(document.documentElement)
      .getPropertyValue('--node-color-rgb').trim()) || '94, 114, 53';
  }
  let OLIVE = getNodeColor();

  // Re-read node color when theme changes
  new MutationObserver(() => { OLIVE = getNodeColor(); })
    .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

  let nodes = [];
  let rafId = null;
  let W, H;

  function resize() {
    W = canvas.offsetWidth;
    H = canvas.offsetHeight;
    canvas.width  = W * devicePixelRatio;
    canvas.height = H * devicePixelRatio;
    ctx.scale(devicePixelRatio, devicePixelRatio);
  }

  function makeNode() {
    const angle = Math.random() * Math.PI * 2;
    return {
      x:     Math.random() * W,
      y:     Math.random() * H,
      vx:    Math.cos(angle) * NODE_SPEED * (0.4 + Math.random() * 0.6),
      vy:    Math.sin(angle) * NODE_SPEED * (0.4 + Math.random() * 0.6),
      r:     NODE_RADIUS * (0.6 + Math.random() * 0.8),
      alpha: 0.5 + Math.random() * 0.5,
    };
  }

  function init() {
    resize();
    nodes = Array.from({ length: NODE_COUNT }, makeNode);
  }

  function drawFrame() {
    ctx.clearRect(0, 0, W, H);

    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx   = nodes[i].x - nodes[j].x;
        const dy   = nodes[i].y - nodes[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < CONNECT_DIST) {
          const opacity = (1 - dist / CONNECT_DIST) * 0.22;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(100, 88, 65, ${opacity})`;
          ctx.lineWidth   = 0.8;
          ctx.moveTo(nodes[i].x, nodes[i].y);
          ctx.lineTo(nodes[j].x, nodes[j].y);
          ctx.stroke();
        }
      }
    }

    for (const n of nodes) {
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${OLIVE}, ${n.alpha * 0.85})`;
      ctx.fill();

      const grd = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.r * 4);
      grd.addColorStop(0, `rgba(${OLIVE}, 0.14)`);
      grd.addColorStop(1, `rgba(${OLIVE}, 0)`);
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.r * 4, 0, Math.PI * 2);
      ctx.fillStyle = grd;
      ctx.fill();
    }
  }

  function step() {
    for (const n of nodes) {
      n.x += n.vx;
      n.y += n.vy;
      if (n.x < -20)    n.x = W + 20;
      if (n.x > W + 20) n.x = -20;
      if (n.y < -20)    n.y = H + 20;
      if (n.y > H + 20) n.y = -20;
    }
    drawFrame();
    rafId = requestAnimationFrame(step);
  }

  init();

  if (prefersReducedMotion) {
    drawFrame();
  } else {
    rafId = requestAnimationFrame(step);
  }

  const ro = new ResizeObserver(() => {
    if (rafId) cancelAnimationFrame(rafId);
    resize();
    if (!prefersReducedMotion) {
      rafId = requestAnimationFrame(step);
    } else {
      drawFrame();
    }
  });
  ro.observe(canvas);
})();




/* ============================================================
   ACTIVE NAV LINK (scroll spy)
   ============================================================ */
(function () {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.pill-nav-link');
  if (!sections.length || !navLinks.length) return;

  const NAV_H = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h')) || 64;

  function setActive() {
    let current = '';
    sections.forEach(sec => {
      if (window.scrollY >= sec.offsetTop - NAV_H - 20) {
        current = sec.getAttribute('id');
      }
    });
    navLinks.forEach(link => {
      const section = link.getAttribute('data-section');
      const href    = link.getAttribute('href');
      const match   = section ? section === current : href === `#${current}`;
      link.classList.toggle('active', match);
    });
  }

  window.addEventListener('scroll', setActive, { passive: true });
  setActive();
})();


/* ============================================================
   SCROLL REVEAL
   ============================================================ */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const targets = document.querySelectorAll(
    '.timeline-card, .project-card, .skill-group, .edu-card, .about-grid, .contact-grid'
  );

  const io = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  targets.forEach((el, i) => {
    el.classList.add('reveal');
    el.style.transitionDelay = `${Math.min(i * 60, 300)}ms`;
    io.observe(el);
  });
})();


/* ============================================================
   FOOTER YEAR
   ============================================================ */
(function () {
  const el = document.getElementById('footerYear');
  if (el) el.textContent = new Date().getFullYear();
})();


/* ============================================================
   CASPER — PORTFOLIO CHAT ASSISTANT
   ============================================================ */
(function () {
  const toggle  = document.getElementById('casperToggle');
  const panel   = document.getElementById('casperPanel');
  const closeBtn= document.getElementById('casperClose');
  const form    = document.getElementById('casperForm');
  const input   = document.getElementById('casperInput');
  const feed    = document.getElementById('casperMessages');
  const badge   = document.getElementById('casperBadge');
  if (!toggle || !panel) return;

  /* ── Backend ────────────────────────────────────────────── */
  // Casper talks to a Cloudflare Worker that calls the Claude API server-side
  // (the API key never touches the browser). Deploy casper-worker/ and paste
  // its URL here — see casper-worker/README.md.
  const WORKER_URL = 'https://casper-worker.sahillarious.workers.dev';

  // Conversation history sent to the Worker (user/assistant turns only).
  const history = [];
  const MAX_TURNS = 12;

  async function askCasper(text) {
    history.push({ role: 'user', content: text });
    if (history.length > MAX_TURNS) history.splice(0, history.length - MAX_TURNS);

    const res = await fetch(WORKER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: history }),
    });
    if (!res.ok) throw new Error(`Casper backend returned ${res.status}`);

    const data = await res.json();
    const reply = (data && data.reply) ? data.reply
      : "Sorry, I couldn't come up with a response.";
    history.push({ role: 'assistant', content: reply });
    return reply;
  }

  // Escape untrusted text before it touches the DOM.
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // Render the small subset of Markdown the model uses (bold, bullets, links,
  // line breaks) into safe HTML. Everything is escaped first, so no injection.
  function inlineMd(s) {
    return escapeHtml(s)
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(
        /\[([^\]]+)\]\((https?:\/\/[^\s)]+|mailto:[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>'
      );
  }

  function renderReply(text) {
    const lines = String(text).split('\n');
    let html = '';
    let inList = false;
    for (const raw of lines) {
      const line = raw.replace(/\s+$/, '');
      const bullet = line.trim().match(/^[-*•]\s+(.*)$/);
      if (bullet) {
        if (!inList) { html += '<ul class="casper-list">'; inList = true; }
        html += `<li>${inlineMd(bullet[1])}</li>`;
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        if (line.trim() !== '') html += `${inlineMd(line)}<br>`;
      }
    }
    if (inList) html += '</ul>';
    return html.replace(/(<br>)+$/, '');
  }

  /* ── UI helpers ─────────────────────────────────────────── */
  function appendMsg(html, role) {
    const row = document.createElement('div');
    row.className = `casper-msg casper-msg-${role}`;
    const bubble = document.createElement('div');
    bubble.className = 'casper-msg-bubble';
    if (role === 'user') {
      bubble.textContent = html;
    } else {
      bubble.innerHTML = html;
    }
    row.appendChild(bubble);
    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;
    return row;
  }

  // Cat faces cycled through while Casper is "thinking".
  const CAT_FACES = [
    'assets/cat1.png',
    'assets/cat12.png',
    'assets/cat3.png',
    'assets/cat4.png',
    'assets/cat5.png',
    'assets/cat6.png',
  ];
  CAT_FACES.forEach((src) => { const im = new Image(); im.src = src; }); // preload for smooth cycling
  let typingTimer = null;

  function showTyping() {
    const row = document.createElement('div');
    row.className = 'casper-msg casper-msg-bot';
    row.id = 'casperTyping';

    const img = document.createElement('img');
    img.className = 'casper-typing-cat';
    img.alt = 'Casper is thinking…';
    let i = Math.floor(Math.random() * CAT_FACES.length);
    img.src = CAT_FACES[i];
    row.appendChild(img);
    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;

    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!reduce) {
      typingTimer = setInterval(() => {
        i = (i + 1) % CAT_FACES.length;
        img.src = CAT_FACES[i];
      }, 450);
    }
  }

  function removeTyping() {
    if (typingTimer) { clearInterval(typingTimer); typingTimer = null; }
    const el = document.getElementById('casperTyping');
    if (el) el.remove();
  }

  /* ── Open / close ───────────────────────────────────────── */
  function openPanel() {
    panel.setAttribute('aria-hidden', 'false');
    toggle.setAttribute('aria-expanded', 'true');
    badge.hidden = true;
    input.focus();
  }

  function closePanel() {
    panel.setAttribute('aria-hidden', 'true');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.focus();
  }

  toggle.addEventListener('click', () => {
    const isOpen = panel.getAttribute('aria-hidden') === 'false';
    isOpen ? closePanel() : openPanel();
  });
  closeBtn.addEventListener('click', closePanel);

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && panel.getAttribute('aria-hidden') === 'false') closePanel();
  });

  /* ── Send message ───────────────────────────────────────── */
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    appendMsg(text, 'user');

    const sendBtn = form.querySelector('.casper-send');
    sendBtn.disabled = true;
    showTyping();

    try {
      const reply = await askCasper(text);
      removeTyping();
      appendMsg(renderReply(reply), 'bot');
    } catch (err) {
      removeTyping();
      appendMsg(
        "I'm having trouble reaching my brain right now 🐱 — please try again in a moment, or email Sahil at <a href=\"mailto:sahilshivajisawant@gmail.com\">sahilshivajisawant@gmail.com</a>.",
        'bot'
      );
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  });

  /* ── Trap focus inside panel when open ─────────────────── */
  panel.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;
    const focusable = [...panel.querySelectorAll('button, input, a[href]')].filter(el => !el.disabled);
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
})();
