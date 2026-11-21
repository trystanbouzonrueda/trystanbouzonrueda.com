import * as THREE from 'three';
import { mergeDeep } from './merge';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';

/** Grand panneau façon « Hollywood » sur une colline au nord-est, visible depuis la vue d'ouverture :
 *  le nom de domaine en lettres blanches en blocs (pixels d'un canvas → petits cubes), chaque lettre sur deux poteaux,
 *  posée sur le relief et tournée vers la caméra d'ouverture. Légèrement lumineux la nuit. */

const TEXT = 'trystanbouzonrueda.com';
const ROWS = 15; // résolution verticale d'une lettre (en blocs) : assez pour distinguer n et r de loin

/** Pixels allumés d'un caractère, en grille (x, y depuis le bas). */
function glyph(ch: string): { w: number; cells: [number, number][] } {
  const c = document.createElement('canvas');
  const H = 64;
  c.width = 64;
  c.height = H;
  const g = c.getContext('2d')!;
  g.font = `900 ${H * 0.9}px system-ui, Arial, sans-serif`;
  g.textBaseline = 'alphabetic';
  const w = Math.ceil(g.measureText(ch).width) + 2;
  g.fillStyle = '#fff';
  g.fillText(ch, 1, H * 0.78);
  const data = g.getImageData(0, 0, c.width, H).data;
  const step = H / ROWS / 0.78; // le corps du texte occupe ~78 % de la hauteur
  const cols = Math.max(1, Math.round(w / step));
  const cells: [number, number][] = [];
  for (let gy = 0; gy < Math.ceil(H / step); gy++) {
    for (let gx = 0; gx < cols; gx++) {
      let on = 0, n = 0;
      for (let py = Math.floor(gy * step); py < Math.min(H, (gy + 1) * step); py++) {
        for (let px = Math.floor(gx * step); px < Math.min(w, (gx + 1) * step); px++) {
          on += data[(py * c.width + px) * 4 + 3] > 128 ? 1 : 0;
          n++;
        }
      }
      if (n && on / n > 0.42) cells.push([gx, Math.ceil(H / step) - 1 - gy]);
    }
  }
  return { w: cols, cells };
}

export class Panneau {
  readonly group = Object.assign(new THREE.Group(), { name: 'panneau' });
  private mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.6, flatShading: true, emissive: 0xfff4e0, emissiveIntensity: 0 });

  /**
   * @param center point au sol au milieu du panneau
   * @param facing point vers lequel les lettres sont tournées (caméra d'ouverture)
   * @param height hauteur d'une lettre majuscule (unités de l'île)
   */
  build(center: THREE.Vector3, facing: THREE.Vector3, height: number, groundAt: (x: number, z: number) => number): void {
    const cell = height / ROWS;
    const depth = cell * 1.2;
    const box = new THREE.BoxGeometry(cell * 0.96, cell * 0.96, depth);
    const glyphs = [...TEXT].map(glyph);
    const gap = 1.2; // blocs entre deux lettres
    const total = glyphs.reduce((a, g) => a + g.w + gap, -gap) * cell;
    // axe du panneau : perpendiculaire à la direction de vue (dans le plan horizontal)
    const view = new THREE.Vector3(facing.x - center.x, 0, facing.z - center.z).normalize();
    const along = new THREE.Vector3(view.z, 0, -view.x); // droite de l'observateur : le texte se lit de gauche à droite
    const yaw = Math.atan2(view.x, view.z);
    const post = new THREE.BoxGeometry(cell * 0.5, 1, cell * 0.5);
    const postMat = new THREE.MeshStandardMaterial({ color: 0x8a8f99, roughness: 0.8, flatShading: true });
    let x = -total / 2;
    for (const g of glyphs) {
      if (g.cells.length) {
        const parts = g.cells.map(([cx, cy]) => box.clone().translate((cx + 0.5) * cell, (cy + 0.5) * cell, 0));
        const letter = new THREE.Mesh(mergeGeometries(parts)!, this.mat);
        letter.castShadow = true;
        const mid = x + (g.w * cell) / 2;
        const p = center.clone().addScaledVector(along, mid);
        const gy = groundAt(p.x, p.z);
        const lift = height * 0.35; // lettres sur poteaux, au-dessus du maquis
        const holder = new THREE.Group();
        holder.position.set(p.x, gy + lift, p.z);
        holder.rotation.set(-0.08, yaw, 0); // légèrement penchées en arrière, comme sur une pente
        letter.position.set((-g.w * cell) / 2, 0, 0);
        holder.add(letter);
        for (const side of [0.25, 0.75]) {
          const ps = new THREE.Mesh(post, postMat);
          ps.scale.y = lift + cell;
          ps.position.set((side - 0.5) * g.w * cell, -lift / 2 + cell / 2, -depth);
          ps.castShadow = true;
          holder.add(ps);
        }
        this.group.add(holder);
      }
      x += (g.w + gap) * cell;
    }
    mergeDeep(this.group); // ~66 maillages → 2 (lettres, poteaux) : le panneau ne bouge jamais
  }

  setNight(f: number): void {
    this.mat.emissiveIntensity = 0.9 * f;
  }
}
