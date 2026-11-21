import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Données exportées par blender/export_web.py (coordonnées three.js, y vers le haut). */
interface LineData {
  color: string;
  line: [number, number, number][];
  stations: { name: string; p: [number, number, number] }[];
}

interface Train {
  group: THREE.Group;
  s: number; // abscisse curviligne
  dir: 1 | -1;
  next: number; // index de la prochaine station
  wait: number; // temps d'arrêt restant (s)
}

interface Line {
  ref: string;
  pts: THREE.Vector3[];
  cum: number[]; // longueurs cumulées
  stops: { name: string; s: number; p: THREE.Vector3 }[];
  color: string;
  trains: Train[];
}

const SPEED = 1.6; // unités / s
const DWELL = 1.4; // arrêt en station (s)

/** Rames low-poly qui font l'aller-retour sur M1 et M2, avec un arrêt à chaque station. */
export class Metro {
  readonly group = Object.assign(new THREE.Group(), { name: 'metro' });
  private lines: Line[] = [];
  private stationMarkers: THREE.Mesh[] = [];

  async load(url: string): Promise<void> {
    const data: Record<string, LineData> = await (await fetch(url)).json();
    for (const [ref, d] of Object.entries(data)) {
      const pts = d.line.map((p) => new THREE.Vector3(...p));
      const cum = [0];
      for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + pts[i].distanceTo(pts[i - 1]));
      const stops = d.stations
        .map((st) => { const p = new THREE.Vector3(...st.p); return { name: st.name, s: this.project(pts, cum, p), p }; })
        .sort((a, b) => a.s - b.s);
      const line: Line = { ref, pts, cum, stops, trains: [], color: d.color };
      // une rame toutes les ~3 stations, dans les deux sens
      const n = Math.max(2, Math.round(stops.length / 3));
      for (let i = 0; i < n; i++) {
        const k = Math.floor((i * (stops.length - 1)) / n);
        const dir: 1 | -1 = i % 2 === 0 ? 1 : -1;
        const tr: Train = { group: this.makeTrain(d.color), s: stops[k].s, dir, next: k + dir, wait: Math.random() * DWELL };
        if (tr.next < 0 || tr.next >= stops.length) { tr.dir = (-dir) as 1 | -1; tr.next = k + tr.dir; }
        line.trains.push(tr);
        this.group.add(tr.group);
      }
      // repères cliquables invisibles sur les stations
      for (const st of d.stations) {
        const m = new THREE.Mesh(new THREE.SphereGeometry(0.28, 8, 6), new THREE.MeshBasicMaterial({ visible: false }));
        m.position.set(...st.p);
        m.userData = { station: st.name, line: ref, color: d.color };
        this.stationMarkers.push(m);
        this.group.add(m);
      }
      this.lines.push(line);
    }
  }

  private project(pts: THREE.Vector3[], cum: number[], p: THREE.Vector3): number {
    let best = 0, bestD = Infinity;
    const seg = new THREE.Line3(), q = new THREE.Vector3();
    for (let i = 1; i < pts.length; i++) {
      seg.set(pts[i - 1], pts[i]);
      const t = seg.closestPointToPointParameter(p, true);
      seg.at(t, q);
      const d = q.distanceToSquared(p);
      if (d < bestD) { bestD = d; best = cum[i - 1] + t * (cum[i] - cum[i - 1]); }
    }
    return best;
  }

  private at(line: Line, s: number, pos: THREE.Vector3, tan: THREE.Vector3): void {
    const { pts, cum } = line;
    let i = 1;
    while (i < cum.length - 1 && cum[i] < s) i++;
    const t = (s - cum[i - 1]) / Math.max(1e-6, cum[i] - cum[i - 1]);
    pos.lerpVectors(pts[i - 1], pts[i], THREE.MathUtils.clamp(t, 0, 1));
    tan.subVectors(pts[i], pts[i - 1]).normalize();
  }

  private static trainMat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.6, flatShading: true });

  /** Boîte teintée par couleur de sommet : toutes les pièces d'une rame partagent un matériau → 1 seul maillage. */
  private static tinted(w: number, h: number, d: number, y: number, x: number, hex: THREE.ColorRepresentation): THREE.BufferGeometry {
    const g = new THREE.BoxGeometry(w, h, d).translate(x, y, 0);
    const c = new THREE.Color(hex);
    const n = g.getAttribute('position').count;
    g.setAttribute('color', new THREE.Float32BufferAttribute(Array.from({ length: n * 3 }, (_, i) => [c.r, c.g, c.b][i % 3]), 3));
    return g;
  }

  private makeTrain(color: string): THREE.Group {
    const g = new THREE.Group();
    const parts: THREE.BufferGeometry[] = [];
    for (let k = 0; k < 3; k++) {
      const x = (k - 1) * 0.17;
      parts.push(Metro.tinted(0.16, 0.1, 0.13, 0.05, x, 0xf4f4f0));
      parts.push(Metro.tinted(0.162, 0.025, 0.132, 0.03, x, color));
      parts.push(Metro.tinted(0.163, 0.03, 0.1, 0.07, x, 0x2f3a4a));
    }
    const m = new THREE.Mesh(mergeGeometries(parts)!, Metro.trainMat); // 9 boîtes → 1 maillage
    m.castShadow = true;
    g.add(m);
    return g;
  }

  update(dt: number): void {
    const pos = new THREE.Vector3(), tan = new THREE.Vector3();
    for (const line of this.lines) {
      for (const tr of line.trains) {
        if (tr.wait > 0) {
          tr.wait -= dt;
        } else {
          const target = line.stops[tr.next].s;
          const step = SPEED * dt;
          if (Math.abs(target - tr.s) <= step) {
            tr.s = target;
            tr.wait = DWELL;
            if (tr.next + tr.dir < 0 || tr.next + tr.dir >= line.stops.length) tr.dir = (-tr.dir) as 1 | -1; // terminus : demi-tour
            tr.next += tr.dir;
          } else {
            tr.s += Math.sign(target - tr.s) * step;
          }
        }
        this.at(line, tr.s, pos, tan);
        tr.group.position.copy(pos);
        tr.group.rotation.y = Math.atan2(-tan.z, tan.x);
      }
    }
  }

  /** Lignes et stations dans l'ordre du tracé (onglet Métro). */
  list(): { ref: string; color: string; stops: { name: string; p: THREE.Vector3 }[] }[] {
    return this.lines.map((l) => ({ ref: l.ref, color: l.color, stops: l.stops.map(({ name, p }) => ({ name, p })) }));
  }

  /** Position d'une station (pour ancrer la bulle). */
  markerOf(name: string): THREE.Vector3 | null {
    return this.stationMarkers.find((m) => m.userData.station === name)?.position ?? null;
  }

  /** Station touchée par le rayon : { nom, ligne, couleur } ou null. */
  pick(raycaster: THREE.Raycaster): { station: string; line: string; color: string } | null {
    const hit = raycaster.intersectObjects(this.stationMarkers, false)[0];
    return hit ? (hit.object.userData as { station: string; line: string; color: string }) : null;
  }
}
