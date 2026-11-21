import * as THREE from 'three';
import { SVGLoader } from 'three/examples/jsm/loaders/SVGLoader.js';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { siGithub, siInstagram, siTiktok } from 'simple-icons';

// LinkedIn n'est plus dans simple-icons : « in » dessiné à la main (même grille 24×24)
const LINKEDIN_PATH =
  'M4 9h3.2v11H4zM5.6 3.6a1.85 1.85 0 1 1 0 3.7 1.85 1.85 0 0 1 0-3.7zM9.6 9h3.1v1.5c.5-.9 1.7-1.8 3.5-1.8 3.2 0 3.8 2.1 3.8 4.8V20h-3.2v-5.6c0-1.4 0-3.1-1.9-3.1s-2.2 1.5-2.2 3V20H9.6z';

const LOGOS = [
  { id: 'instagram', url: 'https://www.instagram.com/trystanbr/', path: siInstagram.path, tile: 0xe1306c, ink: 0xffffff },
  { id: 'tiktok', url: 'https://www.tiktok.com/@trystanbz', path: siTiktok.path, tile: 0x111111, ink: 0xffffff },
  { id: 'linkedin', url: 'https://www.linkedin.com/in/trystan-bouzon-rueda', path: LINKEDIN_PATH, tile: 0x0a66c2, ink: 0xffffff },
  { id: 'github', url: 'https://github.com/trystanbouzonrueda', path: siGithub.path, tile: 0x24292f, ink: 0xffffff },
];

/** Géométrie teintée par couleur de sommet (tuile + logo en un seul maillage, un seul matériau pour les 4). */
function tinted(g: THREE.BufferGeometry, hex: number): THREE.BufferGeometry {
  const n = g.index ? g.toNonIndexed() : g;
  n.deleteAttribute('uv');
  const c = new THREE.Color(hex);
  const a = new Float32Array(n.getAttribute('position').count * 3);
  for (let i = 0; i < a.length; i += 3) a.set([c.r, c.g, c.b], i);
  n.setAttribute('color', new THREE.BufferAttribute(a, 3));
  return n;
}

function roundedSquare(s: number, r: number): THREE.Shape {
  const h = s / 2;
  const sh = new THREE.Shape();
  sh.moveTo(-h + r, -h);
  sh.lineTo(h - r, -h); sh.quadraticCurveTo(h, -h, h, -h + r);
  sh.lineTo(h, h - r); sh.quadraticCurveTo(h, h, h - r, h);
  sh.lineTo(-h + r, h); sh.quadraticCurveTo(-h, h, -h, h - r);
  sh.lineTo(-h, -h + r); sh.quadraticCurveTo(-h, -h, -h + r, -h);
  return sh;
}

function logoGeometry(path: string, tile: number, ink: number): THREE.BufferGeometry {
  const T = 1; // tuile de 1 × 1, mise à l'échelle par le groupe
  const tileGeo = new THREE.ExtrudeGeometry(roundedSquare(T, 0.24), { depth: 0.12, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2, curveSegments: 6 });
  tileGeo.translate(0, 0, -0.06);
  // logo : chemin SVG 24×24 (y vers le bas) → formes, centré, 62 % de la tuile, posé en relief sur la face avant
  const shapes = new SVGLoader().parse(`<svg xmlns="http://www.w3.org/2000/svg"><path d="${path}"/></svg>`).paths.flatMap((p) => p.toShapes());
  const ink3 = new THREE.ExtrudeGeometry(shapes, { depth: 0.6, bevelEnabled: false, curveSegments: 5 });
  const k = (T * 0.62) / 24;
  ink3.scale(k, -k, k).translate(-12 * k, 12 * k, 0.1);
  return mergeGeometries([tinted(tileGeo, tile), tinted(ink3, ink)])!;
}

/** Logos des réseaux qui flottent au-dessus du Dôme ; un clic ouvre le réseau dans un nouvel onglet. */
export class Reseaux {
  readonly group = Object.assign(new THREE.Group(), { name: 'reseaux' });
  private items: { mesh: THREE.Mesh; url: string; phase: number }[] = [];

  build(anchor: THREE.Vector3, size = 0.42): void {
    const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.45, metalness: 0.05, flatShading: true });
    const gap = size * 1.35;
    LOGOS.forEach((l, i) => {
      const mesh = new THREE.Mesh(logoGeometry(l.path, l.tile, l.ink), mat);
      mesh.scale.setScalar(size);
      mesh.position.set((i - (LOGOS.length - 1) / 2) * gap, 0, 0);
      mesh.castShadow = true;
      mesh.userData.url = l.url;
      this.group.add(mesh);
      this.items.push({ mesh, url: l.url, phase: i * 0.9 });
    });
    this.group.position.copy(anchor);
  }

  /** Flottement doux, rangée tournée vers la caméra (seulement en lacet), léger balancement de chaque logo. */
  update(elapsed: number, camera: THREE.Camera): void {
    if (!this.items.length) return;
    this.group.lookAt(camera.position); // face à la caméra, même vue d'en haut
    for (const it of this.items) {
      it.mesh.position.y = Math.sin(elapsed * 1.3 + it.phase) * 0.05;
      it.mesh.rotation.y = Math.sin(elapsed * 0.8 + it.phase) * 0.35;
    }
  }

  /** URL du logo sous le rayon, sinon null. */
  pick(raycaster: THREE.Raycaster): string | null {
    const hit = raycaster.intersectObjects(this.items.map((i) => i.mesh), false)[0];
    return hit ? (hit.object.userData.url as string) : null;
  }
}
