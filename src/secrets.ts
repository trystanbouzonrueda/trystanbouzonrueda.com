// Petits secrets du monde 3D :
// - terminal caché (touche ` / ², ou appui long sur le cartouche du nom) : whoami, ls, nmap, ssh… et raccourcis vers les rubriques ;
// - code Konami (↑↑↓↓←→←→BA) : feu d'artifice sur le Vieux-Port ;
// - chasse aux trésors : 5 objets d'informaticien cachés dans la ville, progression gardée dans le navigateur.
import * as THREE from 'three';
import { PLACES } from './config';
import { lang, t } from './i18n';

// ---------- message éphémère (même pastille que « Adresse copiée »)
export function toast(text: string, ms = 2300): void {
  document.querySelectorAll('.toast').forEach((x) => x.remove());
  const el = Object.assign(document.createElement('div'), { className: 'toast', textContent: text, role: 'status' });
  el.style.animationDuration = `${ms}ms`;
  document.body.append(el);
  setTimeout(() => el.remove(), ms + 100);
}

// ---------- code Konami
export function onKonami(cb: () => void): void {
  const seq = ['arrowup', 'arrowup', 'arrowdown', 'arrowdown', 'arrowleft', 'arrowright', 'arrowleft', 'arrowright', 'b', 'a'];
  let i = 0;
  addEventListener('keydown', (e) => {
    if (e.target instanceof HTMLInputElement) return;
    const k = e.key.toLowerCase();
    i = k === seq[i] ? i + 1 : k === seq[0] ? 1 : 0;
    if (i === seq.length) {
      i = 0;
      cb();
    }
  });
}

// ---------- clics répétés sur un même objet (5 clics en moins de 3 s)
export function multiClick(n = 5, windowMs = 3000): (key: string) => boolean {
  let last = '';
  let times: number[] = [];
  return (key) => {
    const now = performance.now();
    if (key !== last) times = [];
    last = key;
    times = times.filter((x) => now - x < windowMs);
    times.push(now);
    if (times.length >= n) {
      times = [];
      return true;
    }
    return false;
  };
}

// ---------- feu d'artifice
const SPARKS = 900;
export class Feux {
  readonly group = Object.assign(new THREE.Group(), { name: 'feux' });
  private mesh: THREE.InstancedMesh;
  private sparks: { p: THREE.Vector3; v: THREE.Vector3; life: number; max: number; c: THREE.Color }[] = [];
  private rockets: { p: THREE.Vector3; v: THREE.Vector3; fuse: number; c: THREE.Color }[] = [];
  private queue: { at: number; from: THREE.Vector3 }[] = [];
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private s = new THREE.Vector3();
  private clock = 0;

