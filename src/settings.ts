import { TIMES } from './config';
import type { QualityChoice } from './quality';

export type Theme = 'light' | 'dark';

export interface Settings {
  time: string;
  theme: Theme;
  quality: QualityChoice;
  /** lumières de la ville la nuit, 0 → 1 (0,5 = réglage d'origine) */
  lights: number;
  /** son d'ambiance (démarre au premier geste) */
  sound: boolean;
}

const KEY = 'portfolio.settings.v3';
/** v2 → v3 : le coucher de soleil devient le moment par défaut ; on garde thème, qualité et lumières déjà choisis */
const OLD_KEY = 'portfolio.settings.v2';

function systemTheme(): Theme {
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function loadSettings(): Settings {
  const defaults: Settings = { time: 'coucher', theme: systemTheme(), quality: 'auto', lights: 0.5, sound: true };
  try {
    let raw = localStorage.getItem(KEY);
    let migrated = false;
    if (!raw) {
      raw = localStorage.getItem(OLD_KEY);
      migrated = !!raw;
    }
    if (!raw) return defaults;
    const saved = JSON.parse(raw) as Partial<Settings>;
    if (migrated) delete saved.time;
    return {
      time: TIMES.some((t) => t.id === saved.time) ? saved.time! : defaults.time,
      theme: saved.theme === 'light' || saved.theme === 'dark' ? saved.theme : defaults.theme,
      quality: (['auto', 'high', 'mid', 'low'] as const).includes(saved.quality as QualityChoice) ? saved.quality! : 'auto',
      lights: typeof saved.lights === 'number' && saved.lights >= 0 && saved.lights <= 1 ? saved.lights : defaults.lights,
      sound: typeof saved.sound === 'boolean' ? saved.sound : defaults.sound,
    };
  } catch {
    return defaults;
  }
}

export function saveSettings(settings: Settings): void {
  try {
    localStorage.setItem(KEY, JSON.stringify(settings));
  } catch {
    /* stockage indisponible (navigation privée) : on ignore */
  }
}

export function applyTheme(theme: Theme): void {
  document.documentElement.dataset.theme = theme;
}
