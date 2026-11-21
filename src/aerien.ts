import * as THREE from 'three';
import { mergeChildren } from './merge';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Vie aérienne (en plus des avions et mouettes de ciel.ts) :
 *  - montgolfières à rayures qui dérivent lentement (brûleur allumé la nuit) ;
 *  - hélicoptère qui tourne au-dessus du port ;
 *  - Canadair (modèle Meshy) : écope en rasant la mer, survole la ville, largue sur les collines du nord. */

const BALLONS = [
  { c: [2, 4.6, 6], r: 7, h: 4.6, speed: 0.012, colors: [0xd6232a, 0xf4c430] },
  { c: [-2, 5.4, -4], r: 9, h: 5.4, speed: -0.009, colors: [0x2a6fdb, 0xffffff] },
  { c: [8, 5.0, -6], r: 6, h: 5.0, speed: 0.014, colors: [0x3c9a5f, 0xf4f4f0, 0xe9852f] },
  { c: [5, 6.2, 12], r: 8, h: 6.2, speed: -0.011, colors: [0x8f86c9, 0xf4c430] },
  { c: [-6, 4.2, 9], r: 5, h: 4.2, speed: 0.016, colors: [0xe96fa0, 0xffffff, 0x7cc8ff] },
];

/** Enveloppe en goutte d'eau, rayures verticales en couleurs de sommet, nacelle et cordes. */
function makeBalloon(colors: number[]): THREE.BufferGeometry {
  // profil de bas en haut : col étroit au-dessus de la nacelle, ventre large aux deux tiers, calotte arrondie
  const prof: THREE.Vector2[] = [];
  for (let i = 0; i <= 12; i++) {
    const t = i / 12;
    const r = t < 0.65 ? 0.06 + 0.36 * Math.sin((t / 0.65) * Math.PI * 0.5) : 0.42 * Math.cos(((t - 0.65) / 0.35) * Math.PI * 0.5);
    prof.push(new THREE.Vector2(Math.max(0.001, r), 0.16 + t * 0.8));
  }
  const env = new THREE.LatheGeometry(prof, 12).toNonIndexed();
  const pos = env.getAttribute('position');
  const col = new Float32Array(pos.count * 3);
  const c = new THREE.Color();
  for (let i = 0; i < pos.count; i += 3) {
    // une couleur par fuseau (12 fuseaux)
    const ang = Math.atan2(pos.getZ(i) + pos.getZ(i + 1) + pos.getZ(i + 2), pos.getX(i) + pos.getX(i + 1) + pos.getX(i + 2));
    const k = Math.floor(((ang + Math.PI) / (Math.PI * 2)) * 12) % colors.length;
    c.setHex(colors[k]);
    for (let j = 0; j < 3; j++) col.set([c.r, c.g, c.b], (i + j) * 3);
  }
  env.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const solid = (g: THREE.BufferGeometry, hex: number): THREE.BufferGeometry => {
    const n = g.toNonIndexed();
    const cc = new THREE.Color(hex);
    const a = new Float32Array(n.getAttribute('position').count * 3);
    for (let i = 0; i < a.length; i += 3) a.set([cc.r, cc.g, cc.b], i);
    n.setAttribute('color', new THREE.BufferAttribute(a, 3));
    n.deleteAttribute('uv');
    return n;
  };
  env.deleteAttribute('uv');
  const parts = [env, solid(new THREE.BoxGeometry(0.12, 0.09, 0.12).translate(0, -0.04, 0), 0x8a5a3b)];
  for (const [x, z] of [[-0.05, -0.05], [0.05, -0.05], [-0.05, 0.05], [0.05, 0.05]]) {
    parts.push(solid(new THREE.BoxGeometry(0.006, 0.2, 0.006).translate(x, 0.06, z), 0x3a3a3a));
  }
  for (const p of parts) p.deleteAttribute('normal');
  const g = mergeGeometries(parts)!;
  g.computeVertexNormals();
  return g;
}

