import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Moins de maillages = moins de draw calls (et chaque objet est dessiné 2 à 4 fois par frame :
 *  ombre, normales du SSAO, rendu, contour). Fusion par matériau, au chargement. */

/** Copie en flottants (les attributs quantifiés du GLB ne supportent pas applyMatrix4), transformée par `matrix`. */
export function bakedGeometry(src: THREE.BufferGeometry, matrix: THREE.Matrix4): THREE.BufferGeometry {
  const g = new THREE.BufferGeometry();
  for (const name of ['position', 'normal', 'uv', 'color'] as const) {
    const a = src.getAttribute(name);
    if (!a) continue;
    const out = new Float32Array(a.count * a.itemSize);
    for (let i = 0; i < a.count; i++) for (let k = 0; k < a.itemSize; k++) out[i * a.itemSize + k] = a.getComponent(i, k);
    g.setAttribute(name, new THREE.BufferAttribute(out, a.itemSize));
  }
  // toujours indexé : mergeGeometries refuse de mélanger indexé et non indexé
  if (src.index) g.setIndex(Array.from(src.index.array as ArrayLike<number>));
  else g.setIndex(Array.from({ length: g.getAttribute('position').count }, (_, i) => i));
  g.applyMatrix4(matrix);
  return g;
}

/** Fusionne une liste de maillages de même matériau en un seul, exprimé dans le repère de `space`. */
function fuse(meshes: THREE.Mesh[], space: THREE.Object3D, mat: THREE.Material): THREE.Mesh | null {
  const inv = new THREE.Matrix4().copy(space.matrixWorld).invert();
  const geos = meshes.map((m) => bakedGeometry(m.geometry, new THREE.Matrix4().multiplyMatrices(inv, m.matrixWorld)));
  const names = Object.keys(geos[0].attributes).sort().join();
  if (geos.some((g) => Object.keys(g.attributes).sort().join() !== names)) return null;
  const merged = mergeGeometries(geos);
  if (!merged) return null;
  const out = new THREE.Mesh(merged, mat);
  out.castShadow = meshes.some((m) => m.castShadow);
  out.receiveShadow = meshes.some((m) => m.receiveShadow);
  return out;
}

const groupByMaterial = (meshes: THREE.Mesh[]): Map<THREE.Material, THREE.Mesh[]> => {
  const by = new Map<THREE.Material, THREE.Mesh[]>();
  for (const m of meshes) {
    if (Array.isArray(m.material)) continue;
    by.set(m.material, [...(by.get(m.material) ?? []), m]);
  }
  return by;
};

/** Groupe rigide (train, bateau, nuages) : tous les maillages descendants → un maillage par matériau sous `root`. */
export function mergeDeep(root: THREE.Object3D): void {
  root.updateMatrixWorld(true);
  const meshes: THREE.Mesh[] = [];
  // seulement ce qui est affiché : un maillage masqué (repère, ancienne version) fusionné deviendrait visible
  root.traverseVisible((o) => (o as THREE.Mesh).isMesh && o !== root && meshes.push(o as THREE.Mesh));
  for (const [mat, list] of groupByMaterial(meshes)) {
    if (list.length < 2) continue;
    const m = fuse(list, root, mat);
    if (!m) continue;
    root.add(m);
    list.forEach((x) => x.removeFromParent());
  }
}

/** Squelette en blocs : sous chaque nœud, fusionne les maillages enfants feuilles et non animés (`keep` = à garder tels quels). */
export function mergeChildren(root: THREE.Object3D, keep: (o: THREE.Object3D) => boolean): void {
  root.updateMatrixWorld(true);
  const parents: THREE.Object3D[] = [];
  root.traverse((o) => parents.push(o));
  for (const p of parents) {
    const leaves = p.children.filter((c) => (c as THREE.Mesh).isMesh && !c.children.length && !keep(c)) as THREE.Mesh[];
    for (const [mat, list] of groupByMaterial(leaves)) {
      if (list.length < 2) continue;
      const m = fuse(list, p, mat);
      if (!m) continue;
      m.name = `${p.name}_fusion`;
      p.add(m);
      list.forEach((x) => x.removeFromParent());
    }
  }
}