  constructor() {
    // couleurs vives et non éclairées : le bloom de la scène les fait briller (surtout de nuit)
    this.mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.035, 0.035, 0.035), new THREE.MeshBasicMaterial({ toneMapped: false }), SPARKS);
    this.mesh.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(SPARKS * 3), 3);
    this.mesh.count = 0;
    this.mesh.frustumCulled = false;
    this.group.add(this.mesh);
  }

  /** Salve de 7 fusées tirées depuis `from`. */
  show(from: THREE.Vector3): void {
    for (let i = 0; i < 7; i++) this.queue.push({ at: this.clock + i * 0.45 + Math.random() * 0.2, from: from.clone() });
  }

  get active(): boolean {
    return this.queue.length + this.rockets.length + this.sparks.length > 0;
  }

  update(dt: number): void {
    this.clock += dt;
    if (!this.active) {
      this.mesh.count = 0;
      return;
    }
    const PAL = [0xff4d6d, 0xffd166, 0x06d6a0, 0x4cc9f0, 0xf72585, 0xffffff, 0x2a9df4];
    this.queue = this.queue.filter((r) => {
      if (r.at > this.clock) return true;
      const v = new THREE.Vector3((Math.random() - 0.5) * 0.8, 4.0 + Math.random() * 0.9, (Math.random() - 0.5) * 0.8);
      this.rockets.push({ p: r.from.clone(), v, fuse: 0.9 + Math.random() * 0.3, c: new THREE.Color(PAL[Math.floor(Math.random() * PAL.length)]) });
      return false;
    });
    this.rockets = this.rockets.filter((r) => {
      r.v.y -= 2.2 * dt;
      r.p.addScaledVector(r.v, dt);
      this.sparks.push({ p: r.p.clone(), v: new THREE.Vector3(0, -0.2, 0), life: 0.25, max: 0.25, c: new THREE.Color(0xffe2a8) });
      if ((r.fuse -= dt) > 0) return true;
      // explosion : sphère d'étincelles
      for (let k = 0; k < 110; k++) {
        const dir = new THREE.Vector3().randomDirection().multiplyScalar(1.5 + Math.random() * 0.5);
        const life = 1.3 + Math.random() * 0.6;
        this.sparks.push({ p: r.p.clone(), v: dir, life, max: life, c: r.c.clone().offsetHSL(0, 0, (Math.random() - 0.5) * 0.2) });
      }
      return false;
    });
    this.sparks = this.sparks.filter((s) => (s.life -= dt) > 0);
    if (this.sparks.length > SPARKS) this.sparks.splice(0, this.sparks.length - SPARKS);
    let n = 0;
    for (const s of this.sparks) {
      s.v.y -= 0.9 * dt;
      s.v.multiplyScalar(1 - 1.2 * dt); // freinage de l'air
      s.p.addScaledVector(s.v, dt);
      const k = s.life / s.max;
      this.m.compose(s.p, this.q, this.s.setScalar(0.4 + k));
      this.mesh.setMatrixAt(n, this.m);
      this.mesh.setColorAt(n, s.c);
      n++;
    }
    this.mesh.count = n;
    this.mesh.instanceMatrix.needsUpdate = true;
    if (this.mesh.instanceColor) this.mesh.instanceColor.needsUpdate = true;
  }
}

// ---------- chasse aux trésors
export interface Tresor {
  id: string;
  name: { fr: string; en: string };
}
export const TRESORS: Tresor[] = [
  { id: 'cadenas', name: { fr: 'le cadenas (sécurité)', en: 'the padlock (security)' } },
  { id: 'rj45', name: { fr: 'le câble RJ45 (réseau)', en: 'the RJ45 cable (networking)' } },
  { id: 'serveur', name: { fr: 'le serveur (homelab)', en: 'the server (homelab)' } },
  { id: 'usb', name: { fr: 'la clé USB bootable (systèmes)', en: 'the bootable USB stick (systems)' } },
  { id: 'routeur', name: { fr: 'le routeur (infrastructure)', en: 'the router (infrastructure)' } },
];
const T_KEY = 'portfolio.tresors';

function std(color: THREE.ColorRepresentation, emissive = 0): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.55, flatShading: true, emissive: color, emissiveIntensity: emissive });
}
function box(w: number, h: number, d: number, mat: THREE.Material, x = 0, y = 0, z = 0): THREE.Mesh {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  m.castShadow = true;
  return m;
}