function makeHelico(): THREE.Group {
  const g = new THREE.Group();
  const red = new THREE.MeshStandardMaterial({ color: 0xd6232a, roughness: 0.5, flatShading: true });
  const white = new THREE.MeshStandardMaterial({ color: 0xf4f4f0, roughness: 0.5, flatShading: true });
  const dark = new THREE.MeshStandardMaterial({ color: 0x23324a, roughness: 0.3, flatShading: true });
  const add = (geo: THREE.BufferGeometry, mat: THREE.Material, x = 0, y = 0, z = 0): THREE.Mesh => {
    const m = new THREE.Mesh(geo, mat);
    m.position.set(x, y, z);
    m.castShadow = true;
    g.add(m);
    return m;
  };
  add(new THREE.BoxGeometry(0.16, 0.08, 0.08), red);
  add(new THREE.BoxGeometry(0.06, 0.05, 0.075), dark, 0.06, 0.012, 0);
  add(new THREE.BoxGeometry(0.18, 0.025, 0.025), white, -0.15, 0.01, 0);
  add(new THREE.BoxGeometry(0.03, 0.06, 0.01), red, -0.24, 0.04, 0);
  add(new THREE.BoxGeometry(0.14, 0.006, 0.006), dark, 0, -0.055, 0.035);
  add(new THREE.BoxGeometry(0.14, 0.006, 0.006), dark, 0, -0.055, -0.035);
  const rotor = add(new THREE.BoxGeometry(0.38, 0.004, 0.02), dark, 0, 0.055, 0);
  rotor.add(new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.004, 0.38), dark));
  rotor.name = 'rotor';
  const tail = add(new THREE.BoxGeometry(0.05, 0.004, 0.008), dark, -0.24, 0.05, 0.01);
  tail.name = 'tail';
  // carlingue immobile fusionnée par matériau ; rotor et anticouple restent à part (ils tournent)
  mergeChildren(g, (o) => o === rotor || o === tail);
  return g;
}

export class Aerien {
  readonly group = Object.assign(new THREE.Group(), { name: 'aerien' });
  private ballons: { mesh: THREE.Mesh; flame: THREE.Mesh; b: (typeof BALLONS)[number]; phase: number }[] = [];
  private helico = makeHelico();
  private canadair: THREE.Object3D | null = null;
  private route: THREE.CatmullRomCurve3 | null = null;
  private seaY = 0;
  private u = 0;
  private drops!: THREE.InstancedMesh; // gerbe d'écopage et eau larguée
  private spray: { p: THREE.Vector3; v: THREE.Vector3; life: number }[] = [];
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private s = new THREE.Vector3();
  private tmp = new THREE.Vector3();
  private night = 0;
  private forced = 0; // largage demandé par un clic (secondes restantes)

