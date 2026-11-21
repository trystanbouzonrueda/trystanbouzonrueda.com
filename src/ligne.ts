import * as THREE from 'three';
import { mergeDeep } from './merge';

/** « Métro des monuments » : une ligne imaginaire, en aérien, qui relie les lieux du portfolio
 *  (même ceux qu'aucun métro ne dessert, jusqu'au CESI d'Aix). On monte dans la rame dorée,
 *  la caméra la suit au-dessus des toits, et la rubrique s'ouvre à l'arrivée. */

export interface Stop {
  id: string; // id du lieu (config.ts)
  name: string;
  kicker?: string; // id de la rubrique ouverte à l'arrivée
  p: THREE.Vector3; // quai (coordonnées de l'île)
}

const SPEED = 4.5; // unités / s : trajet court, posé
const CLEARANCE = 0.45; // marge au-dessus de l'obstacle le plus haut du trajet
const GOLD = 0xe9b949;

const ease = (x: number): number => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);

export class Ligne {
  readonly group = Object.assign(new THREE.Group(), { name: 'ligne' });
  readonly stops: Stop[] = [];
  /** quai où l'on se trouve (bulle dorée « prendre le métro ») */
  current = 'vieux_port';
  private train = this.makeTrain();
  private track: THREE.Mesh | null = null;
  private trackMat = new THREE.MeshStandardMaterial({ color: GOLD, roughness: 0.35, metalness: 0.4, transparent: true });
  private ride: { curve: THREE.Curve<THREE.Vector3>; t: number; dur: number; speed: number; to: string; fade: number; dir: THREE.Vector3 } | null = null;
  private pos = new THREE.Vector3();
  private tan = new THREE.Vector3();
  private camGoal = new THREE.Vector3();
  private look = new THREE.Vector3();
  private fadeOut = 0;

  constructor() {
    this.train.visible = false;
    this.group.add(this.train);
  }

  /** Rame garée au quai courant, prête à partir. */
  park(): void {
    const st = this.stop(this.current);
    if (!st) return;
    this.train.visible = true;
    this.train.position.copy(st.p).y += 0.012;
    this.train.rotation.set(0, Math.PI / 4, 0);
  }

  get riding(): boolean {
    return !!this.ride;
  }

  stop(id: string): Stop | undefined {
    return this.stops.find((s) => s.id === id);
  }

  /** Rame dorée de 2 voitures, orientée vers +z (pour lookAt). */
  private makeTrain(): THREE.Group {
    const g = new THREE.Group();
    const body = new THREE.MeshStandardMaterial({ color: GOLD, roughness: 0.4, metalness: 0.3, flatShading: true });
    const win = new THREE.MeshStandardMaterial({ color: 0x23324a, roughness: 0.25, flatShading: true });
    const band = new THREE.MeshStandardMaterial({ color: 0xfaf6ea, roughness: 0.6, flatShading: true });
    for (let k = 0; k < 2; k++) {
      const car = new THREE.Group();
      const add = (geo: THREE.BufferGeometry, mat: THREE.Material, y: number): void => {
        const m = new THREE.Mesh(geo, mat);
        m.position.y = y;
        m.castShadow = true;
        car.add(m);
      };
      add(new THREE.BoxGeometry(0.12, 0.09, 0.2), body, 0.05);
      add(new THREE.BoxGeometry(0.122, 0.028, 0.16), win, 0.07);
      add(new THREE.BoxGeometry(0.123, 0.012, 0.202), band, 0.03);
      car.position.z = (k - 0.5) * 0.215;
      g.add(car);
    }
    mergeDeep(g);
    return g;
  }

  /**
   * Trajet en l'air, tout droit : montée verticale du quai jusqu'à l'altitude de croisière (au-dessus de l'obstacle le
   * plus haut du trajet, donné par `ceiling`), ligne droite, descente verticale ; virages arrondis.
   */
  private buildCurve(from: THREE.Vector3, to: THREE.Vector3, ceiling: (a: THREE.Vector3, b: THREE.Vector3) => number): THREE.CurvePath<THREE.Vector3> {
    const cruise = Math.max(ceiling(from, to) + CLEARANCE, Math.max(from.y, to.y) + 0.8);
    const flat = Math.hypot(to.x - from.x, to.z - from.z);
    const r = Math.min(0.35, (cruise - Math.max(from.y, to.y)) * 0.5, flat * 0.25); // rayon des virages
    const dir = new THREE.Vector3(to.x - from.x, 0, to.z - from.z).normalize();
    const A = from.clone().setY(cruise), B = to.clone().setY(cruise);
    const path = new THREE.CurvePath<THREE.Vector3>();
    path.add(new THREE.LineCurve3(from.clone(), A.clone().setY(cruise - r)));
    path.add(new THREE.QuadraticBezierCurve3(A.clone().setY(cruise - r), A.clone(), A.clone().addScaledVector(dir, r)));
    path.add(new THREE.LineCurve3(A.clone().addScaledVector(dir, r), B.clone().addScaledVector(dir, -r)));
    path.add(new THREE.QuadraticBezierCurve3(B.clone().addScaledVector(dir, -r), B.clone(), B.clone().setY(cruise - r)));
    path.add(new THREE.LineCurve3(B.clone().setY(cruise - r), to.clone()));
    return path;
  }

