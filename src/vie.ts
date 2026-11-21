import * as THREE from 'three';
import { mergeDeep } from './merge';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

/** Trajets exportés dans public/data/vie.json (coordonnées three.js, niveau de l'eau). */
interface Route {
  kind: 'navette' | 'ferry' | 'voilier';
  speed: number;
  pts: [number, number, number][];
}

interface Boat {
  kind: Route['kind'];
  group: THREE.Group;
  curve: THREE.CatmullRomCurve3;
  len: number;
  u: number; // 0 → 1 le long du trajet
  dir: 1 | -1;
  speed: number;
  pause: number;
}

const mats = new Map<number, THREE.MeshStandardMaterial>();
const flat = (color: number): THREE.MeshStandardMaterial => {
  let m = mats.get(color);
  if (!m) mats.set(color, (m = new THREE.MeshStandardMaterial({ color, roughness: 0.7, flatShading: true })));
  return m;
};

/** Bateaux qui font l'aller-retour : navettes du Frioul et d'If, ferry de la Joliette, voiliers. */
export class Vie {
  readonly group = Object.assign(new THREE.Group(), { name: 'vie' });
  private boats: Boat[] = [];
  /** niveau de la mer (y des trajets de bateaux) */
  private seaY = 0;
  get sea(): number {
    return this.seaY;
  }

  async load(url: string): Promise<void> {
    const data: Record<string, Route> = await (await fetch(url)).json();
    for (const r of Object.values(data)) {
      this.seaY = r.pts[0][1];
      const curve = new THREE.CatmullRomCurve3(r.pts.map((p) => new THREE.Vector3(...p)), false, 'centripetal');
      const group = this.make(r.kind);
      this.group.add(group);
      this.boats.push({ kind: r.kind, group, curve, len: curve.getLength(), u: Math.random(), dir: 1, speed: r.speed, pause: 0 });
    }
  }

  /** Vrais modèles (Meshy, blender/build_bateaux.py) : remplacent les boîtes une fois chargés. */
  async loadModels(url: string): Promise<void> {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
    const models = new Map<string, THREE.Object3D>();
    gltf.scene.traverse((o) => {
      if (!o.name.startsWith('boat_')) return; // transformation du nœud gardée (échelle/décalage de la compression)
      o.traverse((c) => {
        const m = c as THREE.Mesh;
        if (m.isMesh) m.castShadow = true;
      });
      models.set(o.name.slice(5), o);
    });
    for (const b of this.boats) {
      const m = models.get(b.kind === 'navette' ? 'navette' : b.kind === 'ferry' ? 'ferry' : 'voilier');
      if (!m) continue;
      b.group.clear();
      b.group.add(m.clone());
    }
  }

  /** Phare (Meshy, blender/build_phare.py) posé sur l'eau, rochers compris, à (x, z) en unités de l'île. */
  async loadPhare(url: string, x: number, z: number, rotY = 0): Promise<void> {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
    const phare = gltf.scene;
    phare.traverse((c) => {
      const m = c as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = m.receiveShadow = true;
      const mat = m.material as THREE.MeshStandardMaterial;
      if (!mat.map) mat.flatShading = true;
    });
    phare.position.set(x, this.seaY - 0.03, z);
    phare.rotation.y = rotY;
    phare.name = 'phare';
    this.group.add(phare);
  }

  private make(kind: Route['kind']): THREE.Group {
    const g = new THREE.Group();
    const add = (geo: THREE.BufferGeometry, mat: THREE.Material, x: number, y: number, z: number): void => {
      const m = new THREE.Mesh(geo, mat);
      m.position.set(x, y, z);
      m.castShadow = true;
      g.add(m);
    };
    if (kind === 'ferry') {
      add(new THREE.BoxGeometry(0.9, 0.12, 0.22), flat(0xf4f4f0), 0, 0.06, 0);
      add(new THREE.BoxGeometry(0.55, 0.12, 0.18), flat(0xffffff), -0.05, 0.18, 0);
      add(new THREE.BoxGeometry(0.56, 0.03, 0.185), flat(0x2a6fdb), -0.05, 0.13, 0);
      add(new THREE.BoxGeometry(0.08, 0.1, 0.08), flat(0xd6232a), -0.2, 0.3, 0);
    } else if (kind === 'navette') {
      add(new THREE.BoxGeometry(0.3, 0.06, 0.11), flat(0xffffff), 0, 0.03, 0);
      add(new THREE.BoxGeometry(0.16, 0.06, 0.09), flat(0x2a6fdb), -0.02, 0.09, 0);
    } else {
      add(new THREE.BoxGeometry(0.18, 0.04, 0.06), flat(0xffffff), 0, 0.02, 0);
      add(new THREE.CylinderGeometry(0.004, 0.004, 0.22, 4), flat(0x8a5a3b), 0, 0.15, 0);
      const sail = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.18, 3), flat(0xfaf6ea));
      sail.position.set(0.02, 0.14, 0);
      sail.scale.set(1, 1, 0.15);
      g.add(sail);
    }
    mergeDeep(g);
    return g;
  }

  update(dt: number, t: number): void {
    const pos = new THREE.Vector3(), tan = new THREE.Vector3();
    for (const b of this.boats) {
      if (b.pause > 0) {
        b.pause -= dt;
      } else {
        b.u += (b.dir * b.speed * dt) / b.len;
        if (b.u >= 1 || b.u <= 0) { // quai atteint : pause puis retour
          b.u = THREE.MathUtils.clamp(b.u, 0, 1);
          b.dir = (-b.dir) as 1 | -1;
          b.pause = 3;
        }
      }
      b.curve.getPointAt(b.u, pos);
      b.curve.getTangentAt(b.u, tan).multiplyScalar(b.dir);
      b.group.position.copy(pos);
      b.group.position.y += Math.sin(t * 2 + b.len) * 0.01; // houle
      b.group.rotation.y = Math.atan2(-tan.z, tan.x);
    }
  }
}
