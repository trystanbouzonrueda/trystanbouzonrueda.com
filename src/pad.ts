import { onLang, t } from './i18n';

/** Deux joysticks tactiles (écrans tactiles seulement) :
 *  gauche = se déplacer (avant/arrière, décalage), droite = tourner (gauche/droite) et zoomer (haut/bas).
 *  Valeurs analogiques dans [-1, 1], lues à chaque frame par la balade de main.ts. */
export class Pad {
  readonly move = { x: 0, y: 0 }; // y > 0 : avancer
  readonly look = { x: 0, y: 0 }; // x > 0 : tourner à droite, y > 0 : s'approcher
  readonly el: HTMLElement;
  private onUse: () => void;

  constructor(parent: HTMLElement, onUse: () => void) {
    this.onUse = onUse;
    this.el = document.createElement('div');
    this.el.className = 'pad';
    this.el.setAttribute('aria-hidden', 'true'); // la carte, le métro et les rubriques restent les accès principaux
    const move = this.stick('pad-move', this.move), look = this.stick('pad-look', this.look);
    const label = (): void => {
      move.querySelector('span')!.textContent = t('déplacer', 'move');
      look.querySelector('span')!.textContent = t('tourner · zoom', 'turn · zoom');
    };
    label();
    onLang(label);
    this.el.append(move, look);
    parent.append(this.el);
  }

  get active(): boolean {
    return this.move.x !== 0 || this.move.y !== 0 || this.look.x !== 0 || this.look.y !== 0;
  }

  private stick(cls: string, out: { x: number; y: number }): HTMLElement {
    const base = document.createElement('div');
    base.className = `pad-stick ${cls}`;
    const knob = document.createElement('i');
    const tag = document.createElement('span');
    base.append(knob, tag);
    let id: number | null = null;
    let cx = 0, cy = 0, r = 1;
    const set = (e: PointerEvent): void => {
      let dx = (e.clientX - cx) / r, dy = (e.clientY - cy) / r;
      const l = Math.hypot(dx, dy);
      if (l > 1) { dx /= l; dy /= l; }
      knob.style.transform = `translate(${dx * r * 0.6}px, ${dy * r * 0.6}px)`;
      // petite zone morte, puis réponse progressive (précis au centre, rapide au bord)
      const curve = (v: number): number => (Math.abs(v) < 0.12 ? 0 : Math.sign(v) * ((Math.abs(v) - 0.12) / 0.88) ** 1.5);
      out.x = curve(dx);
      out.y = curve(-dy);
    };
    const end = (e: PointerEvent): void => {
      if (e.pointerId !== id) return;
      id = null;
      out.x = out.y = 0;
      knob.style.transform = '';
      base.classList.remove('on');
    };
    base.addEventListener('pointerdown', (e) => {
      if (id !== null) return;
      id = e.pointerId;
      base.setPointerCapture(id);
      const b = base.getBoundingClientRect();
      cx = b.left + b.width / 2;
      cy = b.top + b.height / 2;
      r = b.width / 2;
      base.classList.add('on');
      this.onUse();
      set(e);
      e.preventDefault();
      e.stopPropagation();
    });
    base.addEventListener('pointermove', (e) => e.pointerId === id && set(e));
    base.addEventListener('pointerup', end);
    base.addEventListener('pointercancel', end);
    return base;
  }
}
