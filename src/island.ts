import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { bakedGeometry, mergeDeep } from './merge';

/** Sols plats : ne projettent pas d'ombre (économise la passe d'ombre). */
const FLAT = /^(voirie_|ile_sol|plateau_|iles$|stations)/;
/** Tuiles fusionnées par matériau sur une grille de cette taille (garde le frustum culling). */
const MERGE_CELL = 12;


const PLACE_PREFIX = 'place_';
// Matériaux qui s'allument la nuit (noms Blender sans le préfixe « M_ »)
const NIGHT_GLOW: Record<string, { color: number; strength: number }> = {
  fenetre: { color: 0xffc56b, strength: 2.6 },
  fenetre_sombre: { color: 0xffbf5e, strength: 2.4 }, // fenêtres des quartiers : la ville s'allume
  lampadaire: { color: 0xffd27a, strength: 1.0 },
  jaune: { color: 0xffd27a, strength: 2.2 },
  or: { color: 0xffd36a, strength: 0.9 },
  verre: { color: 0xffd7a0, strength: 0.55 },
  verre_bureau: { color: 0xdcecff, strength: 0.7 }, // bureaux : lumière froide, douce (grandes surfaces)
  verre_fonce: { color: 0xcfe2ff, strength: 0.5 },
  vitre_cesi: { color: 0xe6f1ff, strength: 0.8 },
};

/** Fenêtres dessinées par le shader sur les façades des arrondissements, la nuit : grille au pas d'un étage,
 *  une fenêtre sur deux ou trois allumée au hasard, teintes chaudes variées. Trop petites à l'écran → leur moyenne
 *  (lueur de ville habitée). Près de la caméra, elles s'effacent devant les vraies fenêtres des détails. */
const WINDOWS_GLSL = `
  vec3 wFn = normalize(cross(dFdx(vWPos), dFdy(vWPos)));
  float wWall = 1.0 - smoothstep(0.2, 0.45, abs(wFn.y));
  vec2 wAlong = normalize(vec2(-wFn.z, wFn.x) + 1e-5);
  vec2 wCell = vec2(dot(vWPos.xz, wAlong), vWPos.y - 0.004) / vec2(0.02, 0.0135);
  vec2 wId = floor(wCell);
  vec2 wF = fract(wCell);
  float wH = fract(sin(dot(wId + floor(vWPos.xz * 3.0) * 17.0, vec2(12.9898, 78.233))) * 43758.5453);
  float wLit = step(1.0 - uWinRatio, wH);
  float wShape = step(0.22, wF.x) * step(wF.x, 0.78) * step(0.28, wF.y) * step(wF.y, 0.82);
  float wPx = max(length(fwidth(wCell)), 1e-4);
  float wPattern = mix(wShape * wLit, 0.16 * uWinRatio, smoothstep(0.3, 0.8, wPx)); // de loin : lueur plus discrète que la somme
  vec3 wCol = mix(vec3(1.0, 0.66, 0.32), vec3(1.0, 0.88, 0.62), fract(wH * 7.13));
  float wFar = uWinNear > 0.0 ? smoothstep(uWinNear * 0.7, uWinNear, distance(vWPos, cameraPosition)) : 1.0;
  totalEmissiveRadiance += wCol * wPattern * wWall * wFar * uNight * uWinStrength;
`;

interface PlaceState {
  node: THREE.Object3D;
  baseY: number;
  baseRotY: number;
  lift: number; // 0 → 1
  vel: number; // vitesse du ressort
  meshes: THREE.Mesh[];
}

