// Son d'ambiance, entièrement synthétisé en Web Audio : aucun fichier à télécharger, rien à créditer.
// Couches continues mélangées selon la vue : mer (vagues), rumeur de la ville, vent en altitude,
// cigales le jour / grillons la nuit, roulement du métro pendant un trajet. Mouettes de temps en temps.
// Bruitages ponctuels : clic sur un lieu, cloches, clameur du stade, feu d'artifice, trésor, terminal…
// Le contexte audio ne démarre qu'au premier geste (règle des navigateurs).

export type Bruit = 'clic' | 'cloches' | 'clameur' | 'feu' | 'tresor' | 'tresorFin' | 'touche' | 'largage' | 'erreur' | 'survol';

interface Vue {
  /** hauteur de la caméra au-dessus de l'île */
  height: number;
  /** distance caméra → point visé (zoom) */
  dist: number;
  /** 0 = jour, 1 = nuit */
  night: number;
  /** trajet en métro des monuments */
  riding: boolean;
}

export class Son {
  private ctx: AudioContext | null = null;
  private master!: GainNode;
  private noise!: AudioBuffer;
  private layers!: { mer: GainNode; ville: GainNode; vent: GainNode; cigales: GainNode; metro: GainNode };
  private nextGull = 4;
  private nextCricket = 0;
  private enabled: boolean;
  private seaLevel = 0;

  constructor(enabled: boolean) {
    this.enabled = enabled;
    const unlock = (): void => {
      if (this.enabled) this.start();
      if (this.ctx) for (const ev of ['pointerdown', 'keydown'] as const) removeEventListener(ev, unlock);
    };
    for (const ev of ['pointerdown', 'keydown'] as const) addEventListener(ev, unlock, { passive: true });
    document.addEventListener('visibilitychange', () => {
      if (!this.ctx) return;
      if (document.hidden) void this.ctx.suspend();
      else if (this.enabled) void this.ctx.resume();
    });
  }

  get on(): boolean {
    return this.enabled;
  }

  setEnabled(on: boolean): void {
    this.enabled = on;
    if (on) {
      this.start();
      void this.ctx?.resume();
      this.fade(0.9);
    } else if (this.ctx) {
      this.fade(0);
      setTimeout(() => !this.enabled && void this.ctx?.suspend(), 400);
    }
  }

  private fade(v: number): void {
    if (!this.ctx) return;
    const now = this.ctx.currentTime;
    this.master.gain.cancelScheduledValues(now);
    this.master.gain.setTargetAtTime(v, now, 0.15);
  }

  private start(): void {
    if (this.ctx) return;
    const AC = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!AC) return;
    const ctx = (this.ctx = new AC());
    this.master = ctx.createGain();
    this.master.gain.value = 0;
    // léger compresseur : les bruitages ne saturent jamais par-dessus l'ambiance
    const comp = ctx.createDynamicsCompressor();
    comp.threshold.value = -14;
    comp.ratio.value = 4;
    this.master.connect(comp).connect(ctx.destination);
    this.master.gain.setTargetAtTime(0.9, ctx.currentTime, 0.6);

