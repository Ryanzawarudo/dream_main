//滑鼠特效腳本：粒子軌跡與月亮游標
(function () {
  const canvas = document.getElementById('particle-canvas');
  const moon = document.getElementById('cursor-moon');
  const meteorLayer = document.getElementById('meteor-layer');
  if (!canvas || !moon) return;

  const ctx = canvas.getContext('2d');

  let mouse = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2,
    moved: false,
  };
  let moonX = mouse.x;
  let moonY = mouse.y;
  const particles = [];

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }

  function spawnParticle(x, y) {
    particles.push({
      x,
      y,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      r: Math.random() * 1.8 + 0.6,
      life: 1,
      maxLife: 1,
      alpha: Math.random() * 0.45 + 0.25,
    });
  }

  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const ease = 0.08;
    moonX += (mouse.x - moonX) * ease;
    moonY += (mouse.y - moonY) * ease;
    moon.style.left = moonX + 'px';
    moon.style.top = moonY + 'px';

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.96;
      p.vy *= 0.96;
      p.life -= 0.015;
      p.alpha = (p.life / p.maxLife) * 0.55;

      if (p.life <= 0) {
        particles.splice(i, 1);
        continue;
      }

      ctx.beginPath();
      ctx.fillStyle = 'rgba(255,255,255,' + p.alpha + ')';
      ctx.shadowBlur = 10;
      ctx.shadowColor = 'rgba(180, 210, 255, 0.9)';
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(animate);
  }

  window.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
    mouse.moved = true;
    spawnParticle(e.clientX, e.clientY);
  });

  window.addEventListener(
    'touchmove',
    (e) => {
      const t = e.touches[0];
      if (!t) return;
      mouse.x = t.clientX;
      mouse.y = t.clientY;
      spawnParticle(t.clientX, t.clientY);
    },
    { passive: true },
  );

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  animate();

  const LANE_COUNT = 5;

  function spawnMeteor(laneIndex) {
    if (!meteorLayer) return;
    const vh = window.innerHeight;
    const vw = window.innerWidth;
    const laneH = vh / LANE_COUNT;
    const startY = laneIndex * laneH + laneH * (0.1 + Math.random() * 0.8);
    const length = 160 + Math.random() * 120;
    const startX = vw + length * 0.3 + Math.random() * 60;
    const angle = -(14 + Math.random() * 12);
    const dur = 2.6 + Math.random() * 0.2;
    const travel = `${-(vw + length * 1.6)}px`;
    const m = document.createElement('div');
    m.className = 'meteor';
    m.style.cssText = `left:${startX}px;top:${startY}px;width:${length}px;--ang:${angle}deg;--travel:${travel};--dur:${dur}s;`;
    meteorLayer.appendChild(m);
    setTimeout(() => m.remove(), (dur + 0.5) * 1000);
  }

  function scheduleLane(i) {
    setTimeout(() => {
      spawnMeteor(i);
      scheduleLane(i);
    }, 2000 + Math.random() * 7000);
  }

  for (let i = 0; i < LANE_COUNT; i++) {
    setTimeout(() => {
      spawnMeteor(i);
      scheduleLane(i);
    }, i * 600 + Math.random() * 800);
  }
})();