export class Island {
  readonly group = Object.assign(new THREE.Group(), { name: 'island' });
  readonly places = new Map<string, PlaceState>();
  selected: string | null = null;
  /** lieu survolé à la souris : il se soulève aussi, sans ouvrir sa rubrique */
  hovered: string | null = null;
  private glowing: { mat: THREE.MeshStandardMaterial; color: THREE.Color; strength: number }[] = [];
  private seen = new Set<THREE.Material>();
  /** Détails (fenêtres, balcons…) d'un quartier : affichés seulement quand la caméra est proche. */
  private details: { mesh: THREE.Mesh; box: THREE.Box3 }[] = [];
  private nightLevel = 0;
  /** Temps partagé par le shader de l'eau. */
  readonly waterTime = { value: 0 };
  /** Uniformes partagés des fenêtres du shader (nuit, intensité, distance où les vraies fenêtres prennent le relais). */
  readonly windows = {
    uNight: { value: 0 },
    uWinStrength: { value: 2.0 },
    uWinRatio: { value: 0.5 },
    uWinNear: { value: 0 },
  };
  private winMat: THREE.MeshStandardMaterial | null = null;
  private sea: { mat: THREE.MeshStandardMaterial; base: THREE.Color } | null = null;

  /** La mer prend un peu la couleur du ciel à l'horizon (orangée au coucher, sombre la nuit). */
  tintSea(sky: THREE.Color, k: number): void {
    if (this.sea) this.sea.mat.color.copy(this.sea.base).lerp(sky, k);
  }
  private groundRay = new THREE.Raycaster();
  detailsLoaded = false;
  private lightMul = 1;

  /** Curseur « lumières de la ville » (0 → 1) : intensité de toutes les lumières et part des fenêtres allumées. */
  setLights(v: number): void {
    this.lightMul = 0.2 + 1.6 * v; // 0,5 → 1 (réglage d'origine), 1 → 1,8
    this.windows.uWinStrength.value = 2.0 * this.lightMul;
    this.windows.uWinRatio.value = 0.15 + 0.7 * v; // 0,5 → la moitié des fenêtres, 1 → 85 %
    this.setNight(this.nightLevel);
  }

  get lights(): number {
    return this.lightMul;
  }

  /** Matériau palette des immeubles avec les fenêtres de nuit (un clone partagé par tous les arrondissements). */
  private windowsMaterial(base: THREE.MeshStandardMaterial): THREE.MeshStandardMaterial {
    if (this.winMat) return this.winMat;
    const m = base.clone();
    m.name = 'palette_bati';
    m.onBeforeCompile = (sh) => {
      Object.assign(sh.uniforms, this.windows);
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vWPos;\nuniform float uNight, uWinStrength, uWinRatio, uWinNear;')
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n' + WINDOWS_GLSL);
    };
    m.customProgramCacheKey = () => 'palette_bati';
    this.winMat = m;
    return m;
  }

  /** Mer vivante : houle lente (nuances de bleu) et reflets qui scintillent, calculés en coordonnées monde. */
  private animateWater(mat: THREE.MeshStandardMaterial): void {
    mat.flatShading = false;
    mat.onBeforeCompile = (sh) => {
      sh.uniforms.uTime = this.waterTime;
      sh.vertexShader = sh.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vWater;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvWater = (modelMatrix * vec4(transformed, 1.0)).xyz;');
      sh.fragmentShader = sh.fragmentShader
        .replace('#include <common>', '#include <common>\nuniform float uTime;\nvarying vec3 vWater;')
        .replace('#include <color_fragment>', `#include <color_fragment>
  vec2 q = vWater.xz;
  float w = sin(q.x * 1.7 + uTime * 0.7) * sin(q.y * 1.4 - uTime * 0.5) + 0.5 * sin((q.x + q.y) * 4.3 + uTime * 1.3);
  diffuseColor.rgb *= 0.93 + 0.07 * w;
  vec2 r = q + 0.6 * vec2(sin(q.y * 2.3 + uTime * 0.3), sin(q.x * 2.9 - uTime * 0.25));
  float sp = sin(r.x * 17.0 - uTime * 1.6) * sin(r.y * 13.0 + uTime * 1.2) + 0.7 * w;
  diffuseColor.rgb += smoothstep(1.45, 1.65, sp) * 0.14;`);
    };
    mat.needsUpdate = true;
  }

