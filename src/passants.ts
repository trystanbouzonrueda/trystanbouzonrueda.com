import * as THREE from 'three';

/** Passants très simples (corps + tête, 2 maillages instanciés) sur des trajets de rue préenregistrés
 *  (public/data/pietons.json). Affichés seulement quand la caméra est assez proche du sol. */
type Path = [number, number, number][];

interface Walker { path: number; s: number; dir: 1 | -1; speed: number; side: number; phase: number }

const PER_PATH = 2;
const SHIRTS = [0xd6232a, 0xf4c430, 0x3c9a5f, 0xf4f4f0, 0x8f86c9, 0xe9852f, 0x2b2d33, 0x7cc8ff, 0xe96fa0, 0x5fb4e6];
const SKIN = [0xf1c7a5, 0xe3ae88, 0xc68e64, 0x8d5a3b];

export class Passants {
  readonly group = Object.assign(new THREE.Group(), { name: 'passants' });
  private paths: { pts: THREE.Vector3[]; cum: number[] }[] = [];
  private walkers: Walker[] = [];
  private bodies!: THREE.InstancedMesh;
  private heads!: THREE.InstancedMesh;
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private p = new THREE.Vector3();
  private t = new THREE.Vector3();
  private one = new THREE.Vector3(1, 1, 1);
  private up = new THREE.Vector3(0, 1, 0);
  /** part des passants animés et affichés (réglage qualité) */
  crowd = 1;

  async load(url: string): Promise<void> {
    const data: Path[] = await (await fetch(url)).json();
    for (const raw of data) {
      const pts = raw.map((v) => new THREE.Vector3(...v));
      const cum = [0];
      for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + pts[i].distanceTo(pts[i - 1]));
      const pi = this.paths.push({ pts, cum }) - 1;
      for (let k = 0; k < PER_PATH; k++) {
        this.walkers.push({ path: pi, s: Math.random() * cum[cum.length - 1], dir: Math.random() < 0.5 ? 1 : -1,
          speed: 0.05 + Math.random() * 0.04, side: Math.random() < 0.5 ? -1 : 1, phase: Math.random() * 6.28 });
      }
    }
    const n = this.walkers.length;
    this.bodies = new THREE.InstancedMesh(new THREE.BoxGeometry(0.016, 0.03, 0.011).translate(0, 0.015, 0),
      new THREE.MeshStandardMaterial({ roughness: 0.8, flatShading: true }), n);
    this.heads = new THREE.InstancedMesh(new THREE.BoxGeometry(0.011, 0.011, 0.011).translate(0, 0.036, 0),
      new THREE.MeshStandardMaterial({ roughness: 0.8, flatShading: true }), n);
    const c = new THREE.Color();
    for (let i = 0; i < n; i++) {
      this.bodies.setColorAt(i, c.setHex(SHIRTS[i % SHIRTS.length]));
      this.heads.setColorAt(i, c.setHex(SKIN[(i * 7) % SKIN.length]));
    }
    for (const im of [this.bodies, this.heads]) {
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      im.frustumCulled = false;
      this.group.add(im);
    }
  }

  update(dt: number, t: number, camDist: number): void {
    const show = camDist < 11 && !!this.bodies;
    this.group.visible = show;
    if (!show) return;
    const n = Math.round(this.walkers.length * this.crowd);
    this.bodies.count = this.heads.count = n;
    this.walkers.forEach((w, i) => {
      if (i >= n) return;
      const { pts, cum } = this.paths[w.path];
      const len = cum[cum.length - 1];
      w.s += w.dir * w.speed * dt;
      if (w.s > len || w.s < 0) { w.s = THREE.MathUtils.clamp(w.s, 0, len); w.dir = (-w.dir) as 1 | -1; }
      let j = 1;
      while (j < cum.length - 1 && cum[j] < w.s) j++;
      const f = (w.s - cum[j - 1]) / Math.max(1e-6, cum[j] - cum[j - 1]);
      this.p.lerpVectors(pts[j - 1], pts[j], f);
      this.t.subVectors(pts[j], pts[j - 1]).multiplyScalar(w.dir);
      const l = Math.hypot(this.t.x, this.t.z) || 1;
      // sur le trottoir (côté fixe), petit sautillement de marche
      this.p.x += (-this.t.z / l) * 0.03 * w.side;
      this.p.z += (this.t.x / l) * 0.03 * w.side;
      this.p.y += Math.abs(Math.sin(t * 9 + w.phase)) * 0.004;
      this.q.setFromAxisAngle(this.up, Math.atan2(this.t.x, this.t.z));
      this.m.compose(this.p, this.q, this.one);
      this.bodies.setMatrixAt(i, this.m);
      this.heads.setMatrixAt(i, this.m);
    });
    this.bodies.instanceMatrix.needsUpdate = true;
    this.heads.instanceMatrix.needsUpdate = true;
  }
}
