import * as THREE from 'three';
import { mergeDeep } from './merge';

/** Arrivée du ciel : la caméra part très haut, traverse une couche de nuages et descend en spirale
 *  jusqu'à la vue d'ouverture, de plus en plus lentement. Un clic, la molette ou une touche accélère la fin. */
const DURATION = 7; // secondes
const START_RADIUS = 95; // distance au point regardé au départ (≈ 24 km à l'échelle de l'île)
const START_POLAR = 0.12; // presque à la verticale
const TURN = 1.15; // radians de rotation pendant la descente

export class Intro {
  readonly clouds = Object.assign(new THREE.Group(), { name: 'intro_nuages' });
  private t = 0;
  private speed = 1;
  private readonly cloudMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, flatShading: true, transparent: true, depthWrite: false });
  private readonly from: THREE.Spherical;
  private readonly to: THREE.Spherical;
  private readonly s = new THREE.Spherical();

  constructor(
    private readonly target: THREE.Vector3,
    home: THREE.Vector3,
    private readonly veil: HTMLElement,
  ) {
    this.to = new THREE.Spherical().setFromVector3(home.clone().sub(target));
    this.from = new THREE.Spherical(START_RADIUS, START_POLAR, this.to.theta + TURN);
    this.makeClouds();
  }

  /** Couche de nuages traversée vers 40–60 % de la descente (mêmes blocs low-poly que les nuages de l'île). */
  private makeClouds(): void {
    const geo = new THREE.IcosahedronGeometry(1, 0);
    let seed = 7;
    const rnd = (): number => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < 14; i++) {
      // le long de la trajectoire, un peu décalés pour passer à côté et au travers
      const k = 0.07 + rnd() * 0.26;
      const p = this.pointAt(k).add(new THREE.Vector3((rnd() - 0.5) * 16, (rnd() - 0.5) * 5, (rnd() - 0.5) * 16));
      const cloud = new THREE.Group();
      const puffs = 4 + Math.floor(rnd() * 4);
      for (let j = 0; j < puffs; j++) {
        const m = new THREE.Mesh(geo, this.cloudMat);
        const sc = 2.2 + rnd() * 2.4;
        m.scale.set(sc * 1.4, sc * 0.7, sc);
        m.position.set((j - puffs / 2) * 2.6, rnd() * 1.4, (rnd() - 0.5) * 3);
        cloud.add(m);
      }
      cloud.position.copy(p);
      cloud.rotation.y = rnd() * Math.PI;
      this.clouds.add(cloud);
    }
    mergeDeep(this.clouds);
  }

  /** Position de la caméra à l'avancement k (0 → 1, avant lissage). */
  private pointAt(k: number, out = new THREE.Vector3()): THREE.Vector3 {
    this.s.radius = THREE.MathUtils.lerp(this.from.radius, this.to.radius, k);
    this.s.phi = THREE.MathUtils.lerp(this.from.phi, this.to.phi, k);
    this.s.theta = THREE.MathUtils.lerp(this.from.theta, this.to.theta, k);
    return out.setFromSpherical(this.s).add(this.target);
  }

  skip(): void {
    this.speed = Math.max(this.speed, (DURATION * (1 - this.t)) / 0.9); // finit en ~0,9 s
  }

  /** Place la caméra ; renvoie true quand l'arrivée est terminée. */
  update(dt: number, camera: THREE.PerspectiveCamera): boolean {
    this.t = Math.min(1, this.t + (dt * this.speed) / DURATION);
    // départ assez vif puis long ralenti : « on zoome petit à petit »
    const k = 1 - Math.pow(1 - this.t, 2.6);
    this.pointAt(k, camera.position);
    camera.lookAt(this.target);
    // voile de ciel au départ, nuages qui s'effacent une fois traversés
    this.veil.style.opacity = String(Math.max(0, 1 - this.t * 9)); // se dissipe vite : les nuages prennent le relais
    this.cloudMat.opacity = THREE.MathUtils.clamp((1 - this.t) * 2.2, 0, 0.92);
    this.clouds.visible = this.cloudMat.opacity > 0.01;
    return this.t >= 1;
  }

  dispose(): void {
    this.clouds.removeFromParent();
    this.clouds.traverse((o) => (o as THREE.Mesh).isMesh && (o as THREE.Mesh).geometry.dispose());
    this.cloudMat.dispose();
    this.veil.remove();
  }
}