/** Objets en blocs francs, même style que la ville (faits main, couleurs unies). Taille ≈ 0,1 unité. */
function makeTresor(id: string): THREE.Group {
  const g = new THREE.Group();
  const led = std(0x39ff88, 1.6);
  switch (id) {
    case 'cadenas': {
      g.add(box(0.1, 0.08, 0.04, std(0xf2b632, 0.15), 0, 0.04, 0));
      const anse = new THREE.Mesh(new THREE.TorusGeometry(0.032, 0.009, 6, 12, Math.PI), std(0xc8ccd2, 0.1));
      anse.position.y = 0.08;
      g.add(anse, box(0.014, 0.024, 0.044, std(0x30343a), 0, 0.04, 0));
      break;
    }
    case 'rj45': {
      const cable = std(0x2a7de1, 0.15);
      g.add(box(0.03, 0.02, 0.16, cable, 0, 0.012, -0.04));
      g.add(box(0.05, 0.03, 0.05, std(0xdfe8ee, 0.25), 0, 0.016, 0.06));
      g.add(box(0.03, 0.01, 0.02, std(0xf2b632, 0.4), 0, 0.034, 0.075));
      break;
    }
    case 'serveur': {
      g.add(box(0.07, 0.16, 0.08, std(0x23262d, 0.05), 0, 0.08, 0));
      for (let i = 0; i < 4; i++) g.add(box(0.012, 0.008, 0.004, i === 2 ? std(0xff8a3d, 1.6) : led, 0.02, 0.03 + i * 0.035, 0.041));
      break;
    }
    case 'usb': {
      g.add(box(0.05, 0.022, 0.1, std(0xe2384f, 0.15), 0, 0.011, 0));
      g.add(box(0.032, 0.014, 0.04, std(0xc8ccd2, 0.15), 0, 0.011, 0.07));
      break;
    }
    case 'routeur': {
      g.add(box(0.13, 0.03, 0.08, std(0xf4f5f7, 0.12), 0, 0.015, 0));
      const ant = std(0x2b2f36);
      g.add(box(0.008, 0.09, 0.008, ant, -0.045, 0.075, -0.03), box(0.008, 0.09, 0.008, ant, 0.045, 0.075, -0.03));
      for (let i = 0; i < 3; i++) g.add(box(0.01, 0.006, 0.004, led, -0.03 + i * 0.03, 0.02, 0.041));
      break;
    }
  }
  // zone cliquable plus large que l'objet (invisible)
  const hit = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 6), new THREE.MeshBasicMaterial({ visible: false }));
  hit.position.y = 0.06;
  hit.name = 'hit';
  g.add(hit);
  return g;
}

export class Tresors {
  readonly group = Object.assign(new THREE.Group(), { name: 'tresors' });
  private items = new Map<string, { obj: THREE.Group; base: number; phase: number; gone: number }>();
  private found: Set<string>;
  private counter: HTMLElement;
  private onChange: (n: number) => void;

  constructor(onChange: (n: number) => void) {
    this.onChange = onChange;
    let saved: string[] = [];
    try {
      saved = JSON.parse(localStorage.getItem(T_KEY) ?? '[]');
    } catch {
      /* stockage indisponible : on repart de zéro */
    }
    this.found = new Set(saved.filter((id) => TRESORS.some((x) => x.id === id)));
    this.counter = document.createElement('div');
    this.counter.className = 'tresor-count glass';
    this.counter.setAttribute('aria-live', 'polite');
    document.body.append(this.counter);
    this.sync();
  }

  get count(): number {
    return this.found.size;
  }

  has(id: string): boolean {
    return this.found.has(id);
  }

  /** Pose chaque trésor (position déjà au sol). */
  place(spots: Record<string, THREE.Vector3>): void {
    TRESORS.forEach((tr, i) => {
      const p = spots[tr.id];
      if (!p) return;
      const obj = makeTresor(tr.id);
      obj.scale.setScalar(1.3);
      obj.position.copy(p);
      obj.userData.tresor = tr.id;
      obj.visible = !this.found.has(tr.id);
      this.group.add(obj);
      this.items.set(tr.id, { obj, base: p.y, phase: i * 1.3, gone: this.found.has(tr.id) ? 1 : 0 });
    });
  }

  pick(raycaster: THREE.Raycaster): string | null {
    const hits = raycaster.intersectObjects([...this.items.values()].filter((x) => x.obj.visible && !this.found.has(x.obj.userData.tresor)).map((x) => x.obj), true);
    let o: THREE.Object3D | null = hits[0]?.object ?? null;
    while (o && !o.userData.tresor) o = o.parent;
    return (o?.userData.tresor as string) ?? null;
  }

  /** Ramasse un trésor ; renvoie true quand c'était le dernier. */
  take(id: string): boolean {
    if (this.found.has(id)) return false;
    this.found.add(id);
    try {
      localStorage.setItem(T_KEY, JSON.stringify([...this.found]));
    } catch {
      /* ignoré */
    }
    this.sync();
    this.onChange(this.found.size);
    return this.found.size === TRESORS.length;
  }

