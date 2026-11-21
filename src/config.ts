import type { Txt } from './i18n';

export interface TimeOfDay {
  id: string;
  name: Txt;
  swatch: string; // fond CSS de la pastille
  sky: [string, string]; // dégradé du ciel (haut, bas)
  sun: { color: string; intensity: number; position: [number, number, number] };
  hemi: { sky: string; ground: string; intensity: number };
  env: number; // intensité de l'environnement (reflets)
  night: number; // 0 = jour, 1 = nuit : fenêtres, lampadaires, halo
}

export const TIMES: TimeOfDay[] = [
  {
    id: 'jour',
    name: { fr: 'Jour', en: 'Day' },
    swatch: 'linear-gradient(160deg, #7cc8ff, #fff3c4)',
    sky: ['#6fb8f5', '#d9efff'],
    sun: { color: '#fff4e0', intensity: 2.6, position: [9, 16, 7] },
    hemi: { sky: '#cfe9ff', ground: '#7a9a5a', intensity: 1.1 },
    env: 0.55,
    night: 0,
  },
  {
    id: 'coucher',
    name: { fr: 'Coucher de soleil', en: 'Sunset' },
    swatch: 'linear-gradient(160deg, #ff9a62, #7a4c9e)',
    sky: ['#4f3f86', '#ffa66e'],
    // soleil bas à l'ouest-sud-ouest, derrière la vue d'ouverture : façades dorées, longues ombres vers les collines
    sun: { color: '#ffa25c', intensity: 2.3, position: [-15, 4.2, 9] },
    hemi: { sky: '#ffbe94', ground: '#4f4470', intensity: 0.75 },
    env: 0.35,
    night: 0.4,
  },
  {
    id: 'nuit',
    name: { fr: 'Nuit', en: 'Night' },
    swatch: 'linear-gradient(160deg, #1b2a5c, #05070f)',
    sky: ['#03050d', '#16224a'],
    sun: { color: '#a8bcff', intensity: 0.45, position: [-7, 13, -5] },
    hemi: { sky: '#2c3d73', ground: '#0d1020', intensity: 0.5 },
    env: 0.12,
    night: 1,
  },
];

export interface Place {
  id: string; // correspond au nœud « place_<id> » du modèle
  name: string;
  blurb: Txt;
  section?: string; // rubrique ouverte (voir content.ts) ; absent = simple bulle
}

export const PLACES: Place[] = [
  { id: 'notre_dame', name: 'Notre-Dame-de-la-Garde', blurb: { fr: 'La Bonne Mère veille sur la ville.', en: 'The “Good Mother” watches over the city.' }, section: 'apropos' },
  { id: 'velodrome', name: 'Orange Vélodrome', blurb: { fr: 'Là où ça vibre.', en: 'Where the city roars.' }, section: 'projets' },
  { id: 'gare', name: 'Gare Saint-Charles', blurb: { fr: 'Le voyage, étape par étape.', en: 'The journey, stop by stop.' }, section: 'parcours' },
  { id: 'city_jul', name: 'City stade de Jul', blurb: { fr: 'City stade au bord des plages du Prado, 8ᵉ.', en: 'A street football pitch by the Prado beaches, 8th.' }, section: 'competences' },
  { id: 'vieux_port', name: 'Vieux-Port', blurb: { fr: 'Le cœur de la ville.', en: 'The heart of the city.' }, section: 'contact' },
  { id: 'cma_cgm', name: 'Tour CMA CGM', blurb: { fr: 'Le quartier des affaires.', en: 'The business district.' } },
  { id: 'dome', name: 'Le Dôme', blurb: { fr: 'La soucoupe des concerts.', en: 'The concert hall shaped like a saucer.' }, section: 'reseaux' },
  { id: 'corniche', name: 'Corniche Kennedy', blurb: { fr: 'Le plus long banc du monde.', en: 'The longest bench in the world.' } },
  { id: 'borely', name: 'Parc Borély', blurb: { fr: 'Pelouses, lac et château.', en: 'Lawns, a lake and a château.' } },
  { id: 'david', name: 'Le David', blurb: { fr: 'Au bout du Prado, face à la mer.', en: 'At the end of the Prado, facing the sea.' } },
  { id: 'mucem', name: 'Mucem & fort Saint-Jean', blurb: { fr: 'Dentelle de béton à l’entrée du port.', en: 'Concrete lace at the harbour entrance.' } },
  { id: 'major', name: 'La Major', blurb: { fr: 'La cathédrale aux dômes.', en: 'The cathedral of domes.' } },
  { id: 'calanques', name: 'Calanques', blurb: { fr: 'Falaises blanches, eau turquoise.', en: 'White cliffs, turquoise water.' } },
  { id: 'longchamp', name: 'Palais Longchamp', blurb: { fr: 'Le château d’eau le plus chic de la ville.', en: 'The fanciest water tower in town.' } },
  { id: 'cite_radieuse', name: 'Cité Radieuse', blurb: { fr: 'La « maison du fada » de Le Corbusier.', en: 'Le Corbusier’s “madman’s house”.' } },
  { id: 'tour_marseillaise', name: 'Tour La Marseillaise', blurb: { fr: 'Bleu, blanc, rouge sur Euroméditerranée.', en: 'Blue, white and red over Euroméditerranée.' } },
  { id: 'eglise_plan_de_cuques', name: 'Église de Plan-de-Cuques', blurb: { fr: 'Le clocher du village, la mairie où je travaille juste à côté.', en: 'The village bell tower, with the town hall where I work right next to it.' }, section: 'entreprise' },
  { id: 'cesi', name: 'CESI École d’Ingénieurs', blurb: { fr: 'Mon école, à Aix-en-Provence.', en: 'My engineering school, in Aix-en-Provence.' }, section: 'formation' },
  { id: 'chateau_if', name: 'Château d’If', blurb: { fr: 'La prison de Monte-Cristo, au large.', en: 'The Count of Monte Cristo’s prison, offshore.' } },
  { id: 'navette', name: 'Navette du Frioul', blurb: { fr: 'Cap sur les îles.', en: 'Off to the islands.' } },
];

