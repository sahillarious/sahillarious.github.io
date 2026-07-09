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
   CONTACT FORM → MAILTO
   ============================================================ */
(function () {
  const form = document.getElementById('contactForm');
  if (!form) return;

  const TO_EMAIL = 'sahilshivajisawant@gmail.com';

  function validate() {
    let ok = true;
    ['contact-name', 'contact-email', 'contact-message'].forEach(id => {
      const el = document.getElementById(id);
      if (!el) return;
      const empty = !el.value.trim();
      const badEmail = id === 'contact-email' && el.value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(el.value);
      const invalid = empty || badEmail;
      el.classList.toggle('invalid', invalid);
      el.setAttribute('aria-invalid', String(invalid));
      if (invalid) ok = false;
    });
    return ok;
  }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!validate()) return;

    const name    = document.getElementById('contact-name').value.trim();
    const email   = document.getElementById('contact-email').value.trim();
    const message = document.getElementById('contact-message').value.trim();

    const subject = encodeURIComponent(`Portfolio contact from ${name}`);
    const body    = encodeURIComponent(
      `Name: ${name}\nEmail: ${email}\n\n${message}`
    );

    window.location.href = `mailto:${TO_EMAIL}?subject=${subject}&body=${body}`;
  });

  // Clear invalid styling on input
  form.querySelectorAll('.form-input').forEach(el => {
    el.addEventListener('input', () => {
      el.classList.remove('invalid');
      el.removeAttribute('aria-invalid');
    });
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

  /* ── Knowledge base ─────────────────────────────────────── */
  const KB = [
    {
      keys: ['hello', 'hi', 'hey', 'howdy', 'sup', 'hiya', 'greetings'],
      reply: `Hey there! 🐱 I'm Casper — Ask me about Sahil's projects, work experience, skills, or how to get in touch. What would you like to know?`
    },
    {
      keys: ['who are you', 'what are you', 'what can you do', 'help', 'about you', 'casper'],
      reply: `I'm Casper 🐱 — named after Sahil's real cat! I'm a portfolio assistant that can tell you about Sahil's AI/ML projects, work history, tech skills, or education. Try asking: <em>"What projects has he built?"</em> or <em>"What's his tech stack?"</em>`
    },
    {
      keys: ['project', 'built', 'build', 'made', 'github', 'portfolio', 'code', 'what has he'],
      reply: `Sahil's featured projects:<br><br>
<strong>01 · BOLT</strong> — Real-time ball tracking on a Unitree Go2 quadruped. YOLOv8 + Intel RealSense on Jetson, with Kalman-filter occlusion-aware re-ID.<br><br>
<strong>02 · Buffalo Accident Risk</strong> — PPO reinforcement learning agent for emergency resource allocation across Buffalo, NY. Outperformed random baseline by ~9,000 reward points.<br><br>
<strong>03 · DeepSpeech</strong> — Speech therapy assessment system. 1D Conv Autoencoder hits 96.89% accuracy; GPT-4 coaches users on articulation and stuttering.<br><br>
<strong>04 · DermAI</strong> — Ensemble skin lesion classifier (ResNet50 + DenseNet + VGG-19 + EfficientNet) on HAM10000 — 94% precision vs 88% single-model baseline.<br><br>
Want details on any of these?`
    },
    {
      keys: ['bolt', 'robot', 'quadruped', 'yolov', 'realsense', 'jetson', 'ball track'],
      reply: `<strong>BOLT</strong> is a real-time ball tracking system built for the Unitree Go2 quadruped robot. It runs YOLOv8 for detection and an Intel RealSense depth camera on an NVIDIA Jetson edge device. Sahil added occlusion-aware re-identification using a Kalman filter so the robot keeps tracking the ball even when it briefly disappears — important for smooth, reactive legged-robot motion. This was built during his Graduate Research Assistant role at UB.`
    },
    {
      keys: ['buffalo', 'accident', 'risk', 'ppo', 'reinforcement', 'rl', 'emergency', 'dispatch', 'resource alloc'],
      reply: `<strong>Buffalo Accident Risk & Resource Allocation</strong> uses Proximal Policy Optimization (PPO) to dynamically dispatch Police, EMS, and DOT resources across a 145-cell grid of Buffalo, NY. Trained on ~10,000 annual traffic incidents from Buffalo's Open Data Portal. The PPO agent scored ~793 episode reward vs. −8,170 for random and −47,500 for DQN. Built with PyTorch. Check it out on <a href="https://github.com/sahillarious/Buffalo-Accident-Risk-Prediction-Resource-Allocation" target="_blank" rel="noopener">GitHub ↗</a>`
    },
    {
      keys: ['deepspeech', 'speech', 'stutter', 'therapy', 'articulation', 'librispeech', 'sep-28k'],
      reply: `<strong>DeepSpeech</strong> is a speech therapy assessment system built with PyTorch. It uses a 1D Convolutional Autoencoder trained on LibriSpeech — flags faulty speech by measuring reconstruction error against a dynamic threshold, reaching 96.89% accuracy. A separate multi-model system on SEP-28k handles stuttering detection (blocks, prolongations, repetitions). A GPT-4 virtual coach deployed via Gradio gives personalised corrective feedback. GitHub: <a href="https://github.com/sahillarious/DeepSpeech" target="_blank" rel="noopener">DeepSpeech ↗</a>`
    },
    {
      keys: ['dermai', 'derm', 'skin', 'lesion', 'ham10000', 'dermatology', 'ensemble', 'resnet', 'efficientnet'],
      reply: `<strong>DermAI</strong> is an ensemble diagnostic system for skin disease classification across 7 lesion types using the HAM10000 dataset. It combines ResNet50, DenseNet121, VGG-19, and EfficientNet-B0 — reaching 94% precision vs. 88% for any single model. SMOTE handles severe class imbalance. GPT-4 generates interpretable, clinically-framed explanations for each prediction. GitHub: <a href="https://github.com/sahillarious/DermAI" target="_blank" rel="noopener">DermAI ↗</a>`
    },
    {
      keys: ['experience', 'work', 'job', 'company', 'career', 'employ', 'arta', 'capgemini', 'internship'],
      reply: `Sahil's work history:<br><br>
<strong>AI Engineer @ Arta Support</strong> (Mar–May 2026) — Built <em>zcopilot-server</em>, a production multi-agent copilot with per-session state isolation over Socket.IO. Designed a SQLite→DynamoDB dual-write token accounting system and deployed across AWS us-west-1 + us-east-2 with Cognito auth and KMS-backed HMAC signing.<br><br>
<strong>Graduate Research Assistant @ UB</strong> (Aug–Dec 2025) — The BOLT robotics project; real-time tracking on the Unitree Go2.<br><br>
<strong>Analyst @ Capgemini</strong> (Dec 2022–May 2024) — Oracle EBS, SQL/PL-SQL development, and job automation with AppWorx in Mumbai.`
    },
    {
      keys: ['arta', 'copilot', 'zcopilot', 'agent', 'agentic', 'multi-agent', 'socket'],
      reply: `At <strong>Arta Support</strong>, Sahil built <em>zcopilot-server</em> — a production agentic copilot backend. Key details:<br>
• Multi-agent orchestration with scope-aware reasoning<br>
• Per-session state isolation using Socket.IO<br>
• Token accounting: SQLite → DynamoDB dual-write for multi-region cost tracking<br>
• Superadmin dashboard aggregating costs across regions<br>
• Deployed in AWS us-west-1 (primary) and us-east-2 (secondary) with Cognito + KMS-backed HMAC`
    },
    {
      keys: ['skill', 'tech', 'stack', 'language', 'framework', 'tool', 'know', 'use', 'familiar'],
      reply: `Sahil's tech stack:<br><br>
<strong>Languages:</strong> Python, SQL / PL-SQL<br>
<strong>Agents & LLMs:</strong> LangGraph, LangChain, LlamaIndex, CrewAI, Pydantic AI, FastAPI<br>
<strong>Retrieval & data:</strong> Neo4j, Qdrant, FAISS, Pinecone, DynamoDB, SQLite<br>
<strong>Cloud & infra:</strong> AWS (SageMaker, Cognito, EC2, KMS), Docker, GitHub Actions, Oracle Cloud<br>
<strong>ML & systems:</strong> RAG, GraphRAG, Multi-agent orchestration, YOLOv8, Computer Vision, Socket.IO, PySpark`
    },
    {
      keys: ['langgraph', 'langchain', 'llamaindex', 'crewai', 'rag', 'retrieval', 'vector', 'embedding'],
      reply: `Sahil works extensively with the LangGraph / LangChain ecosystem for agentic pipelines, LlamaIndex for retrieval, and CrewAI for multi-agent orchestration. On the retrieval side he's used Qdrant, FAISS, Pinecone, and Neo4j for graph-structured RAG. He's shipped these in production (Arta Support) and in research projects.`
    },
    {
      keys: ['aws', 'cloud', 'docker', 'deploy', 'cognito', 'dynamo', 'sagemaker', 'kms', 'ec2'],
      reply: `Sahil has production AWS experience: multi-region deployment (us-west-1 + us-east-2), Cognito for authentication, DynamoDB for persistent state, KMS for HMAC signing, and EC2 for hosting. He also uses Docker for containerisation, GitHub Actions for CI, and Oracle Cloud (free tier) for personal project hosting.`
    },
    {
      keys: ['education', 'degree', 'university', 'study', 'school', 'ms', 'master', 'bachelor', 'ub', 'buffalo'],
      reply: `<strong>MS in Artificial Intelligence</strong> — University at Buffalo, SUNY (Aug 2024 – Dec 2025). Coursework: Deep Learning, NLP, Computer Vision, Reinforcement Learning, LLMs, Robotics.<br><br><strong>BE in Electronics & Telecommunication</strong> — University of Mumbai (Aug 2018 – May 2022).`
    },
    {
      keys: ['contact', 'email', 'reach', 'hire', 'available', 'open to', 'linkedin', 'connect', 'recruiter'],
      reply: `Sahil is open to AI Engineer roles! Best ways to reach him:<br><br>
📧 <a href="mailto:sahilshivajisawant@gmail.com">sahilshivajisawant@gmail.com</a><br>
💼 <a href="https://www.linkedin.com/in/sahilsawant01/" target="_blank" rel="noopener">LinkedIn ↗</a><br>
🐙 <a href="https://github.com/sahillarious" target="_blank" rel="noopener">GitHub ↗</a><br>
📄 <a href="assets/Sahil%20Sawant%20Resume.pdf" download="Sahil Sawant Resume.pdf">Download Resume</a>`
    },
    {
      keys: ['resume', 'cv', 'download'],
      reply: `You can download Sahil's resume here: <a href="assets/Sahil%20Sawant%20Resume.pdf" download="Sahil Sawant Resume.pdf">📄 Sahil Sawant Resume.pdf</a>`
    },
    {
      keys: ['location', 'where', 'based', 'buffalo', 'ny', 'new york', 'india', 'mumbai'],
      reply: `Sahil is currently based in Buffalo, NY (originally from Mumbai, India). He's open to remote roles and on-site positions.`
    },
    {
      keys: ['thank', 'thanks', 'awesome', 'great', 'cool', 'nice', 'good job', 'perfect', 'helpful'],
      reply: `Happy to help! 🐱 Anything else you'd like to know about Sahil?`
    },
    {
      keys: ['bye', 'goodbye', 'later', 'see you', 'cya', 'take care'],
      reply: `Catch you later! 🐾 Feel free to come back if you have more questions.`
    },
  ];

  const FALLBACK = [
    `Hmm, I'm not sure about that one. 🐱 Try asking about Sahil's <strong>projects</strong>, <strong>experience</strong>, <strong>skills</strong>, or <strong>contact info</strong>!`,
    `That's outside my knowledge base. 🐱 I know a lot about Sahil's work though — ask me about his projects or tech stack!`,
    `I'm a portfolio assistant, not a general AI — so I'm best at questions about Sahil! Try: <em>"What's his tech stack?"</em> or <em>"Tell me about his experience."</em> 🐾`,
  ];
  let fallbackIdx = 0;

  function findReply(text) {
    const lower = text.toLowerCase();
    for (const entry of KB) {
      if (entry.keys.some(k => lower.includes(k))) return entry.reply;
    }
    const r = FALLBACK[fallbackIdx % FALLBACK.length];
    fallbackIdx++;
    return r;
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

  function showTyping() {
    const row = document.createElement('div');
    row.className = 'casper-msg casper-msg-bot';
    row.id = 'casperTyping';
    row.innerHTML = `<div class="casper-typing-indicator"><span></span><span></span><span></span></div>`;
    feed.appendChild(row);
    feed.scrollTop = feed.scrollHeight;
  }

  function removeTyping() {
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
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    appendMsg(text, 'user');

    const sendBtn = form.querySelector('.casper-send');
    sendBtn.disabled = true;
    showTyping();

    const delay = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 600 + Math.random() * 400;
    setTimeout(() => {
      removeTyping();
      appendMsg(findReply(text), 'bot');
      sendBtn.disabled = false;
      input.focus();
    }, delay);
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
