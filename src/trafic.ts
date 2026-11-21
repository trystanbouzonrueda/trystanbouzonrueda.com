import * as THREE from 'three';

/** Trajets préenregistrés à l'export (public/data/trafic.json) : polylignes posées sur la voirie. */
interface Path {
  pts: [number, number, number][];
  voie: string;
}

interface Car {
  pts: THREE.Vector3[];
  cum: number[];
  s: number;
  dir: 1 | -1;
  speed: number;
}

const COLORS = [0xd6232a, 0x2a6fdb, 0xf4c430, 0xf4f4f0, 0x3c9a5f, 0x2b2d33, 0xe9852f, 0x8f86c9];
const SIDE = 0.022; // décalage à droite de la chaussée

/** Voitures low-poly sur les grands axes, en maillages instanciés (2 appels de rendu en tout). */
export class Trafic {
  readonly group = Object.assign(new THREE.Group(), { name: 'trafic' });
  private cars: Car[] = [];
  private bodies!: THREE.InstancedMesh;
  private cabins!: THREE.InstancedMesh;
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private p = new THREE.Vector3();
  private t = new THREE.Vector3();
  private up = new THREE.Vector3(0, 1, 0);
  private one = new THREE.Vector3(1, 1, 1);

  async load(url: string): Promise<void> {
    const data: Path[] = await (await fetch(url)).json();
    for (const path of data) {
      const pts = path.pts.map((p) => new THREE.Vector3(...p));
      const cum = [0];
      for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + pts[i].distanceTo(pts[i - 1]));
      const len = cum[cum.length - 1];
      const n = path.voie === '1' ? 5 : 3;
      for (let k = 0; k < n; k++) {
        this.cars.push({ pts, cum, s: (len * (k + 0.37)) / n, dir: k % 2 === 0 ? 1 : -1, speed: path.voie === '1' ? 0.7 : 0.45 });
      }
    }
    const mat = new THREE.MeshStandardMaterial({ roughness: 0.6, flatShading: true });
    this.bodies = new THREE.InstancedMesh(new THREE.BoxGeometry(0.055, 0.02, 0.027), mat, this.cars.length);
    this.cabins = new THREE.InstancedMesh(
      new THREE.BoxGeometry(0.03, 0.016, 0.024),
      new THREE.MeshStandardMaterial({ color: 0x2f3a4a, roughness: 0.3, flatShading: true }),
      this.cars.length,
    );
    const c = new THREE.Color();
    this.cars.forEach((_, i) => this.bodies.setColorAt(i, c.setHex(COLORS[i % COLORS.length])));
    for (const im of [this.bodies, this.cabins]) {
      im.castShadow = true;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      im.frustumCulled = false;
      this.group.add(im);
    }
  }

  update(dt: number): void {
    if (!this.bodies) return;
    this.cars.forEach((car, i) => {
      const len = car.cum[car.cum.length - 1];
      car.s += car.dir * car.speed * dt;
      if (car.s > len || car.s < 0) { // bout de l'axe : demi-tour sur l'autre voie
        car.s = THREE.MathUtils.clamp(car.s, 0, len);
        car.dir = (-car.dir) as 1 | -1;
      }
      let j = 1;
      while (j < car.cum.length - 1 && car.cum[j] < car.s) j++;
      const a = car.pts[j - 1], b = car.pts[j];
      const f = (car.s - car.cum[j - 1]) / Math.max(1e-6, car.cum[j] - car.cum[j - 1]);
      this.p.lerpVectors(a, b, f);
      this.t.subVectors(b, a).normalize().multiplyScalar(car.dir);
      // conduite à droite
      this.p.x += -this.t.z * SIDE;
      this.p.z += this.t.x * SIDE;
      this.q.setFromAxisAngle(this.up, Math.atan2(-this.t.z, this.t.x));
      this.m.compose(this.p.setY(this.p.y + 0.01), this.q, this.one);
      this.bodies.setMatrixAt(i, this.m);
      this.p.y += 0.017;
      this.m.compose(this.p, this.q, this.one);
      this.cabins.setMatrixAt(i, this.m);
    });
    this.bodies.instanceMatrix.needsUpdate = true;
    this.cabins.instanceMatrix.needsUpdate = true;
  }
}