/** Arrondissements : bulle au clic sur un quartier (objets place_arrNN ; 17 = Plan-de-Cuques). */
export const ARRONDISSEMENTS: Record<number, { name: string; quartiers: string | Txt }> = {
  1: { name: '1ᵉʳ arrondissement', quartiers: 'Canebière, Noailles, Belsunce, Thiers' },
  2: { name: '2ᵉ arrondissement', quartiers: 'Le Panier, la Joliette, Euroméditerranée, Arenc' },
  3: { name: '3ᵉ arrondissement', quartiers: 'Belle de Mai, Saint-Mauront, Saint-Lazare' },
  4: { name: '4ᵉ arrondissement', quartiers: 'Cinq-Avenues, les Chartreux, la Blancarde' },
  5: { name: '5ᵉ arrondissement', quartiers: 'La Plaine, Baille, la Timone, le Camas' },
  6: { name: '6ᵉ arrondissement', quartiers: 'Castellane, Cours Julien, Vauban, Préfecture' },
  7: { name: '7ᵉ arrondissement', quartiers: 'Endoume, Vallon des Auffes, Malmousque, le Pharo' },
  8: { name: '8ᵉ arrondissement', quartiers: 'Prado, Périer, Pointe-Rouge, les Goudes' },
  9: { name: '9ᵉ arrondissement', quartiers: 'Mazargues, Sainte-Marguerite, Luminy, Calanques' },
  10: { name: '10ᵉ arrondissement', quartiers: 'Saint-Loup, la Capelette, Pont-de-Vivaux' },
  11: { name: '11ᵉ arrondissement', quartiers: 'La Valentine, Saint-Marcel, les Camoins' },
  12: { name: '12ᵉ arrondissement', quartiers: 'Saint-Barnabé, les Trois-Lucs, Saint-Julien' },
  13: { name: '13ᵉ arrondissement', quartiers: 'La Rose, Château-Gombert, Malpassé' },
  14: { name: '14ᵉ arrondissement', quartiers: 'Le Merlan, Sainte-Marthe, Saint-Barthélemy' },
  15: { name: '15ᵉ arrondissement', quartiers: 'Saint-Louis, Saint-Antoine, la Viste' },
  16: { name: '16ᵉ arrondissement', quartiers: 'L’Estaque, Saint-Henri, la Castellane' },
  17: { name: 'Plan-de-Cuques', quartiers: { fr: 'La commune voisine, au pied de l’Étoile', en: 'The neighbouring town, at the foot of the Étoile hills' } },
};

export const byId = <T extends { id: string }>(list: T[], id: string): T =>
  list.find((item) => item.id === id) ?? list[0];
