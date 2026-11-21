import * as THREE from 'three';

/** Fusionne des boîtes en une géométrie non indexée (positions + normales). */
function merge(geos: THREE.BufferGeometry[]): THREE.BufferGeometry {
  const pos: number[] = [], nor: number[] = [];
  for (const g of geos) {
    const ng = g.toNonIndexed();
    pos.push(...(ng.getAttribute('position').array as Float32Array));
    nor.push(...(ng.getAttribute('normal').array as Float32Array));
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  out.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
  return out;
}

/** Avions et mouettes : tout est instancié (1 appel de rendu par type), trajectoires calculées, rien à charger. */

interface Avion { cx: number; cz: number; rx: number; rz: number; h: number; speed: number; phase: number }
interface Mouette { cx: number; cy: number; cz: number; r: number; speed: number; phase: number; wob: number }

const AVIONS: Avion[] = [
  // grandes boucles au-dessus de la baie et de la ville (axe de Marignane au nord-ouest)
  { cx: -4, cz: -2, rx: 26, rz: 18, h: 7.5, speed: 0.05, phase: 0 },
  { cx: 6, cz: 4, rx: 20, rz: 26, h: 9, speed: -0.04, phase: 2.2 },
  { cx: 2, cz: -10, rx: 30, rz: 14, h: 6.5, speed: 0.035, phase: 4.1 },
];
// vols de mouettes : Vieux-Port, Notre-Dame, plages du Prado, Mucem, Frioul
const NIDS: [number, number, number, number][] = [
  [-1.8, 1.4, 0.4, 12], [-0.7, 4.4, 5.0, 9], [3.5, 1.3, 14.5, 10], [-4.6, 1.3, -1.4, 8], [-10, 1.5, 6, 8],
];

export class Ciel {
  readonly group = Object.assign(new THREE.Group(), { name: 'ciel' });
  private avions: THREE.InstancedMesh;
  private trainees: THREE.InstancedMesh;
  private mouettes: THREE.InstancedMesh;
  private birds: Mouette[] = [];
  private uTime = { value: 0 };
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3(1, 1, 1);
  private e = new THREE.Euler();

  constructor() {
    // avion low-poly : fuselage, ailes, dérive et stabilisateurs (nez vers +x)
    const parts = [
      new THREE.BoxGeometry(0.5, 0.07, 0.07),
      new THREE.BoxGeometry(0.12, 0.012, 0.56).translate(0.02, -0.01, 0),
      new THREE.BoxGeometry(0.07, 0.11, 0.012).translate(-0.22, 0.07, 0),
      new THREE.BoxGeometry(0.06, 0.01, 0.2).translate(-0.22, 0.02, 0),
      new THREE.BoxGeometry(0.06, 0.05, 0.05).translate(0.27, -0.005, 0),
    ];
    const geo = merge(parts);
    this.avions = new THREE.InstancedMesh(geo, new THREE.MeshStandardMaterial({ color: 0xf6f6f2, roughness: 0.5, flatShading: true }), AVIONS.length);
    this.trainees = new THREE.InstancedMesh(
      new THREE.BoxGeometry(1, 0.02, 0.02).translate(-0.5, 0, 0),
      new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.45, depthWrite: false }),
      AVIONS.length * 2,
    );
    // mouette : deux ailes en V, battement dans le vertex shader (phase par instance)
    const wing = new THREE.BufferGeometry();
    wing.setAttribute('position', new THREE.Float32BufferAttribute([
      0, 0, 0, -0.012, 0, -0.05, 0.012, 0, 0, // aile gauche
      0, 0, 0, 0.012, 0, 0, -0.012, 0, 0.05, // aile droite
      0.02, 0, 0, -0.025, 0, 0.006, -0.025, 0, -0.006, // corps
    ], 3));
    wing.computeVertexNormals();
    let n = 0;
    for (const [, , , k] of NIDS) n += k;
    const phases = new Float32Array(n);
    let i = 0;
    for (const [cx, cy, cz, k] of NIDS) {
      for (let j = 0; j < k; j++, i++) {
        phases[i] = Math.random() * 6.28;
        this.birds.push({ cx, cy: cy + Math.random() * 0.6, cz, r: 0.4 + Math.random() * 1.1, speed: (0.35 + Math.random() * 0.3) * (j % 3 ? 1 : -1), phase: Math.random() * 6.28, wob: Math.random() * 6.28 });
      }
    }
    wing.setAttribute('aPhase', new THREE.InstancedBufferAttribute(phases, 1));
    const birdMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.7, side: THREE.DoubleSide });
    birdMat.onBeforeCompile = (sh) => {
      sh.uniforms.uTime = this.uTime;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nattribute float aPhase;\nuniform float uTime;')
        .replace('#include <begin_vertex>', '#include <begin_vertex>\ntransformed.y += abs(position.z) * 0.9 * sin(uTime * 9.0 + aPhase);');
    };
    this.mouettes = new THREE.InstancedMesh(wing, birdMat, n);
    for (const im of [this.avions, this.trainees, this.mouettes]) {
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      im.frustumCulled = false;
      this.group.add(im);
    }
    this.avions.castShadow = true;
  }

  update(t: number): void {
    this.uTime.value = t;
    AVIONS.forEach((a, i) => {
      const u = a.phase + t * a.speed;
      const x = a.cx + a.rx * Math.cos(u), z = a.cz + a.rz * Math.sin(u);
      // tangente de l'ellipse : cap de l'avion ; léger roulis dans le virage
      const dx = -a.rx * Math.sin(u) * Math.sign(a.speed), dz = a.rz * Math.cos(u) * Math.sign(a.speed);
      const yaw = Math.atan2(-dz, dx);
      this.p.set(x, a.h + 0.4 * Math.sin(u * 2), z);
      this.q.setFromEuler(this.e.set(0.25 * Math.sign(a.speed), yaw, 0, 'YXZ'));
      this.m.compose(this.p, this.q, this.s.set(1, 1, 1));
      this.avions.setMatrixAt(i, this.m);
      // deux traînées depuis les ailes
      for (const side of [-1, 1]) {
        const off = new THREE.Vector3(-0.05, -0.01, side * 0.2).applyQuaternion(this.q);
        this.m.compose(this.p.clone().add(off), this.q, this.s.set(3.5, 1, 1));
        this.trainees.setMatrixAt(i * 2 + (side > 0 ? 1 : 0), this.m);
      }
    });
    this.birds.forEach((b, i) => {
      const u = b.phase + t * b.speed;
      this.p.set(b.cx + b.r * Math.cos(u), b.cy + 0.15 * Math.sin(t * 0.7 + b.wob), b.cz + b.r * Math.sin(u));
      const yaw = Math.atan2(-Math.cos(u) * Math.sign(b.speed), -Math.sin(u) * Math.sign(b.speed));
      this.q.setFromEuler(this.e.set(0, yaw, 0.3 * Math.sign(b.speed)));
      this.m.compose(this.p, this.q, this.s.set(1.6, 1.6, 1.6));
      this.mouettes.setMatrixAt(i, this.m);
    });
    this.avions.instanceMatrix.needsUpdate = true;
    this.trainees.instanceMatrix.needsUpdate = true;
    this.mouettes.instanceMatrix.needsUpdate = true;
  }
}