    // bruit rose (approximation de Paul Kellet), 4 s en boucle : base de toutes les textures
    const len = ctx.sampleRate * 4;
    this.noise = ctx.createBuffer(1, len, ctx.sampleRate);
    const d = this.noise.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < len; i++) {
      const w = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + w * 0.0555179;
      b1 = 0.99332 * b1 + w * 0.0750759;
      b2 = 0.969 * b2 + w * 0.153852;
      b3 = 0.8665 * b3 + w * 0.3104856;
      b4 = 0.55 * b4 + w * 0.5329522;
      b5 = -0.7616 * b5 - w * 0.016898;
      d[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + w * 0.5362) * 0.11;
      b6 = w * 0.115926;
    }

    const loop = (type: BiquadFilterType, freq: number, q = 0.7): { out: GainNode; filter: BiquadFilterNode } => {
      const src = ctx.createBufferSource();
      src.buffer = this.noise;
      src.loop = true;
      src.loopStart = Math.random() * 3; // chaque couche démarre ailleurs dans la boucle : pas d'écho entre elles
      const filter = ctx.createBiquadFilter();
      filter.type = type;
      filter.frequency.value = freq;
      filter.Q.value = q;
      const out = ctx.createGain();
      out.gain.value = 0;
      src.connect(filter).connect(out).connect(this.master);
      src.start(0, src.loopStart);
      return { out, filter };
    };

    // mer : bruit grave dont le volume et la brillance ondulent comme des vagues (deux houles décalées)
    const mer = loop('lowpass', 520);
    const swell = ctx.createGain();
    swell.gain.value = 0.55;
    mer.out.disconnect();
    mer.out.connect(swell).connect(this.master);
    for (const [rate, depth] of [[0.11, 0.3], [0.067, 0.18]] as const) {
      const lfo = ctx.createOscillator();
      lfo.frequency.value = rate;
      const g = ctx.createGain();
      g.gain.value = depth;
      lfo.connect(g).connect(swell.gain);
      const gf = ctx.createGain();
      gf.gain.value = depth * 900;
      lfo.connect(gf).connect(mer.filter.frequency);
      lfo.start();
    }
    // ville : rumeur sourde, un peu de médium pour les voix lointaines
    const ville = loop('lowpass', 260);
    const voix = loop('bandpass', 900, 0.6);
    voix.out.disconnect();
    const vg = ctx.createGain();
    vg.gain.value = 0.25;
    voix.out.gain.value = 1;
    voix.out.connect(vg).connect(ville.out);
    // vent en altitude : passe-bande qui balaie lentement
    const vent = loop('bandpass', 420, 1.4);
    const vlfo = ctx.createOscillator();
    vlfo.frequency.value = 0.09;
    const vlg = ctx.createGain();
    vlg.gain.value = 260;
    vlfo.connect(vlg).connect(vent.filter.frequency);
    vlfo.start();
    // cigales : passe-bande aigu modulé très vite (le crissement), par vagues lentes
    const cig = loop('bandpass', 4600, 7);
    const am = ctx.createGain();
    am.gain.value = 0.5;
    cig.out.disconnect();
    cig.out.connect(am).connect(this.master);
    const fast = ctx.createOscillator();
    fast.frequency.value = 42;
    const fg = ctx.createGain();
    fg.gain.value = 0.5;
    fast.connect(fg).connect(am.gain);
    fast.start();
    // métro : grondement + bogies (impulsions régulières)
    const metro = loop('lowpass', 140);
    const clack = ctx.createOscillator();
    clack.type = 'square';
    clack.frequency.value = 1.6;
    const cg = ctx.createGain();
    cg.gain.value = 0.3;
    clack.connect(cg).connect(metro.filter.frequency);
    clack.start();

    this.layers = { mer: mer.out, ville: ville.out, vent: vent.out, cigales: cig.out, metro: metro.out };
  }

  /** Mélange des couches selon la vue (appelé à chaque image, léger). */
  update(dt: number, v: Vue): void {
    const ctx = this.ctx;
    if (!ctx || !this.enabled || ctx.state !== 'running') return;
    const now = ctx.currentTime;
    const sat = (x: number): number => Math.min(1, Math.max(0, x));
    const close = sat(1 - (v.dist - 2) / 14); // 1 = au ras des rues, 0 = vue d'ensemble
    const high = sat((v.height - 10) / 25);
    const day = 1 - v.night;
    const set = (g: GainNode, x: number): void => { g.gain.setTargetAtTime(x, now, 0.4); };
    this.seaLevel = 0.32 * (1 - close * 0.45) * (1 - high * 0.5);
    set(this.layers.mer, this.seaLevel);
    set(this.layers.ville, (v.riding ? 0.05 : 0.24) * close * (0.6 + 0.4 * day));
    set(this.layers.vent, 0.03 + 0.22 * high);
    set(this.layers.cigales, 0.035 * day * (0.3 + 0.7 * close) * (v.riding ? 0 : 1));
    set(this.layers.metro, v.riding ? 0.5 : 0);
    // mouettes : de temps en temps, plutôt de jour et près de la mer
    this.nextGull -= dt;
    if (this.nextGull <= 0) {
      this.nextGull = 7 + Math.random() * 14;
      if (day > 0.3 && !v.riding) this.gull(0.07 * day * (1 - high * 0.6));
    }
    // grillons la nuit : petites rafales de chants
    this.nextCricket -= dt;
    if (this.nextCricket <= 0 && v.night > 0.5 && !v.riding) {
      this.nextCricket = 0.6 + Math.random() * 1.4;
      this.cricket(0.025 * v.night * (0.4 + 0.6 * close));
    }
  }

  // ---------- briques de synthèse
  private env(g: GainNode, t: number, peak: number, attack: number, decay: number): void {
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(peak, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
  }

  private tone(freq: number, t: number, peak: number, decay: number, type: OscillatorType = 'sine', attack = 0.005, to?: number): void {
    const ctx = this.ctx!;
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(freq, t);
    if (to) o.frequency.exponentialRampToValueAtTime(to, t + attack + decay);
    const g = ctx.createGain();
    this.env(g, t, peak, attack, decay);
    o.connect(g).connect(this.master);
    o.start(t);
    o.stop(t + attack + decay + 0.05);
  }

  private burst(t: number, dur: number, peak: number, type: BiquadFilterType, f0: number, f1 = f0, q = 0.8, attack = 0.01): void {
    const ctx = this.ctx!;
    const src = ctx.createBufferSource();
    src.buffer = this.noise;
    const f = ctx.createBiquadFilter();
    f.type = type;
    f.Q.value = q;
    f.frequency.setValueAtTime(f0, t);
    f.frequency.exponentialRampToValueAtTime(f1, t + dur);
    const g = ctx.createGain();
    this.env(g, t, peak, attack, dur);
    src.connect(f).connect(g).connect(this.master);
    src.start(t, Math.random() * 3);
    src.stop(t + dur + attack + 0.05);
  }

  private gull(vol: number): void {
    const t = this.ctx!.currentTime;
    const n = 2 + Math.floor(Math.random() * 3);
    const base = 1300 + Math.random() * 500;
    for (let i = 0; i < n; i++) {
      const s = t + i * (0.32 + Math.random() * 0.1);
      // « kéé-ow » : montée brève puis chute, timbre nasal (dents de scie filtrées par l'enveloppe courte)
      this.tone(base * 0.8, s, vol * 0.6, 0.06, 'sawtooth', 0.02, base * 1.25);
      this.tone(base * 1.25, s + 0.08, vol, 0.22, 'triangle', 0.01, base * 0.7);
    }
  }

  private cricket(vol: number): void {
    const t = this.ctx!.currentTime;
    const f = 4200 + Math.random() * 600;
    for (let i = 0; i < 3; i++) this.tone(f, t + i * 0.055, vol, 0.03, 'sine', 0.004);
  }

  private bell(t: number, f: number, vol: number): void {
    // cloche d'église : partiels inharmoniques qui s'éteignent à des vitesses différentes
    const parts: [number, number, number][] = [[0.5, 1, 4.5], [1, 0.8, 3], [1.19, 0.5, 2.2], [1.5, 0.4, 2], [2, 0.35, 1.6], [2.74, 0.2, 1.1], [3.76, 0.12, 0.8]];
    for (const [r, a, d] of parts) this.tone(f * r, t, vol * a, d, 'sine', 0.004);
  }

  /** Bruitage ponctuel (ignoré si le son est coupé ou pas encore autorisé). */
  play(b: Bruit): void {
    const ctx = this.ctx;
    if (!ctx || !this.enabled || ctx.state !== 'running') return;
    const t = ctx.currentTime + 0.01;
    switch (b) {
      case 'clic':
        this.tone(880, t, 0.08, 0.09, 'sine', 0.004, 1320);
        this.tone(1760, t + 0.03, 0.03, 0.12, 'sine');
        break;
      case 'survol':
        // souffle léger et note douce : le bâtiment décolle
        this.burst(t, 0.35, 0.05, 'bandpass', 500, 1400, 1.2, 0.08);
        this.tone(660, t, 0.025, 0.25, 'sine', 0.02, 990);
        break;
      case 'touche':
        this.burst(t, 0.025, 0.06, 'highpass', 2500, 2500, 0.5, 0.002);
        break;
      case 'erreur':
        this.tone(220, t, 0.06, 0.18, 'square', 0.005, 160);
        break;
      case 'cloches':
        // volée de la Bonne Mère : deux cloches alternées
        for (let i = 0; i < 6; i++) this.bell(t + i * 0.75, i % 2 ? 392 : 330, 0.12);
        break;
      case 'clameur':
        // stade : foule qui monte puis retombe, et deux « oh » graves
        this.burst(t, 3.2, 0.35, 'bandpass', 600, 1100, 0.5, 0.9);
        this.burst(t + 0.2, 3, 0.2, 'bandpass', 1800, 2400, 0.7, 0.8);
        for (let i = 0; i < 3; i++) this.tone(150 + i * 4, t + 0.4, 0.04, 2.2, 'sawtooth', 0.5);
        break;
      case 'feu':
        // fusée qui siffle, explosion, crépitements
        this.tone(900, t, 0.03, 0.7, 'sine', 0.05, 2600);
        this.burst(t + 0.75, 1.4, 0.5, 'lowpass', 900, 80, 0.7, 0.005);
        for (let i = 0; i < 14; i++) this.burst(t + 0.9 + Math.random() * 1.1, 0.03, 0.08, 'highpass', 3000, 3000, 0.5, 0.002);
        break;
      case 'tresor':
        [523, 659, 784, 1047].forEach((f, i) => this.tone(f, t + i * 0.08, 0.07, 0.35, 'triangle'));
        break;
      case 'tresorFin':
        [523, 659, 784, 1047, 784, 1047, 1319].forEach((f, i) => this.tone(f, t + i * 0.11, 0.08, i === 6 ? 1.2 : 0.3, 'triangle'));
        break;
      case 'largage':
        this.burst(t, 1.6, 0.25, 'lowpass', 2400, 300, 0.6, 0.15);
        break;
    }
  }
}