  async load(url: string, onProgress?: (ratio: number) => void): Promise<void> {
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(url, (e) => e.total && onProgress?.(e.loaded / e.total));
    const root = gltf.scene;
    const seen = this.seen;
    root.traverse((obj) => {
      if (obj.name.startsWith(PLACE_PREFIX) && !obj.name.startsWith('place_arr')) {
        const meshes: THREE.Mesh[] = [];
        obj.traverse((c) => (c as THREE.Mesh).isMesh && meshes.push(c as THREE.Mesh));
        this.places.set(obj.name.slice(PLACE_PREFIX.length), {
          node: obj, baseY: obj.position.y, baseRotY: obj.rotation.y, lift: 0, vel: 0, meshes,
        });
      }
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh) return;
      let top: THREE.Object3D = mesh;
      while (top.parent && top.parent !== root) top = top.parent;
      mesh.castShadow = !FLAT.test(top.name);
      mesh.receiveShadow = true;
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (seen.has(m)) continue;
        seen.add(m);
        const mat = m as THREE.MeshStandardMaterial;
        if (!mat.map) mat.flatShading = true; // couleurs unies : look low-poly facetté
        mat.needsUpdate = true;
        const key = mat.name.replace(/^M_/, '').replace(/\.\d+$/, '');
        if (key === 'mer' || key === 'cascade') {
          // mer opaque : le plateau a un fond, et la transparence délavait la ville avec le ciel
          mat.transparent = key !== 'mer';
          mat.opacity = key === 'mer' ? 1 : 0.75;
          if (key === 'mer') {
            mat.color.offsetHSL(0.01, 0.08, -0.12); // compense l'éclaircissement du tone mapping
            this.sea = { mat, base: mat.color.clone() };
            this.animateWater(mat);
          }
          mesh.castShadow = false;
        }
        const glow = NIGHT_GLOW[key];
        if (glow) this.glowing.push({ mat, color: new THREE.Color(glow.color), strength: glow.strength });
      }
    });
    this.mergeStatic(root);
    // lieux à rubrique : leurs petites pièces (gradins, lisses, allées…) → un maillage par matériau sous le nœud,
    // qui reste l'unité soulevée/surlignée au clic
    for (const p of this.places.values()) {
      mergeDeep(p.node);
      p.meshes = [];
      p.node.traverse((c) => (c as THREE.Mesh).isMesh && p.meshes.push(c as THREE.Mesh));
    }
    // immeubles des arrondissements : fenêtres de nuit dessinées par le shader
    root.traverse((o) => {
      const mesh = o as THREE.Mesh;
      if (!mesh.isMesh) return;
      let inArr = false;
      for (let p: THREE.Object3D | null = mesh; p && !inArr; p = p.parent) inArr = p.name.startsWith('place_arr');
      if (!inArr) return;
      const mat = mesh.material as THREE.MeshStandardMaterial;
      if (!Array.isArray(mesh.material) && mat.name.startsWith('palette') && mat.vertexColors) mesh.material = this.windowsMaterial(mat);
    });
    // décor immobile : matrices calculées une fois (des milliers d'objets de moins à recomposer à chaque frame) ;
    // les lieux place_* gardent la mise à jour auto (soulèvement au clic), leurs enfants suivent via le parent
    root.updateMatrixWorld(true);
    root.traverse((o) => {
      if (o.name.startsWith(PLACE_PREFIX)) return;
      o.updateMatrix();
      o.matrixAutoUpdate = false;
    });
    this.group.add(root);
  }

  /** Fusionne les tuiles de voirie (même matériau, même case de grille) : ~225 draw calls → quelques dizaines par passe. */
  private mergeStatic(root: THREE.Object3D): void {
    root.updateMatrixWorld(true);
    const toRoot = new THREE.Matrix4().copy(root.matrixWorld).invert();
    const buckets = new Map<string, { mat: THREE.Material; meshes: THREE.Mesh[] }>();
    root.traverse((obj) => {
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh || Array.isArray(mesh.material)) return;
      let named: THREE.Object3D | null = mesh;
      while (named && !named.name.startsWith('voirie_')) named = named.parent;
      if (!named) return;
      const c = new THREE.Box3().setFromObject(mesh).getCenter(new THREE.Vector3());
      const key = `${mesh.material.uuid}|${Math.floor(c.x / MERGE_CELL)}|${Math.floor(c.z / MERGE_CELL)}`;
      const b = buckets.get(key) ?? { mat: mesh.material, meshes: [] };
      b.meshes.push(mesh);
      buckets.set(key, b);
    });
    for (const { mat, meshes } of buckets.values()) {
      if (meshes.length < 2) continue;
      const geos = meshes.map((m) => bakedGeometry(m.geometry, new THREE.Matrix4().multiplyMatrices(toRoot, m.matrixWorld)));
      const attrs = Object.keys(geos[0].attributes).join();
      if (geos.some((g) => Object.keys(g.attributes).join() !== attrs)) continue;
      const merged = mergeGeometries(geos);
      if (!merged) continue;
      const m = new THREE.Mesh(merged, mat);
      m.name = 'voirie_fusion';
      m.castShadow = false;
      m.receiveShadow = true;
      root.add(m);
      for (const old of meshes) {
        old.removeFromParent();
        old.geometry.dispose();
      }
    }
  }

  /**
   * Monuments Meshy (blender/build_monuments_meshy.py) à la place des monuments faits main : même nœud place_<id>
   * (soulèvement, contour, bulles, clic inchangés), même emprise au sol. Allongement aligné sur l'ancien, puis
   * `turn[id]` quarts de tour en plus si la façade regarde du mauvais côté.
   */
  /** Lance le téléchargement d'un GLB tout de suite (en parallèle de la ville), à passer ensuite à replaceMonuments. */
  static preload(url: string): Promise<GLTF> {
    return new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
  }

  async replaceMonuments(
    src: string | Promise<GLTF>,
    turn: Record<string, number> = {},
    tune: Record<string, { scale?: number; sink?: number; fit?: number }> = {},
  ): Promise<string[]> {
    const gltf = typeof src === 'string' ? await Island.preload(src) : await src;
    const models = new Map<string, THREE.Object3D>();
    gltf.scene.traverse((o) => o.name.startsWith('mon_') && models.set(o.name.slice(4), o));
    const done: string[] = [];
    const v = new THREE.Vector3();
    for (const [id, model] of models) {
      const p = this.places.get(id);
      const box = this.box(id);
      if (!p || !box) continue;
      p.node.updateMatrixWorld(true);
      // emprise de l'ancien monument dans le repère du nœud (au repos)
      const lift = p.node.position.y - p.baseY;
      const local = box.clone().translate(v.set(0, lift, 0)).applyMatrix4(p.node.matrixWorld.clone().invert());
      const size = local.getSize(new THREE.Vector3());
      const center = local.getCenter(new THREE.Vector3());
      // le nœud garde sa transformation (échelle/décalage de la compression) : on le tourne via un parent
      model.removeFromParent();
      const spin = new THREE.Group();
      spin.add(model);
      const mb = new THREE.Box3().setFromObject(spin).getSize(new THREE.Vector3());
      const oldLong = size.x >= size.z, newLong = mb.x >= mb.z;
      const quarter = (oldLong !== newLong ? 1 : 0) + (turn[id] ?? 0);
      const holder = new THREE.Group();
      holder.name = `meshy_${id}`;
      spin.rotation.y = (quarter * Math.PI) / 2;
      const footprint = quarter % 2 ? Math.max(mb.z, mb.x) : Math.max(mb.x, mb.z);
      holder.scale.setScalar((Math.max(size.x, size.z) / footprint) * (tune[id]?.scale ?? 1));
      holder.position.set(center.x, local.min.y, center.z);
      holder.add(spin);
      for (const m of p.meshes) m.removeFromParent();
      p.node.add(holder);
      // posé sur le terrain réellement sous son centre (l'ancien monument pouvait descendre dans une colline)
      const cw = p.node.localToWorld(center.clone());
      const groundY = (x: number, z: number): number | null => {
        this.groundRay.set(new THREE.Vector3(x, cw.y + 100, z), new THREE.Vector3(0, -1, 0));
        const h = this.groundRay.intersectObject(this.group, true).find((hh) => {
          if (!(hh.object as THREE.Mesh).isMesh || !hh.object.visible) return false;
          for (let o: THREE.Object3D | null = hh.object; o; o = o.parent) if (o === p.node) return false;
          return true;
        });
        return h ? h.point.y : null;
      };
      // fit : sur une colline, on pose la base à la hauteur moyenne d'un cercle autour du centre (fraction du rayon)
      // → le socle s'enfonce au sommet et rejoint les pentes, au lieu de déborder au-dessus d'elles
      let gy = groundY(cw.x, cw.z);
      const fit = tune[id]?.fit;
      if (fit && gy !== null) {
        const rr = (new THREE.Box3().setFromObject(holder).getSize(new THREE.Vector3()).x / 2) * fit;
        const ring: number[] = [];
        for (let k = 0; k < 12; k++) {
          const y = groundY(cw.x + Math.cos((k / 12) * Math.PI * 2) * rr, cw.z + Math.sin((k / 12) * Math.PI * 2) * rr);
          if (y !== null) ring.push(y);
        }
        if (ring.length) gy = ring.reduce((a, b) => a + b, 0) / ring.length;
      }
      if (gy !== null) {
        const yLocal = p.node.worldToLocal(new THREE.Vector3(cw.x, gy, cw.z)).y;
        const h = new THREE.Box3().setFromObject(holder).getSize(new THREE.Vector3()).y;
        holder.position.y = yLocal - h * (tune[id]?.sink ?? 0.02); // un peu enfoncé : le socle ne flotte pas sur les pentes
      }
      const meshes: THREE.Mesh[] = [];
      holder.traverse((c) => {
        const m = c as THREE.Mesh;
        if (!m.isMesh) return;
        m.castShadow = m.receiveShadow = true;
        meshes.push(m);
      });
      p.meshes = meshes;
      done.push(id);
    }
    return done;
  }

  /** Charge les détails après l'affichage de la ville (chargement progressif). */
  async loadDetails(url: string): Promise<void> {
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const gltf = await loader.loadAsync(url);
    const root = gltf.scene;
    this.group.add(root);
    root.updateMatrixWorld(true);
    root.traverse((obj) => {
      obj.matrixAutoUpdate = false; // détails immobiles
      const mesh = obj as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.castShadow = false; // trop fins pour porter une ombre utile
      mesh.receiveShadow = true;
      mesh.visible = false;
      this.details.push({ mesh, box: new THREE.Box3().setFromObject(mesh) });
      for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
        if (this.seen.has(m)) continue;
        this.seen.add(m);
        const mat = m as THREE.MeshStandardMaterial;
        const glow = NIGHT_GLOW[mat.name.replace(/^M_/, '').replace(/\.\d+$/, '')];
        if (glow) this.glowing.push({ mat, color: new THREE.Color(glow.color), strength: glow.strength });
      }
    });
    this.setNight(this.nightLevel);
    this.detailsLoaded = true;
  }

  /** Affiche les détails des quartiers proches de la caméra (coordonnées monde). */
  updateDetails(camPos: THREE.Vector3, range: number): void {
    // tant que les vraies fenêtres ne sont pas là, celles du shader restent visibles même de près
    this.windows.uWinNear.value = this.detailsLoaded ? range : 0;
    const local = this.group.worldToLocal(camPos.clone());
    for (const d of this.details) d.mesh.visible = d.box.distanceToPoint(local) < range;
  }

  /** 0 = jour, 1 = nuit */
  setNight(f: number): void {
    this.nightLevel = f;
    this.windows.uNight.value = f;
    for (const g of this.glowing) {
      g.mat.emissive.copy(g.color);
      g.mat.emissiveIntensity = g.strength * f * this.lightMul;
    }
  }

  /** Lieu (ou arrondissement « arrNN ») touché par le rayon, avec le point d'impact. */
  pickHit(raycaster: THREE.Raycaster): { id: string; point: THREE.Vector3 } | null {
    const hit = raycaster.intersectObject(this.group, true).find((h) => h.object.visible);
    for (let o: THREE.Object3D | null = hit?.object ?? null; o; o = o.parent) {
      if (o.name.startsWith(PLACE_PREFIX)) return { id: o.name.slice(PLACE_PREFIX.length), point: hit!.point.clone() };
    }
    return null;
  }

  /** Lieu touché par le rayon, ou null. */
  pick(raycaster: THREE.Raycaster): string | null {
    const hit = raycaster.intersectObject(this.group, true)[0];
    for (let o: THREE.Object3D | null = hit?.object ?? null; o; o = o.parent) {
      if (o.name.startsWith(PLACE_PREFIX)) return o.name.slice(PLACE_PREFIX.length);
    }
    return null;
  }

  /** Meshes du lieu (pour le contour lumineux). */
  meshesOf(id: string): THREE.Mesh[] {
    return this.places.get(id)?.meshes ?? [];
  }

  /** Boîte englobante du lieu, position de repos (sans le soulèvement). */
  box(id: string): THREE.Box3 | null {
    const p = this.places.get(id);
    if (!p) return null;
    const box = new THREE.Box3().setFromObject(p.node);
    box.translate(new THREE.Vector3(0, -(p.node.position.y - p.baseY), 0));
    return box.isEmpty() ? null : box;
  }

  /** Animation de sélection : le lieu choisi se soulève, rebondit et se dandine. */
  update(dt: number, t: number, motion: number): void {
    this.waterTime.value = t;
    for (const [id, p] of this.places) {
      const up = id === this.selected || id === this.hovered;
      const target = up ? 1 : 0;
      // ressort amorti → petit rebond à l'arrivée
      p.vel += ((target - p.lift) * 90 - p.vel * 11) * dt;
      p.lift += p.vel * dt;
      if (Math.abs(p.lift) < 1e-4 && target === 0) {
        p.lift = 0;
        p.vel = 0;
      }
      const size = p.node.scale.y; // les lieux sont à l'échelle 1, mais au cas où
      const hover = up ? Math.sin(t * 2.4) * 0.04 * motion : 0;
      p.node.position.y = p.baseY + (p.lift * 0.35 + hover) * size;
      p.node.rotation.y = p.baseRotY + p.lift * Math.sin(t * 1.6) * 0.12 * motion;
    }
  }
}

