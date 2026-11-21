import * as THREE from 'three';
import { PLACES } from './config';
import type { Island } from './island';

/** Icône de chaque rubrique (traits 24×24, même style que la barre du bas). */
const ICONS: Record<string, string> = {
  apropos: '<circle cx="12" cy="8" r="3.5"/><path d="M5 20c.8-3.8 3.6-6 7-6s6.2 2.2 7 6"/>',
  projets: '<rect x="3.5" y="4.5" width="17" height="11" rx="1.5"/><path d="M8 19.5h8M12 15.5v4"/>',
  parcours: '<path d="M7 3.5h7l4 4v13H7z"/><path d="M14 3.5v4h4M9.5 12h6M9.5 15h6M9.5 18h4"/>',
  formation: '<path d="m2.5 9.5 9.5-4.5 9.5 4.5-9.5 4.5z"/><path d="M6.5 11.5v4.5c3 2.5 8 2.5 11 0v-4.5M21.5 9.5v5"/>',
  competences: '<path d="M14.5 6.5a4 4 0 0 0-5.3 5.3L4 17l3 3 5.2-5.2a4 4 0 0 0 5.3-5.3l-2.5 2.5-2.5-.5-.5-2.5z"/>',
  contact: '<rect x="3.5" y="5.5" width="17" height="13" rx="2"/><path d="m4 7 8 6 8-6"/>',
  entreprise: '<rect x="3.5" y="7.5" width="17" height="12" rx="2"/><path d="M9 7.5V5.5h6v2M3.5 12.5h17"/>',
  reseaux: '<circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="m8.2 10.8 7.6-3.6M8.2 13.2l7.6 3.6"/>',
};

/** Bulles à icône au-dessus des bâtiments qui ouvrent une rubrique du portfolio. */
export class Bulles {
  private items: { id: string; el: HTMLButtonElement }[] = [];
  private v = new THREE.Vector3();

  constructor(root: HTMLElement, onPick: (id: string) => void, onHover: () => void) {
    for (const p of PLACES) {
      if (!p.section || !ICONS[p.section]) continue;
      const el = document.createElement('button');
      el.type = 'button';
      el.className = 'bulle glass';
      el.title = p.name;
      el.setAttribute('aria-label', p.name);
      el.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[p.section]}</svg>`;
      // sélection dès l'appui : la bulle peut bouger avec la caméra entre l'appui et le relâchement
      el.addEventListener('pointerdown', (e) => { e.stopPropagation(); e.preventDefault(); onPick(p.id); });
      el.addEventListener('pointerenter', onHover);
      el.addEventListener('keydown', (e) => (e.key === 'Enter' || e.key === ' ') && onPick(p.id));
      root.append(el);
      this.items.push({ id: p.id, el });
    }
  }

  update(camera: THREE.Camera, island: Island, offset: THREE.Vector3, hideId: string | null): void {
    for (const { id, el } of this.items) {
      const box = island.box(id);
      if (!box || id === hideId) { el.hidden = true; continue; }
      box.getCenter(this.v);
      this.v.y = box.max.y + 0.25;
      this.v.add(offset);
      if (this.v.distanceTo(camera.position) > 30) { el.hidden = true; continue; } // trop loin : on n'encombre pas
      this.v.project(camera);
      if (this.v.z > 1 || Math.abs(this.v.x) > 1.05 || this.v.y < -1.05 || this.v.y > 1.8) { el.hidden = true; continue; }
      el.hidden = false;
      // un monument très haut garde sa bulle en haut de l'écran plutôt que de la perdre
      const x = Math.round(((this.v.x + 1) / 2) * innerWidth), y = Math.max(110, Math.round(((1 - this.v.y) / 2) * innerHeight));
      el.style.transform = `translate(${x - 15}px, ${y - 36}px)`;
    }
  }
}