  /** Lance le trajet vers le quai `to`. */
  go(to: string, ceiling: (a: THREE.Vector3, b: THREE.Vector3) => number): boolean {
    const a = this.stop(this.current), b = this.stop(to);
    if (!a || !b || a === b || this.ride) return false;
    const curve = this.buildCurve(a.p, b.p, ceiling);
    const len = curve.getLength();
    this.clearTrack();
    this.track = new THREE.Mesh(new THREE.TubeGeometry(curve, Math.min(400, Math.ceil(len * 6) + 40), 0.014, 5, false), this.trackMat);
    this.trackMat.opacity = 0;
    this.group.add(this.track);
    this.train.visible = true;
    const dir = new THREE.Vector3(b.p.x - a.p.x, 0, b.p.z - a.p.z).normalize();
    this.ride = { curve, t: 0, dur: THREE.MathUtils.clamp(len / SPEED, 3.2, 7.5), speed: 1, to, fade: 0, dir };
    this.place(0);
    return true;
  }

  /** Accélère la fin du trajet (clic, Échap). */
  skip(): void {
    if (this.ride) this.ride.speed = Math.max(this.ride.speed, (this.ride.dur * (1 - this.ride.t)) / 0.8);
  }

  private place(u: number): void {
    const c = this.ride!.curve;
    c.getPointAt(u, this.pos);
    c.getTangentAt(u, this.tan);
    this.train.position.copy(this.pos).y += 0.012;
    // cap vers la destination, à peine incliné dans les montées et descentes (pas de rame à la verticale)
    this.look.copy(this.pos).add(this.ride!.dir).y += THREE.MathUtils.clamp(this.tan.y, -1, 1) * 0.35;
    this.train.lookAt(this.look);
  }

  /**
   * Avance la rame et place la caméra derrière elle (coordonnées monde = île + `offset`).
   * Renvoie l'id du quai atteint à l'arrivée, sinon null.
   */
  update(dt: number, camera: THREE.PerspectiveCamera, target: THREE.Vector3, offset: THREE.Vector3): string | null {
    if (this.fadeOut > 0) {
      // le rail s'efface après l'arrivée
      this.fadeOut = Math.max(0, this.fadeOut - dt);
      this.trackMat.opacity = this.fadeOut;
      if (this.fadeOut === 0) this.clearTrack();
    }
    const r = this.ride;
    if (!r) return null;
    r.t = Math.min(1, r.t + (dt * r.speed) / r.dur);
    this.trackMat.opacity = Math.min(1, r.t * 6);
    const u = ease(r.t);
    this.place(u);
    // caméra embarquée : derrière et au-dessus de la rame, regard vers l'avant (lissée)
    // toujours derrière la rame dans le sens du trajet (même pendant la montée et la descente verticales)
    const back = r.dir;
    this.camGoal.copy(this.pos).addScaledVector(back, -1.7).add(offset);
    this.camGoal.y += 0.75;
    // la caméra glisse depuis la vue courante jusque derrière la rame, puis la suit de près
    camera.position.lerp(this.camGoal, 1 - Math.exp(-dt * (r.t < 0.25 ? 2.5 : 6)));
    this.look.copy(this.pos).addScaledVector(back, 2.4).add(offset);
    this.look.y -= 0.35; // regard un peu plongeant : la ville défile sous la rame
    target.lerp(this.look, 1 - Math.exp(-dt * (r.t < 0.25 ? 2.5 : 8)));
    camera.lookAt(target);
    if (r.t < 1) return null;
    this.ride = null;
    this.current = r.to;
    this.fadeOut = 1; // la rame reste à quai, le rail s'efface
    return r.to;
  }

  private clearTrack(): void {
    if (!this.track) return;
    this.track.removeFromParent();
    this.track.geometry.dispose();
    this.track = null;
  }
}