/** Petits nuages low-poly qui tournent autour de l'île. */
export function makeClouds(count: number, scale = 1): THREE.Group {
  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, flatShading: true, roughness: 1 });
  const geo = new THREE.IcosahedronGeometry(1, 0);
  for (let i = 0; i < count; i++) {
    const cloud = new THREE.Group();
    const puffs = 3 + Math.floor(Math.random() * 3);
    for (let k = 0; k < puffs; k++) {
      const p = new THREE.Mesh(geo, mat);
      const s = 0.7 + Math.random() * 0.8;
      p.scale.set(s * 1.3, s * 0.75, s);
      p.position.set((k - puffs / 2) * 1.0, Math.random() * 0.35, Math.random() * 0.6 - 0.3);
      cloud.add(p);
    }
    const a = (i / count) * Math.PI * 2 + Math.random() * 0.5;
    const r = (17 + Math.random() * 8) * scale;
    cloud.position.set(6 + Math.cos(a) * r, (-6 + Math.random() * 9) * scale * 0.6, 4 + Math.sin(a) * r);
    cloud.rotation.y = -a;
    cloud.scale.setScalar((0.4 + Math.random() * 0.4) * scale);
    group.add(cloud);
  }
  mergeDeep(group); // ~60 bouffées → 1 maillage
  return group;
}
