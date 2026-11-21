import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

/** Objets Meshy posés autour de repères (blender/build_props.py → models/props.glb) :
 *  Plan-de-Cuques (mairie), CESI (terrasse étudiante), calanques (cabanons), et le Canadair pour aerien.ts.
 *  Position relative au centre du lieu repère, posé au sol (rayon vers le bas), tourné de `rot` radians. */
export interface Pose {
  prop: string;
  anchor: string;
  dx: number;
  dz: number;
  rot?: number;
  scale?: number;
  /** cherche la terre ferme si le point tombe dans l'eau */
  land?: boolean;
  /** rayon de l'emprise, pour scripts/place_props.py qui cherche hors ligne un sol plat sans bâtiment (dx/dz ci-dessous en sont le résultat) */
  free?: number;
}

export const POSES: Pose[] = [
  // Plan-de-Cuques : la mairie (où travaille Trystan) à côté de l'église
  // (pétanque, maisons de ville et bastides retirées : anciens modèles trop lourds, texture abîmée par l'allègement)
  { prop: 'mairie_pdc', anchor: 'eglise_plan_de_cuques', dx: 0.67, dz: 0.15, rot: -Math.PI / 2, free: 0.26 },
  // CESI : terrasse étudiante (food truck, tables, vélos) au pied du bâtiment
  { prop: 'terrasse_cesi', anchor: 'cesi', dx: 0.59, dz: 0.40, rot: Math.PI, free: 0.2 },
  // calanques : cabanons de pêcheurs
  { prop: 'cabanon', anchor: 'calanques', dx: -0.6, dz: -0.4, rot: 0.6, land: true },
  { prop: 'cabanon', anchor: 'calanques', dx: -0.2, dz: -0.75, rot: 0.9, land: true },
  { prop: 'cabanon', anchor: 'calanques', dx: 0.5, dz: 0.3, rot: -1.2, land: true },
];

export async function loadProps(
  url: string,
  parent: THREE.Object3D,
  centerOf: (id: string) => THREE.Vector3 | null,
  groundAt: (x: number, z: number) => number,
  seaY = -Infinity,
): Promise<Map<string, THREE.Object3D>> {
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
  const models = new Map<string, THREE.Object3D>();
  gltf.scene.traverse((o) => o.name.startsWith('prop_') && models.set(o.name.slice(5), o));
  for (const m of models.values()) {
    // le nœud garde sa transformation (échelle/décalage de la compression) : on place toujours un parent
    m.traverse((c) => {
      const mesh = c as THREE.Mesh;
      if (mesh.isMesh) mesh.castShadow = mesh.receiveShadow = true;
    });
  }
  for (const p of POSES) {
    const src = models.get(p.prop);
    const c = centerOf(p.anchor);
    if (!src || !c) continue;
    const o = new THREE.Group();
    o.add(src.clone());
    let x = c.x + p.dx, z = c.z + p.dz;
    if (p.land && groundAt(x, z) < seaY + 0.03) {
      // tombé dans l'eau : point de terre ferme le plus proche (spirale autour)
      search: for (let r = 0.08; r < 2; r += 0.08) {
        for (let a = 0; a < Math.PI * 2; a += 0.4) {
          const tx = x + Math.cos(a) * r, tz = z + Math.sin(a) * r;
          if (groundAt(tx, tz) > seaY + 0.03) { x = tx; z = tz; break search; }
        }
      }
    }
    o.position.set(x, groundAt(x, z), z);
    o.rotation.y = p.rot ?? 0;
    o.scale.setScalar(p.scale ?? 1);
    o.name = `pose_${p.prop}`;
    parent.add(o);
  }
  // le Canadair est repris par aerien.ts, dans un parent qu'il peut orienter librement
  const wrapped = new Map<string, THREE.Object3D>();
  for (const [k, m] of models) {
    const g = new THREE.Group();
    g.add(m.clone());
    wrapped.set(k, g);
  }
  return wrapped;
}