  reset(): void {
    this.found.clear();
    try {
      localStorage.removeItem(T_KEY);
    } catch {
      /* ignoré */
    }
    for (const it of this.items.values()) {
      it.gone = 0;
      it.obj.visible = true;
      it.obj.scale.setScalar(1.3);
    }
    this.sync();
  }

  sync(): void {
    const n = this.found.size;
    this.counter.hidden = n === 0;
    this.counter.title = t('Trésors trouvés', 'Treasures found');
    this.counter.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 10V7a5 5 0 0 1 10 0v3M5 10h14v10H5zM12 14v2"/></svg><span>${n}/${TRESORS.length}</span>`;
    this.counter.setAttribute('aria-label', t(`Trésors trouvés : ${n} sur ${TRESORS.length}`, `Treasures found: ${n} of ${TRESORS.length}`));
    this.counter.classList.toggle('full', n === TRESORS.length);
  }

  update(dt: number, elapsed: number): void {
    for (const [id, it] of this.items) {
      if (!it.obj.visible) continue;
      if (this.found.has(id)) {
        // ramassé : monte en tournant puis disparaît
        it.gone = Math.min(1, it.gone + dt * 1.6);
        it.obj.position.y = it.base + it.gone * 0.8;
        it.obj.rotation.y += dt * 12;
        it.obj.scale.setScalar(1.3 * (1 - it.gone));
        if (it.gone >= 1) it.obj.visible = false;
        continue;
      }
      it.obj.position.y = it.base + 0.04 + Math.sin(elapsed * 2 + it.phase) * 0.025;
      it.obj.rotation.y = elapsed * 0.9 + it.phase;
    }
  }
}

// ---------- terminal caché
export interface TermApi {
  open: (placeId: string) => void;
  lang: (l: 'fr' | 'en') => void;
  sound: (on?: boolean) => boolean;
  tresors: () => { found: string[]; total: number };
  resetTresors: () => void;
  fireworks: () => void;
  track: (name: string) => void;
}

const esc = (s: string): string => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c]!);

export class Terminal {
  private el: HTMLElement;
  private out: HTMLElement;
  private input: HTMLInputElement;
  private history: string[] = [];
  private hi = 0;
  private api: TermApi;
  private onKey: () => void;
  private lastFocus: HTMLElement | null = null;

  constructor(api: TermApi, onKey: () => void) {
    this.api = api;
    this.onKey = onKey;
    this.el = document.createElement('div');
    this.el.className = 'term glass';
    this.el.setAttribute('role', 'dialog');
    this.el.setAttribute('aria-modal', 'false');
    this.el.hidden = true;
    this.el.innerHTML = `
      <div class="term-bar"><i></i><i></i><i></i><span>trystan@rog-flow: ~</span><button type="button" class="term-x" aria-label="Fermer">×</button></div>
      <div class="term-out" aria-live="polite"></div>
      <label class="term-line"><span class="term-ps">trystan@rog-flow:~$</span><input type="text" spellcheck="false" autocomplete="off" autocapitalize="off" aria-label="Commande" /></label>`;
    document.body.append(this.el);
    this.out = this.el.querySelector('.term-out')!;
    this.input = this.el.querySelector('input')!;
    this.el.querySelector('.term-x')!.addEventListener('click', () => this.close());
    this.el.addEventListener('pointerdown', (e) => e.stopPropagation());
    this.input.addEventListener('keydown', (e) => this.key(e));
    // ouverture : touche sous Échap (` en QWERTY, ² en AZERTY : même position physique)
    addEventListener('keydown', (e) => {
      if (e.code !== 'Backquote' || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.target instanceof HTMLInputElement && e.target !== this.input) return;
      e.preventDefault();
      this.toggle();
    });
  }

