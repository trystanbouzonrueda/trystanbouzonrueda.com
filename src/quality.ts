import type { Txt } from './i18n';
/** Niveaux de qualité du rendu. « auto » part d'une estimation de l'appareil puis descend
 *  d'un cran si les fps restent bas (jamais de remontée automatique, pour éviter le yo-yo). */
export type Level = 'high' | 'mid' | 'low';
export type QualityChoice = 'auto' | Level;

export interface Profile {
  /** plafond du devicePixelRatio */
  dpr: number;
  /** taille de la carte d'ombre du soleil */
  shadowSize: number;
  /** ombres recalculées toutes les N frames quand la vue est immobile (la vie bouge quand même) */
  shadowEvery: number;
  /** occlusion ambiante (SSAO + passe de normales) */
  ssao: boolean;
  ssaoSamples: number;
  /** flou de maquette haut/bas */
  tiltShift: boolean;
  /** distance d'affichage des détails des quartiers */
  detailRange: number;
  /** part des passants affichés (0–1) */
  crowd: number;
}

export const PROFILES: Record<Level, Profile> = {
  high: { dpr: 2, shadowSize: 4096, shadowEvery: 2, ssao: true, ssaoSamples: 16, tiltShift: true, detailRange: 16, crowd: 1 },
  mid: { dpr: 1.5, shadowSize: 2048, shadowEvery: 3, ssao: true, ssaoSamples: 9, tiltShift: false, detailRange: 11, crowd: 0.6 },
  low: { dpr: 1, shadowSize: 1024, shadowEvery: 4, ssao: false, ssaoSamples: 0, tiltShift: false, detailRange: 7, crowd: 0.3 },
};

export const LEVEL_NAMES: Record<QualityChoice, Txt> = {
  auto: { fr: 'Auto', en: 'Auto' },
  high: { fr: 'Haute', en: 'High' },
  mid: { fr: 'Moyenne', en: 'Medium' },
  low: { fr: 'Basse', en: 'Low' },
};

/** Estimation de départ : téléphone / tablette → moyen, petit GPU ou peu de mémoire → bas. */
export function guessLevel(gl: WebGLRenderingContext | WebGL2RenderingContext): Level {
  const coarse = matchMedia('(pointer: coarse)').matches;
  const mem = (navigator as { deviceMemory?: number }).deviceMemory ?? 8;
  let gpu = '';
  try {
    const ext = gl.getExtension('WEBGL_debug_renderer_info');
    gpu = ext ? String(gl.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : '';
  } catch {
    /* extension refusée : on se fie au reste */
  }
  if (/swiftshader|llvmpipe|software|mali-[gt]?[4-7]\d|adreno \(tm\) [3-5]\d\d|powervr/i.test(gpu) || mem <= 2) return 'low';
  if (coarse || mem <= 4) return 'mid';
  return 'high';
}

/** Surveille les fps (moyenne glissante) et propose de descendre d'un cran. */
export class FpsWatch {
  private acc = 0;
  private n = 0;
  private slow = 0;
  private grace = 4; // secondes ignorées au départ et après chaque changement (compilation des shaders)
  private crawl = 0; // secondes d'affilée sous 20 fps (appareil trop faible même en basse qualité)

  constructor(private onDrop: () => void, private onCrawl: () => void = () => {}) {}

  reset(): void {
    this.acc = 0;
    this.n = 0;
    this.slow = 0;
    this.grace = 4;
  }

  /** dt réel (non plafonné) de la frame */
  tick(dt: number): void {
    if (document.hidden) return;
    this.acc += dt;
    this.n++;
    if (this.acc < 1) return;
    const fps = this.n / this.acc;
    this.acc = 0;
    this.n = 0;
    if (this.grace > 0) {
      this.grace--;
      return;
    }
    this.slow = fps < 38 ? this.slow + 1 : 0;
    this.crawl = fps < 20 ? this.crawl + 1 : 0;
    if (this.crawl === 8) this.onCrawl();
    if (this.slow >= 3) {
      this.reset();
      this.onDrop();
    }
  }
}