  constructor() {
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.75, flatShading: true });
    const flameMat = new THREE.MeshBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0 });
    BALLONS.forEach((b, i) => {
      const mesh = new THREE.Mesh(makeBalloon(b.colors), mat);
      mesh.scale.setScalar(0.85);
      mesh.castShadow = true;
      const flame = new THREE.Mesh(new THREE.ConeGeometry(0.035, 0.09, 6), flameMat.clone());
      flame.position.y = 0.06;
      mesh.add(flame);
      this.group.add(mesh);
      this.ballons.push({ mesh, flame, b, phase: i * 1.7 });
    });
    this.helico.scale.setScalar(1.4);
    this.group.add(this.helico);
    this.drops = new THREE.InstancedMesh(
      new THREE.BoxGeometry(0.03, 0.03, 0.03),
      new THREE.MeshStandardMaterial({ color: 0xeaf6ff, roughness: 0.4, transparent: true, opacity: 0.85 }),
      260,
    );
    this.drops.count = 0;
    this.drops.frustumCulled = false;
    this.group.add(this.drops);
  }

  /** Canadair : modèle Meshy (props.glb, nez vers +X) et circuit fermé écopage → largage. */
  setCanadair(model: THREE.Object3D, seaY: number): void {
    this.seaY = seaY;
    const s = seaY + 0.06; // ras de l'eau
    const pts: [number, number, number][] = [
      [-15, 2.2, 13], [-11, s + 0.3, 9.5], [-9, s, 7], [-6, s, 3.5], [-3, 1.8, -0.5], [2, 3.0, -6],
      [8, 2.8, -10], [12, 3.0, -13], [9, 4.2, -19], [-2, 4.8, -19], [-12, 4.0, -9], [-17, 3.2, 3],
    ];
    this.route = new THREE.CatmullRomCurve3(pts.map((p) => new THREE.Vector3(...p)), true, 'centripetal');
    model.traverse((c) => {
      const m = c as THREE.Mesh;
      if (m.isMesh) m.castShadow = true;
    });
    this.canadair = model;
    this.group.add(model);
  }

  /** Clic sur le Canadair (zone élargie autour de l'avion). */
  hit(raycaster: THREE.Raycaster): boolean {
    if (!this.canadair) return false;
    const p = this.canadair.getWorldPosition(this.tmp);
    return raycaster.ray.distanceSqToPoint(p) < 0.35 * 0.35;
  }

  /** Largage immédiat, où qu'il soit. */
  larguer(): void {
    this.forced = 2.2;
  }

  setNight(f: number): void {
    this.night = f;
  }

  update(dt: number, t: number): void {
    // montgolfières : grand cercle lent, légère houle verticale, flamme du brûleur par bouffées la nuit
    for (const { mesh, flame, b, phase } of this.ballons) {
      const a = t * b.speed * 2 + phase;
      mesh.position.set(b.c[0] + Math.cos(a) * b.r, b.h + Math.sin(t * 0.4 + phase) * 0.25, b.c[2] + Math.sin(a) * b.r);
      mesh.rotation.y = t * 0.05 + phase;
      const burst = Math.max(0, Math.sin(t * 1.3 + phase * 3)) ** 6;
      const op = Math.max(this.night * 0.25, burst * (0.4 + this.night * 0.6));
      (flame.material as THREE.MeshBasicMaterial).opacity = op;
      flame.visible = op > 0.01; // flamme éteinte : pas de draw call pour rien
      flame.scale.setScalar(0.6 + burst * 0.8);
    }
    // hélicoptère : boucle au-dessus du Vieux-Port et de la Joliette, nez dans le sens du vol
    const ha = t * 0.18;
    const hp = this.tmp.set(-1.5 + Math.cos(ha) * 3.2, 2.4 + Math.sin(t * 0.7) * 0.15, -1 + Math.sin(ha) * 2.2);
    this.helico.position.copy(hp);
    // cap = sens de la vitesse (dérivée de la boucle), nez vers +x ; léger roulis dans le virage
    this.helico.rotation.set(Math.sin(t * 0.5) * 0.06, Math.atan2(-Math.cos(ha) * 2.2, -Math.sin(ha) * 3.2), 0);
    this.helico.getObjectByName('rotor')!.rotation.y = t * 40;
    this.helico.getObjectByName('tail')!.rotation.z = t * 50;

    // Canadair
    if (this.canadair && this.route) {
      const len = 120; // ≈ longueur du circuit, vitesse constante
      this.u = (this.u + (dt * 1.1) / len) % 1;
      const p = this.route.getPointAt(this.u);
      const tan = this.route.getTangentAt(this.u);
      this.canadair.position.copy(p);
      this.canadair.lookAt(this.tmp.copy(p).add(tan));
      this.canadair.rotateY(-Math.PI / 2); // lookAt vise +Z, le modèle a le nez vers +X
      const bank = THREE.MathUtils.clamp(this.route.getTangentAt((this.u + 0.01) % 1).cross(tan).y * 60, -0.5, 0.5);
      this.canadair.rotateX(bank);
      // écopage : gerbe d'eau derrière l'avion au ras de l'eau ; largage au-dessus des collines du nord
      const scooping = p.y < this.seaY + 0.2;
      this.forced = Math.max(0, this.forced - dt);
      const dropping = (this.u > 0.44 && this.u < 0.56) || (this.forced > 0 && !scooping);
      if (scooping || dropping) {
        for (let k = 0; k < 3; k++) {
          const v = scooping
            ? new THREE.Vector3((Math.random() - 0.5) * 0.6, 0.5 + Math.random() * 0.6, (Math.random() - 0.5) * 0.6).addScaledVector(tan, -0.6)
            : new THREE.Vector3((Math.random() - 0.5) * 0.3, -0.2, (Math.random() - 0.5) * 0.3).addScaledVector(tan, 0.8);
          this.spray.push({ p: p.clone().add(new THREE.Vector3(0, scooping ? -0.02 : -0.06, 0)), v, life: scooping ? 0.7 : 1.6 });
        }
      }
    }
    // gouttes : gravité, disparition
    let n = 0;
    this.spray = this.spray.filter((d) => (d.life -= dt) > 0 && d.p.y > this.seaY - 0.1);
    for (const d of this.spray) {
      d.v.y -= 2.2 * dt;
      d.p.addScaledVector(d.v, dt);
      if (n >= 260) break;
      const sc = 0.6 + d.life;
      this.m.compose(d.p, this.q, this.s.set(sc, sc, sc));
      this.drops.setMatrixAt(n++, this.m);
    }
    this.drops.count = n;
    this.drops.instanceMatrix.needsUpdate = true;
  }
}