  /** Appui long (650 ms) sur un élément : ouverture au doigt. */
  longPress(target: HTMLElement): void {
    let timer = 0;
    target.addEventListener('pointerdown', () => (timer = window.setTimeout(() => this.open(), 650)));
    for (const ev of ['pointerup', 'pointerleave', 'pointercancel'] as const) target.addEventListener(ev, () => clearTimeout(timer));
    target.addEventListener('contextmenu', (e) => this.el.hidden || e.preventDefault());
  }

  get isOpen(): boolean {
    return !this.el.hidden;
  }

  toggle(): void {
    if (this.el.hidden) this.open();
    else this.close();
  }

  open(): void {
    if (!this.el.hidden) return;
    this.lastFocus = document.activeElement as HTMLElement | null;
    this.el.hidden = false;
    this.el.querySelector('.term-x')!.setAttribute('aria-label', t('Fermer', 'Close'));
    this.el.setAttribute('aria-label', t('Terminal caché', 'Hidden terminal'));
    if (!this.out.childElementCount) {
      this.print(t(
        'Bienvenue sur trystanbouzonrueda.com. Tu as trouvé le terminal caché 🎉\nTape <b>help</b> pour la liste des commandes.',
        'Welcome to trystanbouzonrueda.com. You found the hidden terminal 🎉\nType <b>help</b> for the list of commands.',
      ), true);
      this.api.track('terminal');
    }
    this.input.focus();
  }

  close(): void {
    this.el.hidden = true;
    this.lastFocus?.focus?.({ preventScroll: true });
  }

  private print(text: string, html = false): void {
    const p = document.createElement('pre');
    if (html) p.innerHTML = text;
    else p.textContent = text;
    this.out.append(p);
    this.out.scrollTop = this.out.scrollHeight;
  }

  private key(e: KeyboardEvent): void {
    e.stopPropagation(); // pas de déplacement de caméra (ZQSD, flèches) pendant la frappe
    if (e.key === 'Escape') { this.close(); return; }
    if (e.code === 'Backquote') { e.preventDefault(); this.close(); return; }
    if (e.key.length === 1 || e.key === 'Backspace') this.onKey();
    if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
      e.preventDefault();
      this.hi = THREE.MathUtils.clamp(this.hi + (e.key === 'ArrowUp' ? -1 : 1), 0, this.history.length);
      this.input.value = this.history[this.hi] ?? '';
      return;
    }
    if (e.key === 'Tab') {
      e.preventDefault();
      const v = this.input.value;
      const words = [...this.commands(), ...PLACES.filter((p) => p.section).map((p) => `cd ${p.id}`)];
      const m = words.filter((w) => w.startsWith(v));
      if (m.length === 1) this.input.value = m[0] + ' ';
      else if (m.length > 1) this.print(m.join('  '));
      return;
    }
    if (e.key !== 'Enter') return;
    const line = this.input.value.trim();
    this.input.value = '';
    this.print(`<span class="term-ps">trystan@rog-flow:~$</span> ${esc(line)}`, true);
    if (!line) return;
    this.history.push(line);
    this.hi = this.history.length;
    this.run(line);
  }

  private commands(): string[] {
    return ['help', 'whoami', 'ls', 'cd', 'cat cv', 'ping', 'nmap', 'ssh', 'uname -a', 'neofetch', 'date', 'history', 'trophees', 'lang', 'sound', 'sudo', 'clear', 'exit'];
  }

  private run(line: string): void {
    const [cmd, ...args] = line.split(/\s+/);
    const arg = args.join(' ').toLowerCase();
    const sections = PLACES.filter((p) => p.section);
    switch (cmd.toLowerCase()) {
      case 'help':
      case 'aide':
        this.print(t(
          `<b>whoami</b>         qui je suis
<b>ls</b>             les rubriques (lieux)
<b>cd</b> &lt;lieu&gt;      s'y rendre (ex. cd velodrome)
<b>cat cv</b>         version recruteur et CV
<b>nmap</b> ile       scanner l'île
<b>ping</b>, <b>ssh</b>      à essayer…
<b>trophees</b>       chasse aux trésors
<b>lang</b> fr|en     langue · <b>sound</b> on|off  son
<b>clear</b>, <b>exit</b>   effacer, fermer`,
          `<b>whoami</b>         who I am
<b>ls</b>             sections (landmarks)
<b>cd</b> &lt;place&gt;     go there (e.g. cd velodrome)
<b>cat cv</b>         recruiter version and resume
<b>nmap</b> island    scan the island
<b>ping</b>, <b>ssh</b>      try them…
<b>trophies</b>       treasure hunt
<b>lang</b> fr|en     language · <b>sound</b> on|off  sound
<b>clear</b>, <b>exit</b>   clear, close`,
        ), true);
        break;
      case 'whoami':
        this.print(t(
          'Trystan Bouzon Rueda — étudiant ingénieur au CESI, alternant à la mairie de Plan-de-Cuques.\nSystèmes, réseaux, homelab ; je cherche un stage de 12 semaines à l’étranger (systèmes, réseaux, IA).',
          'Trystan Bouzon Rueda — engineering student at CESI, work-study at Plan-de-Cuques town hall.\nSystems, networking, homelab; looking for a 12-week internship abroad (systems, networking, AI).',
        ));
        break;
      case 'ls':
        this.print(sections.map((p) => `<b>${p.id}/</b>  <span class="term-dim">${esc(p.name)}</span>`).join('\n'), true);
        break;
      case 'cd':
      case 'open': {
        if (!arg || arg === '~' || arg === '..') { this.print(t('Usage : cd <lieu>  (voir ls)', 'Usage: cd <place>  (see ls)')); break; }
        const p = PLACES.find((x) => x.id === arg.replace(/\/$/, '') || x.name.toLowerCase().includes(arg));
        if (!p) { this.print(`cd: ${esc(arg)}: ${t('aucun lieu de ce nom', 'no such place')}`); break; }
        this.print(t(`En route vers ${p.name}…`, `Flying to ${p.name}…`));
        this.api.open(p.id);
        setTimeout(() => this.close(), 500);
        break;
      }
      case 'cat':
        if (/cv|resume/.test(arg)) {
          this.print(t('Ouverture de la version recruteur…', 'Opening the recruiter version…'));
          setTimeout(() => location.assign(`${import.meta.env.BASE_URL}recruteur/${lang === 'en' ? '?lang=en' : ''}`), 500);
        } else if (arg === '/etc/passwd' || arg === '/etc/shadow') this.print(t('Bien essayé 😏 Accès refusé.', 'Nice try 😏 Permission denied.'));
        else this.print(`cat: ${esc(arg || '?')}: ${t('fichier introuvable (essaie cat cv)', 'no such file (try cat cv)')}`);
        break;
      case 'ping': {
        const host = esc(arg || 'trystanbouzonrueda.com');
        const lines = [`PING ${host} (127.0.0.1) 56(84) bytes of data.`];
        for (let i = 1; i <= 4; i++) lines.push(`64 bytes from ${host}: icmp_seq=${i} ttl=64 time=${(0.03 + Math.random() * 0.05).toFixed(3)} ms`);
        lines.push(`--- ${host} ping statistics ---`, `4 packets transmitted, 4 received, 0% packet loss`);
        this.print(lines.join('\n'));
        break;
      }
      case 'nmap': {
        const rows = sections.map((p, i) => `${String(22 + i * 1000).padEnd(9)}open  ${p.id.padEnd(22)}${p.name}`);
        this.print(`Starting Nmap 7.95 ( https://nmap.org )\nNmap scan report for ${t('ile', 'island')}.trystanbouzonrueda.com\nPORT     STATE SERVICE               ${t('LIEU', 'LANDMARK')}\n${rows.join('\n')}\n\n${t('Astuce : cd <service> pour t’y rendre.', 'Tip: cd <service> to go there.')}`);
        break;
      }
      case 'ssh':
        if (/mairie|plan|cuques|town/.test(arg)) {
          this.print(t('Connexion à mairie.plan-de-cuques… authentifié par clé ✔', 'Connecting to town hall… key authentication ✔'));
          this.api.open('eglise_plan_de_cuques');
          setTimeout(() => this.close(), 700);
        } else this.print(arg ? `ssh: connect to host ${esc(arg)} port 22: ${t('accès réservé (essaie ssh mairie)', 'access restricted (try ssh mairie)')}` : 'usage: ssh mairie');
        break;
      case 'sudo':
        if (/rm\s+-rf/.test(line)) this.print(t('Ah non. Pas sur mon île. 🏝️', 'Nope. Not on my island. 🏝️'));
        else this.print(t('trystan n’est pas dans le fichier sudoers. Cet incident sera signalé. 🚨', 'trystan is not in the sudoers file. This incident will be reported. 🚨'));
        break;
      case 'rm':
        this.print(t('rm : opération refusée (île protégée en écriture)', 'rm: operation not permitted (read-only island)'));
        break;
      case 'uname':
        this.print('Linux rog-flow 7.3.3-300.fc45.x86_64 #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux');
        break;
      case 'neofetch':
      case 'fastfetch':
        this.print(`<span class="term-acc">        .--.        </span> <b>trystan</b>@<b>rog-flow</b>
<span class="term-acc">       |o_o |       </span> OS: Fedora Linux 45
<span class="term-acc">       |:_/ |       </span> Host: ROG Flow X13
<span class="term-acc">      //   \\ \\      </span> Shell: bash
<span class="term-acc">     (|     | )     </span> WM: three.js ${THREE.REVISION}
<span class="term-acc">    /'\\_   _/\`\\     </span> ${t('Site', 'Site')}: trystanbouzonrueda.com
<span class="term-acc">    \\___)=(___/     </span> ${t('Statut', 'Status')}: ${t('cherche un stage à l’étranger', 'looking for an internship abroad')}`, true);
        break;
      case 'date':
        this.print(new Date().toString());
        break;
      case 'history':
        this.print(this.history.map((h, i) => `${String(i + 1).padStart(4)}  ${h}`).join('\n'));
        break;
      case 'trophees':
      case 'trophies':
      case 'tresors': {
        const s = this.api.tresors();
        if (arg === 'reset') {
          this.api.resetTresors();
          this.print(t('Chasse remise à zéro : les objets sont de retour dans la ville.', 'Hunt reset: the items are back in the city.'));
          break;
        }
        const list = TRESORS.map((tr) => `${s.found.includes(tr.id) ? '✔' : '·'} ${s.found.includes(tr.id) ? tr.name[lang] : '???'}`).join('\n');
        this.print(`${t('Trésors', 'Treasures')} : ${s.found.length}/${s.total}\n${list}${s.found.length === s.total ? `\n\n🏆 ${t('Chasse terminée, bravo !', 'Hunt complete, well done!')}` : `\n\n${t('Indice : 5 objets d’informaticien sont cachés près des monuments.', 'Hint: 5 IT items are hidden near the landmarks.')}`}`);
        break;
      }
      case 'lang':
        if (arg === 'fr' || arg === 'en') { this.api.lang(arg); this.print(arg === 'fr' ? 'Langue : français' : 'Language: English'); }
        else this.print('usage: lang fr|en');
        break;
      case 'sound':
      case 'son': {
        const on = this.api.sound(arg === 'on' ? true : arg === 'off' ? false : undefined);
        this.print(t(`Son ${on ? 'activé' : 'coupé'}`, `Sound ${on ? 'on' : 'off'}`));
        break;
      }
      case 'konami':
      case 'fireworks':
      case 'feu':
        this.print('↑ ↑ ↓ ↓ ← → ← → B A  🎆');
        this.api.fireworks();
        break;
      case 'clear':
        this.out.replaceChildren();
        break;
      case 'exit':
      case 'quit':
        this.close();
        break;
      default:
        this.print(`${esc(cmd)}: ${t('commande introuvable (tape help)', 'command not found (type help)')}`, true);
    }
  }
}
