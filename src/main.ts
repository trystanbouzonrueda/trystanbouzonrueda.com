import './style.css';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import {
  BlendFunction,
  BloomEffect,
  EffectComposer,
  EffectPass,
  HueSaturationEffect,
  KernelSize,
  NormalPass,
  TiltShiftEffect,
  OutlineEffect,
  RenderPass,
  SMAAEffect,
  SSAOEffect,
  ToneMappingEffect,
  ToneMappingMode,
} from 'postprocessing';
import { PLACES, TIMES, byId, type TimeOfDay } from './config';
import { sectionById } from './content';
import { onLang, setLang, t, tx } from './i18n';
import { Pad } from './pad';
import { Reseaux } from './reseaux';
import { Island, makeClouds } from './island';
import { Metro } from './metro';
import { Vie } from './vie';
import { Trafic } from './trafic';
import { Bulles } from './bulles';
import { Trystan } from './trystan';
import { Ciel } from './ciel';
import { Passants } from './passants';
import { applyTheme, loadSettings, saveSettings } from './settings';
import { FpsWatch, guessLevel, LEVEL_NAMES, PROFILES, type Level, type QualityChoice } from './quality';
import { mountHud } from './ui';
import { Intro } from './intro';
import { Ligne } from './ligne';
import { Aerien } from './aerien';
import { loadProps } from './props';
import { Panneau } from './panneau';
import { Son } from './son';
import { Feux, multiClick, onKonami, Terminal, toast, Tresors, TRESORS } from './secrets';
import { event, initStats } from './stats';

/** racine du site : « / » en dev et sur le NUC, « ./ » pour une copie publiée ailleurs (vite build --base=./) */
const BASE = import.meta.env.BASE_URL;
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const motion = reducedMotion ? 0 : 1;
const settings = loadSettings();
applyTheme(settings.theme);
initStats();
console.log('%c trystanbouzonrueda.com ', 'background:#0071e3;color:#fff;border-radius:4px;padding:2px 4px', '\nCurieux ? Appuie sur ² (ou `) pour ouvrir le terminal caché.\nCurious? Press ` to open the hidden terminal.');

const canvas = document.querySelector<HTMLCanvasElement>('#scene')!;
const tag = document.querySelector<HTMLElement>('#place-tag')!;
const panel = document.querySelector<HTMLElement>('#panel')!;
const loading = document.querySelector<HTMLElement>('#loading')!;
const hint = document.querySelector<HTMLElement>('#hint')!;

const noWebgl = (): void => {
  document.querySelector('#loading-text')!.textContent = t('La 3D n’est pas disponible sur ce navigateur : direction la version simple…', '3D is not available in this browser: taking you to the simple version…');
  setTimeout(() => location.replace(`${BASE}recruteur/${t('', '?lang=en')}`), 1800);
};
const hasWebgl = ((): boolean => {
  try {
    return !!document.createElement('canvas').getContext('webgl2');
  } catch {
    return false;
  }
})();
if (hasWebgl) {
  start().catch((err) => {
    console.error(err);
    noWebgl();
  });
} else noWebgl();

async function start(): Promise<void> {
  // ---------- rendu
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap; // PCFSoft retiré de three 0.18x (il retombait déjà sur PCF)
  // ombres recalculées à la main : sinon three les refait à chaque rendu de la frame (normales, contour…)
  renderer.shadowMap.autoUpdate = false;

  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

  const hemi = new THREE.HemisphereLight();
  const sun = new THREE.DirectionalLight();
  sun.castShadow = true;
  sun.shadow.mapSize.set(4096, 4096);
  // les blocs unis n'ont pas de normales (ombrage facetté calculé par three) : normalBias n'agit pas,
  // on compense par un biais de profondeur plus fort (sinon « acné » rayée sur les murs)
  sun.shadow.bias = -0.0022;
  sun.shadow.normalBias = 0;
  Object.assign(sun.shadow.camera, { left: -15, right: 15, top: 15, bottom: -15, near: 1, far: 140 });
  scene.add(hemi, sun, sun.target);

  // île fidèle : 1 unité = 250 m. Ouverture rapprochée : Notre-Dame, la mer et le Vélodrome dans le champ,
  // jamais les bords de l'île (recul limité + brouillard couleur d'horizon)
  const camera = new THREE.PerspectiveCamera(35, 1, 0.05, 300);
  // vue d'ouverture choisie par Trystan : depuis la mer au sud-ouest, la Corniche au premier plan, Notre-Dame au centre,
  // le Vélodrome à droite, le Vieux-Port (bulle du métro) et le Mucem à gauche, les collines à l'horizon
  const HOME = { pos: new THREE.Vector3(-15.0, 8.5, 19.0), target: new THREE.Vector3(1.5, 1.8, 5.5) };
  camera.position.copy(HOME.pos);

  const world = new THREE.Group();
  scene.add(world);
  const island = new Island();
  world.add(island.group);
  const clouds = makeClouds(16, 4.5);
  const metro = new Metro();
  world.add(metro.group);
  const vie = new Vie();
  world.add(vie.group);
  const trafic = new Trafic();
  const trystan = new Trystan();
  const ciel = new Ciel();
  world.add(ciel.group);
  const passants = new Passants();
  world.add(passants.group);
  world.add(trystan.group);
  world.add(trafic.group);
  const panneau = new Panneau();
  world.add(panneau.group);
  const reseaux = new Reseaux();
  world.add(reseaux.group);
  const aerien = new Aerien();
  world.add(aerien.group);
  const ligne = new Ligne();
  world.add(ligne.group);
  scene.add(clouds);

  // ---------- son et petits secrets
  const son = new Son(settings.sound);
  const feux = new Feux();
  world.add(feux.group);
  const tresors = new Tresors((n) => {
    if (n === TRESORS.length) event('tresors-complets');
  });
  world.add(tresors.group);
  const soundBtn = document.querySelector<HTMLButtonElement>('#sound-btn')!;
  const syncSound = (): void => {
    soundBtn.setAttribute('aria-pressed', String(son.on));
    const l = son.on ? t('Couper le son', 'Mute sound') : t('Activer le son', 'Turn sound on');
    soundBtn.title = l;
    soundBtn.setAttribute('aria-label', l);
  };
  const setSound = (on: boolean): void => {
    son.setEnabled(on);
    settings.sound = on;
    saveSettings(settings);
    syncSound();
  };
  soundBtn.addEventListener('click', () => setSound(!son.on));
  syncSound();
  onLang(() => {
    syncSound();
    tresors.sync();
  });
  const fireworks = (): void => {
    const b = island.box('vieux_port');
    const c = b ? b.getCenter(new THREE.Vector3()).sub(world.position) : new THREE.Vector3(-1.5, 0, -1);
    c.y = groundAt(c.x, c.z) + 0.1;
    feux.show(c);
    for (let i = 0; i < 4; i++) setTimeout(() => son.play('feu'), i * 900);
    // après les écouteurs du clavier : le « A » final du code Konami est aussi une touche de déplacement (qui couperait le vol)
    if (!island.selected) setTimeout(() => flyTo(c.clone().add(new THREE.Vector3(-6, 5, 7)), c.clone().setY(c.y + 2.2), 1.6), 0);
    toast(t('🎆 Bonne fête, Marseille !', '🎆 Party time in Marseille!'), 3500);
    event('konami');
  };
  onKonami(fireworks);
  const terminal = new Terminal(
    {
      open: (id) => select(id),
      lang: (l) => setLang(l),
      sound: (on) => {
        if (on !== undefined) setSound(on);
        return son.on;
      },
      tresors: () => ({ found: TRESORS.filter((x) => tresors.has(x.id)).map((x) => x.id), total: TRESORS.length }),
      resetTresors: () => tresors.reset(),
      fireworks,
      track: (name) => event(name),
    },
    () => son.play('touche'),
  );
  terminal.longPress(document.querySelector<HTMLElement>('.brand')!);
  const clicks = multiClick();

  island.setLights(settings.lights);
  const bulles = new Bulles(document.querySelector<HTMLElement>('#bulles')!, (id) => select(id), () => (controls.autoRotate = false));
  const fill = document.querySelector<HTMLElement>('#loading-fill')!;
  const loadText = document.querySelector<HTMLElement>('#loading-text')!;
  // monuments Meshy téléchargés en même temps que la ville : posés avant de lever l'écran d'entrée,
  // pour ne jamais montrer les monuments faits main (secours) puis les voir sauter
  const monumentsGltf = Island.preload(`${BASE}models/monuments.glb`);
  monumentsGltf.catch(() => {});
  await island.load(`${BASE}models/marseille.glb`, (r) => {
    fill.style.width = `${Math.round(r * 100)}%`;
    loadText.textContent = r < 1 ? `${t("Chargement de l'île…", 'Loading the island…')} ${Math.round(r * 100)} %` : t('On pose les bâtiments…', 'Placing the buildings…');
  });
  fill.style.width = '100%';
  // monuments Meshy (si le fichier est là) ; la figurine et les quais du métro se calent dessus
  const MONUMENT_TURN: Record<string, number> = {};
  // Notre-Dame : son socle rocheux Meshy mange l'emprise → plus grande, socle fondu dans la colline
  const MONUMENT_TUNE = { notre_dame: { scale: 1.15, sink: 0.02, fit: 0.45 } };
  const monumentsReady = island.replaceMonuments(monumentsGltf, MONUMENT_TURN, MONUMENT_TUNE).catch((e) => {
    console.warn('monuments Meshy indisponibles', e);
    return [] as string[];
  });
  metro.load(`${BASE}data/metro.json`).then(() => monumentsReady).then(() => buildLigne()).catch((e) => console.warn('métro indisponible', e));
  const vieReady = vie.load(`${BASE}data/vie.json`);
  vieReady
    .then(() => Promise.all([vie.loadModels(`${BASE}models/bateaux.glb`), vie.loadPhare(`${BASE}models/phare.glb`, -4.55, -3.05)]))
    .catch((e) => console.warn('bateaux indisponibles', e));
  // panneau du nom de domaine sur les collines de l'horizon, à droite de Notre-Dame dans la vue d'ouverture
  // logos des réseaux au-dessus du Dôme (rubrique Réseaux)
  monumentsReady.then(() => {
    const box = island.box('dome');
    if (box) reseaux.build(box.getCenter(new THREE.Vector3()).sub(world.position).setY(box.max.y - world.position.y + 0.85));
  });
  // trésors : à côté de 5 monuments, du côté de la vue d'ouverture (visibles sans chercher derrière les bâtiments)
  monumentsReady.then(() => {
    const SPOTS: Record<string, [string, number]> = { cadenas: ['notre_dame', -0.9], rj45: ['mucem', 0.6], serveur: ['velodrome', 0.9], usb: ['borely', -0.5], routeur: ['eglise_plan_de_cuques', 0.4] };
    const spots: Record<string, THREE.Vector3> = {};
    for (const [tid, [pid, turn]] of Object.entries(SPOTS)) {
      const b = island.box(pid);
      if (!b) continue;
      const c = b.getCenter(new THREE.Vector3()).sub(world.position);
      const r = Math.max(b.max.x - b.min.x, b.max.z - b.min.z) * 0.62 + 0.25;
      const dir = new THREE.Vector2(HOME.pos.x - c.x, HOME.pos.z - c.z).normalize().rotateAround(new THREE.Vector2(), turn);
      const x = c.x + dir.x * r, z = c.z + dir.y * r;
      spots[tid] = new THREE.Vector3(x, groundAt(x, z), z);
    }
    tresors.place(spots);
  });
  monumentsReady.then(() => panneau.build(new THREE.Vector3(28, 0, -6), HOME.pos, 1.7, (x, z) => groundAt(x, z)));
  // objets Meshy (Plan-de-Cuques, CESI, calanques) et Canadair, une fois le décor en place
  Promise.all([monumentsReady, vieReady])
    .then(() => loadProps(`${BASE}models/props.glb`, world, (id) => island.box(id)?.getCenter(new THREE.Vector3()).sub(world.position) ?? null, (x, z) => groundAt(x, z), vie.sea))
    .then((models) => {
      const c = models.get('canadair');
      if (c) aerien.setCanadair(c, vie.sea);
    })
    .catch((e) => console.warn('objets Meshy indisponibles', e));
  trafic.load(`${BASE}data/trafic.json`).catch((e) => console.warn('circulation indisponible', e));
  passants.load(`${BASE}data/pietons.json`).catch((e) => console.warn('passants indisponibles', e));
  Promise.all([trystan.load(`${BASE}models/trystan.glb`), monumentsReady]).then(() => {
    // sur la terrasse de Notre-Dame, côté ville, tourné vers la vue d'ouverture
    const b = island.box('notre_dame');
    if (!b) return;
    const c = b.getCenter(new THREE.Vector3());
    // sur la terrasse du socle de la basilique (modèle Meshy), côté vue d'ensemble
    const toward = new THREE.Vector2(HOME.pos.x - c.x, HOME.pos.z - c.z).normalize();
    const r = Math.min(b.max.x - c.x, b.max.z - c.z) * 0.38;
    const x = c.x + toward.x * r, z = c.z + toward.y * r;
    trystan.place(x, groundAt(x, z), z, HOME.pos.x - x, HOME.pos.z - z);
  }).catch((e) => console.warn('figurine indisponible', e));

  // ---------- contrôles (mode libre)
  const controls = new OrbitControls(camera, canvas);
  controls.target.copy(HOME.target);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.screenSpacePanning = false;
  controls.minDistance = 1.2;
  controls.maxDistance = 26; // la vue d'ouverture est à 22,3
  controls.minPolarAngle = 0.25;
  controls.maxPolarAngle = 1.3;
  controls.autoRotate = !reducedMotion;
  controls.autoRotateSpeed = 0.3;
  controls.addEventListener('start', () => {
    controls.autoRotate = false;
    flight = null;
    canvas.classList.add('grabbing');
    hint.classList.add('gone');
  });
  controls.addEventListener('end', () => canvas.classList.remove('grabbing'));

  // ---------- post-traitement : contour du lieu choisi, halo la nuit, antialiasing, tone mapping
  const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType });
  composer.addPass(new RenderPass(scene, camera));
  // rendu « diorama doux » : occlusion ambiante (pieds d'immeubles, rues étroites) teintée chaude
  const mobile = matchMedia('(max-width: 700px)').matches;
  const touch = matchMedia('(pointer: coarse)').matches;
  const normalPass = new NormalPass(scene, camera, { resolutionScale: 0.5 });
  composer.addPass(normalPass);
  const ssao = new SSAOEffect(camera, normalPass.texture, {
    blendFunction: BlendFunction.MULTIPLY,
    worldDistanceThreshold: 40, worldDistanceFalloff: 8, worldProximityThreshold: 0.35, worldProximityFalloff: 0.1,
    radius: 0.05, intensity: 1.6, bias: 0.035, fade: 0.04, luminanceInfluence: 0.55, samples: mobile ? 9 : 16, rings: 7,
    resolutionScale: 0.75, color: new THREE.Color(0x3b2e28),
  });
  const outline = new OutlineEffect(scene, camera, {
    blendFunction: BlendFunction.SCREEN,
    edgeStrength: 4,
    pulseSpeed: 0.6,
    visibleEdgeColor: 0xffffff,
    hiddenEdgeColor: 0x9fd0ff,
    blur: true,
    xRay: true,
  });
  const bloom = new BloomEffect({ luminanceThreshold: 0.85, luminanceSmoothing: 0.2, intensity: 0, mipmapBlur: true });
  const saturation = new HueSaturationEffect({ saturation: 0.12 });
  composer.addPass(
    new EffectPass(camera, ssao, outline, bloom, new SMAAEffect(), new ToneMappingEffect({ mode: ToneMappingMode.ACES_FILMIC }), saturation),
  );
  // léger flou de maquette en haut et en bas de l'image (selon la qualité, jamais en mouvement réduit)
  // (retirée plutôt que désactivée : seule la dernière passe du composer écrit à l'écran)
  const tiltPass = new EffectPass(camera, new TiltShiftEffect({ focusArea: 0.8, feather: 0.25, kernelSize: KernelSize.VERY_SMALL }));

  // ---------- qualité (auto par défaut ; ?q=high|mid|low force un niveau pour les tests)
  const forced = new URLSearchParams(location.search).get('q') as Level | null;
  let level: Level = forced && forced in PROFILES ? forced
    : settings.quality === 'auto' ? guessLevel(renderer.getContext()) : settings.quality;
  let profile = PROFILES[level];
  const applyQuality = (): void => {
    profile = PROFILES[level];
    // écran tactile (téléphone, tablette) : 1,5 suffit à l'œil sur un petit écran, et c'est 4× moins de pixels qu'à 3
    renderer.setPixelRatio(Math.min(devicePixelRatio, profile.dpr, touch ? 1.5 : 4));
    if (sun.shadow.mapSize.x !== profile.shadowSize) {
      sun.shadow.mapSize.set(profile.shadowSize, profile.shadowSize);
      sun.shadow.map?.dispose();
      sun.shadow.map = null; // recréée au prochain rendu
    }
    normalPass.enabled = profile.ssao;
    ssao.blendMode.blendFunction = profile.ssao ? BlendFunction.MULTIPLY : BlendFunction.SKIP;
    if (profile.ssao) ssao.samples = mobile ? Math.min(9, profile.ssaoSamples) : profile.ssaoSamples;
    const tilt = profile.tiltShift && !reducedMotion;
    if (tilt && !composer.passes.includes(tiltPass)) composer.addPass(tiltPass);
    if (!tilt && composer.passes.includes(tiltPass)) composer.removePass(tiltPass);
    passants.crowd = profile.crowd;
    renderer.shadowMap.needsUpdate = true;
    resize();
    hud.setQuality(settings.quality, level);
  };
  const fpsWatch = new FpsWatch(() => {
    if (settings.quality !== 'auto' || forced || level === 'low') return;
    level = level === 'high' ? 'mid' : 'low';
    console.info(`qualité abaissée : ${LEVEL_NAMES[level].fr}`);
    applyQuality();
  }, () => {
    // déjà en basse qualité et toujours saccadé : proposer la version simple, une fois
    if (level !== 'low' || document.querySelector('.slow-offer')) return;
    const o = Object.assign(document.createElement('div'), { className: 'slow-offer glass', role: 'status' });
    o.innerHTML = `<span>${t('Cet appareil peine à faire tourner la 3D.', 'This device struggles with the 3D view.')}</span><a href="${BASE}recruteur/${t('', '?lang=en')}">${t('Version simple', 'Simple version')}</a><button type="button" aria-label="${t('Fermer', 'Close')}">×</button>`;
    o.querySelector('button')!.addEventListener('click', () => o.remove());
    document.body.append(o);
  });
  const setQualityChoice = (q: QualityChoice): void => {
    settings.quality = q;
    saveSettings(settings);
    level = q === 'auto' ? guessLevel(renderer.getContext()) : q;
    fpsWatch.reset();
    applyQuality();
  };

  // ---------- moment de la journée (transition douce)
  let timeTarget: TimeOfDay = byId(TIMES, settings.time);
  const cur = {
    sunColor: new THREE.Color(timeTarget.sun.color), sunInt: timeTarget.sun.intensity,
    sunPos: new THREE.Vector3().fromArray(timeTarget.sun.position),
    sky: new THREE.Color(timeTarget.hemi.sky), ground: new THREE.Color(timeTarget.hemi.ground),
    hemiInt: timeTarget.hemi.intensity, env: timeTarget.env, night: timeTarget.night,
    fog: new THREE.Color(timeTarget.sky[1]),
  };
  scene.fog = new THREE.Fog(cur.fog, 40, 130); // seulement l'horizon lointain
  const tmpC = new THREE.Color();
  const tmpV = new THREE.Vector3();
  const applyTime = (k: number): void => {
    const t = timeTarget;
    cur.sunColor.lerp(tmpC.set(t.sun.color), k);
    cur.sky.lerp(tmpC.set(t.hemi.sky), k);
    cur.ground.lerp(tmpC.set(t.hemi.ground), k);
    cur.sunPos.lerp(tmpV.fromArray(t.sun.position), k);
    cur.sunInt += (t.sun.intensity - cur.sunInt) * k;
    cur.hemiInt += (t.hemi.intensity - cur.hemiInt) * k;
    cur.env += (t.env - cur.env) * k;
    cur.night += (t.night - cur.night) * k;
    cur.fog.lerp(tmpC.set(t.sky[1]), k);
    (scene.fog as THREE.Fog).color.copy(cur.fog);
    sun.color.copy(cur.sunColor);
    sun.intensity = cur.sunInt;
    // le soleil suit le point regardé : ombres nettes là où l'on regarde, quelle que soit la distance
    sun.position.copy(controls.target).addScaledVector(tmpV.copy(cur.sunPos).normalize(), 60);
    sun.target.position.copy(controls.target);
    hemi.color.copy(cur.sky);
    hemi.groundColor.copy(cur.ground);
    hemi.intensity = cur.hemiInt;
    scene.environmentIntensity = cur.env;
    island.setNight(cur.night);
    // reflet du ciel sur la mer : discret le jour, plus marqué au coucher, assombrie la nuit
    island.tintSea(cur.fog, cur.night < 0.5 ? 0.25 * cur.night : 0.1 + 0.4 * (cur.night - 0.5)); // coucher 10 %, nuit 30 %
    aerien.setNight(cur.night);
    panneau.setNight(cur.night);
    bloom.intensity = 2.1 * cur.night * Math.min(1.5, island.lights);
  };
  applyTime(1);
  const fitShadow = (): void => {
    const d = camera.position.distanceTo(controls.target);
    const ext = THREE.MathUtils.clamp(d * 0.55, 6, 70);
    const cam = sun.shadow.camera;
    if (Math.abs(cam.right - ext) > 0.5) {
      Object.assign(cam, { left: -ext, right: ext, top: ext, bottom: -ext });
      cam.updateProjectionMatrix();
    }
  };

  // bouton « Copier l'adresse » (rubrique Contact) : presse-papiers + petit message
  document.querySelector('#panel-body')!.addEventListener('click', (e) => {
    const b = (e.target as HTMLElement).closest<HTMLElement>('[data-copy]');
    if (!b) return;
    navigator.clipboard?.writeText(b.dataset.copy!).then(
      () => toast(t('Adresse copiée', 'Address copied')),
      () => toast(b.dataset.copy!),
    );
  });

  // bulle BD au-dessus de la figurine quand on clique dessus (une phrase différente à chaque fois)
  const PHRASES = [
    { fr: 'Bienvenue sur trystanbouzonrueda.com !', en: 'Welcome to trystanbouzonrueda.com!' },
    { fr: 'Je cherche un stage de 12 semaines à l’étranger.', en: 'I’m looking for a 12-week internship abroad.' },
    { fr: 'Systèmes, réseaux, IA : c’est mon terrain de jeu.', en: 'Systems, networks, AI: that’s my playground.' },
    { fr: 'Tout ce que tu vois tourne sur un serveur chez moi.', en: 'Everything you see runs on a server at my place.' },
  ];
  const dit = Object.assign(document.createElement('div'), { className: 'dit', role: 'status' });
  dit.hidden = true;
  document.body.append(dit);
  let ditUntil = 0, ditN = 0;
  const dire = (): void => {
    dit.textContent = tx(PHRASES[ditN++ % PHRASES.length]);
    dit.hidden = false;
    ditUntil = performance.now() + 3800;
  };
  const ditAt = new THREE.Vector3();
  const updateDit = (): void => {
    if (dit.hidden) return;
    if (performance.now() > ditUntil) { dit.hidden = true; return; }
    trystan.group.getWorldPosition(ditAt).add(new THREE.Vector3(0, 0.3, 0)).project(camera);
    dit.style.transform = `translate(${((ditAt.x + 1) / 2) * innerWidth}px, ${((1 - ditAt.y) / 2) * innerHeight}px) translate(-50%, -100%)`;
  };

  // ---------- vols de caméra
  interface Flight { fromPos: THREE.Vector3; fromTarget: THREE.Vector3; toPos: THREE.Vector3; toTarget: THREE.Vector3; t: number; dur: number }
  let flight: Flight | null = null;
  const flyTo = (toPos: THREE.Vector3, toTarget: THREE.Vector3, dur = 1.6): void => {
    controls.autoRotate = false;
    // vols plus posés (demande de Trystan) : +35 %, et un peu plus long quand le trajet est grand
    const far = THREE.MathUtils.clamp(camera.position.distanceTo(toPos) * 0.03, 0, 0.9);
    flight = { fromPos: camera.position.clone(), fromTarget: controls.target.clone(), toPos, toTarget, t: 0, dur: reducedMotion ? 0.01 : dur * 1.35 + far };
  };
  const viewOf = (box: THREE.Box3): { pos: THREE.Vector3; target: THREE.Vector3 } => {
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3()).length();
    const dist = THREE.MathUtils.clamp(size * (innerWidth > 900 ? 2.75 : 2.4), 3.5, 15); // grand écran : un peu plus de recul, le monument tient dans l'espace libre
    // on garde l'angle actuel autour de l'île, vu d'un peu au-dessus
    const dir = camera.position.clone().sub(controls.target).setY(0).normalize();
    const pos = center.clone().addScaledVector(dir, dist * 0.8).setY(center.y + dist * 0.6);
    // le panneau ne bouge pas la caméra : c'est le décalage de projection (frame) qui recentre le monument dans l'espace libre
    return { pos, target: center.clone() };
  };

  // ---------- sélection d'un lieu
  const hud = mountHud(settings, {
    time: (id) => {
      settings.time = id;
      timeTarget = byId(TIMES, id);
      saveSettings(settings);
    },
    theme: (theme) => {
      settings.theme = theme;
      applyTheme(theme);
      saveSettings(settings);
    },
    place: (id) => select(id),
    quality: (q) => setQualityChoice(q),
    lights: (v) => {
      settings.lights = v;
      island.setLights(v);
      saveSettings(settings);
    },
    overview: () => {
      select(null);
      flyTo(HOME.pos.clone(), HOME.target.clone(), 1.8);
    },
  });

  const fillPanel = (place: (typeof PLACES)[number]): void => {
    const section = sectionById(place.section);
    if (!section) return;
    document.querySelector('#panel-kicker')!.textContent = `${section.kicker} · ${place.name}`;
    document.querySelector('#panel-title')!.textContent = section.title;
    document.querySelector('#panel-body')!.innerHTML = section.html;
  };
  // bascule de langue : panneau ouvert rempli à nouveau, listes du menu reconstruites à la prochaine ouverture, bulle fermée
  onLang(() => {
    const place = PLACES.find((p) => p.id === island.selected);
    if (place && !panel.hidden) fillPanel(place);
    tag.hidden = true;
    navLieux.replaceChildren();
    if (!nav.hidden && !navLieux.hidden) fillLieux();
    if (!nav.hidden && !navMetro.hidden) fillLigne();
  });
  // contour lumineux : bâtiment sélectionné + bâtiment survolé
  const refreshOutline = (): void => {
    const ids = [island.selected, island.hovered].filter((v, i, a): v is string => !!v && a.indexOf(v) === i);
    outline.selection.set(ids.flatMap((i) => island.meshesOf(i)));
  };
  const select = (id: string | null): void => {
    arrAt = null;
    stationAt = null;
    if (id && !island.places.has(id)) id = null; // lieu pas encore modélisé
    island.selected = id;
    refreshOutline();
    hud.setCurrent(id);
    tag.hidden = true;
    panel.hidden = true;
    if (!id) return;
    const place = byId(PLACES, id);
    const box = island.box(id);
    if (box) {
      const v = viewOf(box);
      flyTo(v.pos, v.target);
    }
    son.play('clic');
    if (place.section) {
      event(`rubrique-${place.section}`);
      // le panneau s'ouvre pendant le vol
      setTimeout(() => {
        if (island.selected !== id) return;
        fillPanel(place);
        panel.hidden = false;
        openNav(null);
        document.querySelector<HTMLElement>('#panel-title')!.focus({ preventScroll: true });
      }, reducedMotion ? 0 : 650);
    } else {
      tag.innerHTML = '';
      const h = document.createElement('strong');
      h.textContent = place.name;
      const s = document.createElement('span');
      s.textContent = tx(place.blurb);
      tag.append(h, s);
      tag.hidden = false;
    }
  };
  document.querySelector('#panel-close')!.addEventListener('click', () => select(null));

  // ---------- carte (téléportation) et métro (aller à une station)
  const nav = document.querySelector<HTMLElement>('#nav')!;
  const navMap = document.querySelector<HTMLElement>('#nav-map')!;
  const navImg = navMap.querySelector('img')!;
  const navDot = document.querySelector<HTMLElement>('#nav-dot')!;
  const navMetro = document.querySelector<HTMLElement>('#nav-metro')!;
  const navLieux = document.querySelector<HTMLElement>('#nav-lieux')!;
  const tabs = [...nav.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
  let mapB: { x0: number; x1: number; z0: number; z1: number } | null = null;
  fetch(`${BASE}data/minimap.json`).then((r) => r.json()).then((b) => (mapB = b)).catch(() => {});
  type Tab = 'carte' | 'metro' | 'lieux';
  const TABS: Tab[] = ['carte', 'metro', 'lieux'];
  const openNav = (tab: Tab | null): void => {
    nav.hidden = !tab;
    for (const id of TABS) {
      document.querySelector(`#${id}-btn`)!.setAttribute('aria-pressed', String(tab === id));
    }
    if (!tab) return;
    panel.hidden = true;
    tabs.forEach((t) => t.setAttribute('aria-selected', String(t.dataset.tab === tab)));
    navMap.parentElement!.hidden = tab !== 'carte';
    navMetro.hidden = tab !== 'metro';
    navLieux.hidden = tab !== 'lieux';
    if (tab === 'lieux' && !navLieux.childElementCount) fillLieux();
    if (tab === 'metro' && !navMetro.querySelector('h3')) fillMetro();
    if (tab === 'metro') fillLigne();
  };
  tabs.forEach((t) => t.addEventListener('click', () => openNav(t.dataset.tab as Tab)));
  for (const id of TABS) {
    // le bouton ouvre son onglet, ou ferme le panneau s'il est déjà ouvert dessus
    const btn = document.querySelector(`#${id}-btn`)!;
    btn.addEventListener('click', () => openNav(btn.getAttribute('aria-pressed') === 'true' ? null : id));
  }
  document.querySelector('#nav-close')!.addEventListener('click', () => openNav(null));

  // vue rapprochée sur un point : assez près pour voir les rues, assez loin pour garder le décor
  const groundRay = new THREE.Raycaster();
  const groundAt = (x: number, z: number): number => {
    groundRay.set(new THREE.Vector3(x, 60, z), new THREE.Vector3(0, -1, 0));
    const hit = groundRay.intersectObject(island.group, true).find((h) => (h.object as THREE.Mesh).isMesh);
    return hit ? hit.point.y - world.position.y : 0.3;
  };
  // on regarde toujours vers la mer, Notre-Dame et le Vélodrome : le décor reste dans le champ
  const SEA = new THREE.Vector3(-3, 0, 7);
  const goTo = (spot: THREE.Vector3, dist: number): void => {
    const dir = new THREE.Vector3(spot.x - SEA.x, 0, spot.z - SEA.z);
    if (dir.length() < 3) dir.set(1, 0, -1); // déjà au bord de l'eau : vue vers le sud-ouest
    dir.normalize();
    const target = spot.clone().add(world.position).addScaledVector(dir, -dist * 0.3);
    const pos = spot.clone().add(world.position).addScaledVector(dir, dist * 0.75).setY(spot.y + world.position.y + dist * 0.42);
    if (innerWidth > 700 && !nav.hidden) {
      // le panneau est à droite : on décale la vue vers la gauche
      const right = new THREE.Vector3().crossVectors(dir, new THREE.Vector3(0, 1, 0)).normalize();
      target.addScaledVector(right, -dist * 0.28);
      pos.addScaledVector(right, -dist * 0.28);
    }
    flyTo(pos, target, 2.2);
    hint.classList.add('gone');
  };
  navMap.addEventListener('click', (e) => {
    if (!mapB) return;
    const r = navImg.getBoundingClientRect();
    const u = (e.clientX - r.left) / r.width, v = (e.clientY - r.top) / r.height;
    if (u < 0 || u > 1 || v < 0 || v > 1) return;
    const x = mapB.x0 + u * (mapB.x1 - mapB.x0), z = mapB.z0 + v * (mapB.z1 - mapB.z0);
    select(null);
    goTo(new THREE.Vector3(x, groundAt(x, z), z), 7);
    if (innerWidth <= 700) openNav(null);
  });
  const showStation = (name: string, line: string, color: string): void => {
    select(null);
    tag.innerHTML = '';
    const h = document.createElement('strong');
    h.textContent = name;
    const sp = document.createElement('span');
    sp.textContent = `${t('Métro', 'Metro')} ${line}`;
    sp.style.color = color;
    tag.append(h, sp);
    tag.hidden = false;
    stationAt = name;
  };
  const fillMetro = (): void => {
    for (const l of metro.list()) {
      const h = document.createElement('h3');
      const b = document.createElement('b');
      b.textContent = l.ref;
      b.style.background = l.color;
      h.append(b, ` ${l.stops[0]?.name ?? ''} ↔ ${l.stops.at(-1)?.name ?? ''}`);
      const ul = document.createElement('ul');
      ul.style.setProperty('--metro', l.color);
      for (const st of l.stops) {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = st.name;
        btn.addEventListener('click', () => {
          goTo(st.p.clone().setY(st.p.y - 0.09), 7);
          showStation(st.name, l.ref, l.color);
          if (innerWidth <= 700) openNav(null);
        });
        li.append(btn);
        ul.append(li);
      }
      navMetro.append(h, ul);
    }
    if (!navMetro.childElementCount) navMetro.textContent = t('Le métro charge encore…', 'The metro is still loading…');
  };
  const fillLieux = (): void => {
    const ul = document.createElement('ul');
    for (const p of PLACES) {
      if (!island.places.has(p.id)) continue;
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      const strong = document.createElement('strong');
      strong.textContent = p.name;
      const small = document.createElement('span');
      small.textContent = sectionById(p.section)?.kicker ?? tx(p.blurb);
      btn.append(strong, small);
      btn.addEventListener('click', () => { openNav(null); select(p.id); });
      li.append(btn);
      ul.append(li);
    }
    navLieux.append(ul);
  };
  const updateNavDot = (): void => {
    if (nav.hidden || !mapB || navMap.parentElement!.hidden) return;
    const u = (controls.target.x - mapB.x0) / (mapB.x1 - mapB.x0);
    const v = (controls.target.z - mapB.z0) / (mapB.z1 - mapB.z0);
    navDot.style.left = `${navImg.offsetLeft + u * navImg.clientWidth}px`;
    navDot.style.top = `${navImg.offsetTop + v * navImg.clientHeight}px`;
  };
  // ---------- balade au clavier (ZQSD / flèches : avancer et se décaler, A/E : tourner, R/F : zoomer, Maj : plus vite)
  const keys = new Set<string>();
  const KEYMAP: Record<string, string> = {
    KeyW: 'av', ArrowUp: 'av', KeyS: 'ar', ArrowDown: 'ar', KeyA: 'g', ArrowLeft: 'g', KeyD: 'd', ArrowRight: 'd',
    KeyQ: 'tg', KeyE: 'td', KeyR: 'zi', KeyF: 'zo',
  };
  const typing = (t: EventTarget | null): boolean => t instanceof HTMLInputElement || t instanceof HTMLTextAreaElement;
  addEventListener('keydown', (e) => {
    // e.code = position physique : ZQSD sur AZERTY = WASD sur QWERTY
    const k = KEYMAP[e.code];
    if (!k || typing(e.target) || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.code.startsWith('Arrow')) e.preventDefault();
    keys.add(k);
    if (e.shiftKey) keys.add('vite');
    controls.autoRotate = false;
    flight = null;
    hint.classList.add('gone');
  });
  addEventListener('keyup', (e) => {
    const k = KEYMAP[e.code];
    if (k) keys.delete(k);
    if (e.key === 'Shift') keys.delete('vite');
  });
  addEventListener('blur', () => keys.clear());
  const kf = new THREE.Vector3(), kr = new THREE.Vector3(), kmove = new THREE.Vector3(), kup = new THREE.Vector3(0, 1, 0);
  // joysticks tactiles : mêmes mouvements que le clavier, en analogique
  // créés au chargement sur écran tactile, ou au premier toucher (écran hybride, mode appareil du navigateur)
  let pad: Pad | null = null;
  const makePad = (): void => {
    pad ??= new Pad(document.body, () => {
      controls.autoRotate = false;
      flight = null;
      hint.classList.add('gone');
    });
  };
  if (touch) makePad();
  else {
    addEventListener('touchstart', makePad, { once: true, passive: true });
    matchMedia('(pointer: coarse)').addEventListener('change', (e) => e.matches && makePad());
  }
  const keyboardMove = (dt: number): void => {
    if (!keys.size && !pad?.active) return;
    const dist = camera.position.distanceTo(controls.target);
    const speed = Math.max(0.9, dist * 0.35) * (keys.has('vite') ? 2.6 : 1) * dt;
    kf.subVectors(controls.target, camera.position).setY(0).normalize();
    kr.crossVectors(kf, kup).normalize();
    const fwd = (keys.has('av') ? 1 : 0) - (keys.has('ar') ? 1 : 0) + (pad?.move.y ?? 0);
    const side = (keys.has('d') ? 1 : 0) - (keys.has('g') ? 1 : 0) + (pad?.move.x ?? 0);
    kmove.set(0, 0, 0).addScaledVector(kf, fwd).addScaledVector(kr, side);
    if (kmove.lengthSq() > 0) {
      if (kmove.lengthSq() > 1) kmove.normalize();
      kmove.multiplyScalar(speed);
      // reste au-dessus de l'île (jusqu'au CESI d'Aix au nord)
      const nx = THREE.MathUtils.clamp(controls.target.x + kmove.x, -18, 18);
      const nz = THREE.MathUtils.clamp(controls.target.z + kmove.z, -62, 26);
      kmove.set(nx - controls.target.x, 0, nz - controls.target.z);
      controls.target.add(kmove);
      camera.position.add(kmove);
    }
    const turn = (keys.has('td') ? 1 : 0) - (keys.has('tg') ? 1 : 0) + (pad?.look.x ?? 0);
    if (turn) camera.position.sub(controls.target).applyAxisAngle(kup, -turn * 1.4 * dt).add(controls.target);
    const zoom = (keys.has('zo') ? 1 : 0) - (keys.has('zi') ? 1 : 0) - (pad?.look.y ?? 0);
    if (zoom) {
      const d = THREE.MathUtils.clamp(dist * (1 + zoom * 0.8 * dt), controls.minDistance, controls.maxDistance);
      camera.position.sub(controls.target).setLength(d).add(controls.target);
    }
  };

  addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    if (ligne.riding) ligne.skip();
    else select(null);
  });

  // ---------- métro des monuments (ligne imaginaire, voir ligne.ts)
  const buildLigne = (): void => {
    const hub = metro.list().flatMap((l) => l.stops).find((st) => /vieux.?port/i.test(st.name))?.p;
    for (const p of PLACES) {
      if (!p.section || !island.places.has(p.id)) continue;
      let q: THREE.Vector3;
      if (p.id === 'vieux_port' && hub) {
        q = hub.clone(); // départ : la vraie station Vieux-Port
      } else {
        // quai à côté du monument, du côté du Vieux-Port, posé sur ce qu'il y a dessous (sol ou toit)
        const box = island.box(p.id)!;
        const c = box.getCenter(new THREE.Vector3()).sub(world.position);
        const size = box.getSize(new THREE.Vector3());
        const dir = new THREE.Vector3((hub?.x ?? 0) - c.x, 0, (hub?.z ?? 0) - c.z).normalize();
        q = c.addScaledVector(dir, Math.hypot(size.x, size.z) * 0.5 + 0.3);
        q.y = groundAt(q.x, q.z) + 0.02;
      }
      ligne.stops.push({ id: p.id, name: p.name, kicker: p.section, p: q });
    }
    ligne.park();
  };
  const ligneBox = document.createElement('div');
  ligneBox.className = 'ligne';
  const fillLigne = (): void => {
    if (!ligne.stops.length) return;
    ligneBox.innerHTML = '';
    const h = document.createElement('h3');
    const b = document.createElement('b');
    b.textContent = '★';
    h.append(b, ` ${t('Métro des monuments', 'Landmark metro')}`);
    const help = document.createElement('p');
    help.className = 'ligne-help';
    help.textContent = t(`Ligne imaginaire, départ de ${ligne.stop(ligne.current)?.name ?? 'ici'} : choisis où descendre.`, `Imaginary line from ${ligne.stop(ligne.current)?.name ?? 'here'}: pick where to get off.`);
    const ul = document.createElement('ul');
    for (const st of ligne.stops) {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.disabled = st.id === ligne.current;
      btn.innerHTML = '';
      const strong = document.createElement('strong');
      strong.textContent = st.name;
      const small = document.createElement('span');
      small.textContent = st.id === ligne.current ? t('vous êtes ici', 'you are here') : sectionById(st.kicker)?.kicker ?? '';
      btn.append(strong, small);
      btn.addEventListener('click', () => startRide(st.id));
      li.append(btn);
      ul.append(li);
    }
    ligneBox.append(h, help, ul);
    navMetro.prepend(ligneBox);
  };
  // plafond du trajet aérien : bâtiments et monuments par leurs boîtes (rapide, prudent), relief par quelques rayons
  let obstacles: THREE.Box3[] | null = null;
  const terrain: THREE.Object3D[] = [];
  const buildObstacles = (): THREE.Box3[] => {
    const list: THREE.Box3[] = [];
    island.group.updateMatrixWorld(true);
    island.group.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      let kind = 'bati';
      for (let q: THREE.Object3D | null = m; q && q !== island.group; q = q.parent) {
        if (/^(ile_sol|ile_falaise|plateau|iles$)/.test(q.name)) kind = 'sol';
        else if (/^(voirie|metro|stations|tram|arbres)/.test(q.name)) kind = 'non';
      }
      if (kind === 'sol') terrain.push(m);
      else if (kind === 'bati') list.push(new THREE.Box3().setFromObject(m).translate(world.position.clone().negate()));
    });
    return list;
  };
  const ceilRay = new THREE.Raycaster();
  const ceilingAlong = (a: THREE.Vector3, b: THREE.Vector3): number => {
    obstacles ??= buildObstacles();
    let top = Math.max(a.y, b.y);
    const m = 0.2; // demi-largeur du couloir de la rame
    const minX = Math.min(a.x, b.x) - m, maxX = Math.max(a.x, b.x) + m, minZ = Math.min(a.z, b.z) - m, maxZ = Math.max(a.z, b.z) + m;
    const dx = b.x - a.x, dz = b.z - a.z, L = Math.hypot(dx, dz) || 1;
    for (const box of obstacles) {
      if (box.max.y <= top || box.max.x < minX || box.min.x > maxX || box.max.z < minZ || box.min.z > maxZ) continue;
      // distance du segment au rectangle (approximée par son centre et sa demi-diagonale)
      const cx = (box.min.x + box.max.x) / 2, cz = (box.min.z + box.max.z) / 2;
      const t = THREE.MathUtils.clamp(((cx - a.x) * dx + (cz - a.z) * dz) / (L * L), 0, 1);
      const d = Math.hypot(a.x + dx * t - cx, a.z + dz * t - cz);
      if (d < Math.hypot(box.max.x - box.min.x, box.max.z - box.min.z) / 2 + m) top = box.max.y;
    }
    const n = Math.min(40, Math.max(6, Math.ceil(L / 0.6)));
    for (let i = 1; i < n; i++) {
      const k = i / n;
      ceilRay.set(new THREE.Vector3(a.x + dx * k + world.position.x, 80, a.z + dz * k + world.position.z), new THREE.Vector3(0, -1, 0));
      const hit = ceilRay.intersectObjects(terrain, false)[0];
      if (hit) top = Math.max(top, hit.point.y - world.position.y);
    }
    return top;
  };
  const startRide = (id: string): void => {
    select(null);
    openNav(null);
    flight = null;
    controls.autoRotate = false;
    if (!ligne.go(id, ceilingAlong)) return;
    controls.enabled = false;
    document.body.classList.add('riding');
    hint.classList.add('gone');
  };
  // bulle dorée au quai courant : « prendre le métro »
  const metroBulle = document.createElement('button');
  metroBulle.type = 'button';
  metroBulle.className = 'bulle glass metro-bulle';
  const labelMetroBulle = (): void => {
    metroBulle.setAttribute('aria-label', t('Prendre le métro des monuments', 'Ride the landmark metro'));
    metroBulle.title = t('Métro des monuments', 'Landmark metro');
    metroBulle.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 17V7l5.5 7 5.5-7v10"/></svg><span>${t('Métro', 'Metro')}</span>`;
  };
  labelMetroBulle();
  onLang(labelMetroBulle);
  metroBulle.addEventListener('pointerdown', (e) => { e.stopPropagation(); e.preventDefault(); openNav('metro'); });
  metroBulle.addEventListener('keydown', (e) => (e.key === 'Enter' || e.key === ' ') && openNav('metro'));
  document.querySelector('#bulles')!.append(metroBulle);
  const bulleAt = new THREE.Vector3();
  const updateMetroBulle = (): void => {
    const st = ligne.stop(ligne.current);
    const show = !!st && !ligne.riding && !intro;
    if (show) {
      bulleAt.copy(st!.p).setY(st!.p.y + 0.32).add(world.position).project(camera);
      const visible = bulleAt.z < 1 && Math.abs(bulleAt.x) < 1.1 && Math.abs(bulleAt.y) < 1.1;
      metroBulle.hidden = !visible;
      if (visible) metroBulle.style.transform = `translate(-50%, -100%) translate(${((bulleAt.x + 1) / 2) * innerWidth}px, ${((1 - bulleAt.y) / 2) * innerHeight}px)`;
    } else metroBulle.hidden = true;
  };

  // clic (sans glisser) sur un lieu
  const raycaster = new THREE.Raycaster();
  let stationAt: string | null = null;
  let arrAt: THREE.Vector3 | null = null;
  const ndc = new THREE.Vector2();
  let downAt = { x: 0, y: 0 };
  const toNdc = (e: PointerEvent): void => {
    ndc.set((e.clientX / innerWidth) * 2 - 1, -(e.clientY / innerHeight) * 2 + 1);
  };
  canvas.addEventListener('pointerdown', (e) => (downAt = { x: e.clientX, y: e.clientY }));
  canvas.addEventListener('pointerup', (e) => {
    if (intro) return; // pendant l'arrivée, un clic sert seulement à accélérer
    if (ligne.riding) { ligne.skip(); return; } // pendant le trajet, un clic accélère l'arrivée
    if (Math.hypot(e.clientX - downAt.x, e.clientY - downAt.y) > 6) return; // c'était un glisser
    toNdc(e);
    raycaster.setFromCamera(ndc, camera);
    const url = reseaux.pick(raycaster);
    if (url) { window.open(url, '_blank', 'noopener'); return; }
    const tr = tresors.pick(raycaster);
    if (tr) {
      const last = tresors.take(tr);
      const name = TRESORS.find((x) => x.id === tr)!.name;
      son.play(last ? 'tresorFin' : 'tresor');
      toast(last
        ? t('🏆 Les 5 trésors sont à toi ! Tape « trophees » dans le terminal (touche ²).', '🏆 All 5 treasures found! Type “trophies” in the terminal (` key).')
        : t(`Trésor trouvé : ${name.fr} (${tresors.count}/${TRESORS.length})`, `Treasure found: ${name.en} (${tresors.count}/${TRESORS.length})`), last ? 6000 : 3200);
      if (last) fireworks();
      return;
    }
    if (aerien.hit(raycaster)) {
      aerien.larguer();
      son.play('largage');
      if (clicks('canadair')) toast(t('🚒 Largage d’urgence !', '🚒 Emergency water drop!'));
      return;
    }
    if (trystan.hit(raycaster)) {
      trystan.coucou();
      dire();
      select('notre_dame');
      return;
    }
    const st = metro.pick(raycaster);
    if (st) {
      showStation(st.station, st.line, st.color); // bulle de station : nom + ligne
      return;
    }
    stationAt = null;
    arrAt = null;
    const hit = island.pickHit(raycaster);
    const id = hit?.id ?? null;
    if (id && island.places.has(id) && PLACES.some((p) => p.id === id)) {
      if (id === 'notre_dame' && clicks(id)) { son.play('cloches'); toast(t('🔔 La Bonne Mère sonne pour toi.', '🔔 The Good Mother rings for you.')); }
      else if (id === 'velodrome' && clicks(id)) { son.play('clameur'); toast(t('⚽ Allez l’OM !', '⚽ Allez l’OM!')); }
      else if (island.selected === id) return; // déjà ouvert : pas de nouveau vol à chaque clic
      select(id);
      return;
    }
    // élément du décor : retour à la vue d'ouverture seulement si un monument était sélectionné ;
    // sinon on reste où l'on est (balade au clavier ou à la souris), on ferme juste bulle et panneaux
    const hadPlace = island.selected !== null;
    select(null);
    openNav(null);
    if (hadPlace) flyTo(HOME.pos.clone(), HOME.target.clone(), 1.8);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (e.buttons || e.pointerType !== 'mouse') return;
    toNdc(e);
    raycaster.setFromCamera(ndc, camera);
    const id = island.pick(raycaster);
    const place = id && island.places.has(id) && PLACES.some((p) => p.id === id) ? id : null;
    canvas.style.cursor = reseaux.pick(raycaster) || place ? 'pointer' : '';
    setHover(place);
  });
  // survol : le bâtiment se soulève comme à la sélection, sans ouvrir la rubrique.
  // Petit délai avant de le reposer : en montant, il peut glisser hors du curseur (sinon il clignoterait).
  let hoverOff = 0;
  const setHover = (id: string | null): void => {
    if (id) {
      clearTimeout(hoverOff);
      hoverOff = 0;
      if (island.hovered !== id) {
        island.hovered = id;
        refreshOutline();
        if (id !== island.selected) son.play('survol');
      }
    } else if (island.hovered && !hoverOff) {
      hoverOff = window.setTimeout(() => {
        island.hovered = null;
        refreshOutline();
        hoverOff = 0;
      }, 350);
    }
  };
  canvas.addEventListener('pointerleave', () => setHover(null));

  // ---------- taille
  const resize = (): void => {
    renderer.setSize(innerWidth, innerHeight, false);
    composer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.fov = camera.aspect < 0.8 ? 50 : 35; // portrait : champ plus large
    camera.updateProjectionMatrix();
  };
  addEventListener('resize', resize);
  applyQuality();

  // ---------- mesures (…/?debug) : lues par scripts/perf.py
  const debug = new URLSearchParams(location.search).has('debug')
    ? { frames: 0, calls: 0, triangles: 0, cpu: 0, renderer, scene, camera, controls, THREE, island: island.group, groundAt: (x: number, z: number) => groundAt(x, z), setView: (p: number[], t: number[]) => { flight = null; controls.autoRotate = false; camera.position.fromArray(p); controls.target.fromArray(t); } }
    : null;
  if (debug) {
    renderer.info.autoReset = false; // cumul de toutes les passes de la frame
    (window as unknown as { __perf: typeof debug }).__perf = debug;
  }

  // ---------- boucle
  const timer = new THREE.Timer();
  let elapsed = 0;
  const ease = (x: number): number => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const anchor = new THREE.Vector3();
  const lastCam = new THREE.Vector3();
  const lastTarget = new THREE.Vector3();
  const camNoBob = new THREE.Vector3();
  const targetNoBob = new THREE.Vector3();
  let frameNo = 0;
  let bob = 0;
  let detailsAsked = false;
  let loadDetails = (): void => {};
  const viewShift = { x: 0, y: 0 };
  const frame = (): void => {
    const t0 = debug ? performance.now() : 0;
    if (debug) renderer.info.reset();
    timer.update();
    const rawDt = timer.getDelta();
    fpsWatch.tick(rawDt);
    const dt = Math.min(rawDt, 0.05);
    elapsed += dt * motion;
    // l'île « flotte » : on déplace la caméra (et les nuages) à l'inverse plutôt que la ville entière,
    // même image, mais plus de recalcul des matrices de milliers d'objets à chaque frame
    const bobNow = Math.sin(elapsed * 0.6) * 0.06;
    const bobD = bobNow - bob;
    bob = bobNow;
    camera.position.y -= bobD;
    controls.target.y -= bobD;
    clouds.position.y -= bobD;
    clouds.rotation.y += dt * 0.02 * motion;
    applyTime(1 - Math.exp(-dt * 2.5));
    island.update(dt, elapsed, motion);
    metro.update(dt * motion);
    vie.update(dt * motion, elapsed);
    trafic.update(dt * motion);
    trystan.update(dt * motion);
    reseaux.update(elapsed, camera);
    updateDit();
    ciel.update(elapsed);
    aerien.update(dt * motion, elapsed);
    feux.update(dt);
    tresors.update(dt, elapsed);
    son.update(dt, { height: camera.position.y, dist: camera.position.distanceTo(controls.target), night: cur.night, riding: ligne.riding });
    passants.update(dt * motion, elapsed, camera.position.distanceTo(controls.target));
    updateNavDot();
    bulles.update(camera, island, world.position, island.selected);
    updateMetroBulle();
    const riding = ligne.riding;
    const arrived = ligne.update(dt * (riding ? 1 : motion), camera, controls.target, world.position);
    island.updateDetails(camera.position, profile.detailRange);
    if (!detailsAsked && (level !== 'low' || camera.position.distanceTo(controls.target) < profile.detailRange)) loadDetails();
    fitShadow();

    if (intro) {
      // arrivée du ciel : la caméra est pilotée par l'intro, les contrôles attendent
      if (intro.update(dt, camera)) endIntro();
      else {
        // de très haut, le brouillard recule avec la caméra : la ville reste nette, les bords de l'île se fondent dans l'horizon
        const fog = scene.fog as THREE.Fog;
        const d = camera.position.distanceTo(HOME.target);
        fog.near = Math.max(40, d * 0.95);
        fog.far = Math.max(130, d * 1.22);
        (scene.background as THREE.Color).copy(fog.color); // au-delà du bord : même teinte que le brouillard
      }
    } else if (riding) {
      if (arrived) {
        // à quai : on descend, la rubrique du lieu s'ouvre
        controls.enabled = true;
        document.body.classList.remove('riding');
        select(arrived);
      }
    } else if (flight) {
      flight.t = Math.min(1, flight.t + dt / flight.dur);
      const k = ease(flight.t);
      controls.target.lerpVectors(flight.fromTarget, flight.toTarget, k);
      // arc : la caméra monte un peu au milieu du vol
      camera.position.lerpVectors(flight.fromPos, flight.toPos, k);
      camera.position.y += Math.sin(Math.PI * k) * flight.fromPos.distanceTo(flight.toPos) * 0.15;
      if (flight.t >= 1) flight = null;
    }
    if (!intro && !riding) {
      keyboardMove(dt);
      controls.update(dt);
    }
    // rubrique ouverte : centre de projection décalé au milieu de l'espace libre (à gauche du panneau, ou au-dessus en portrait)
    let sx = 0, sy = 0;
    if (!panel.hidden) {
      const r = panel.getBoundingClientRect();
      if (r.left > innerWidth * 0.25) sx = innerWidth / 2 - r.left / 2;
      else if (r.top > innerHeight * 0.25) sy = innerHeight / 2 - r.top / 2;
    }
    const ks = 1 - Math.exp(-dt * 5);
    viewShift.x += (sx - viewShift.x) * ks;
    viewShift.y += (sy - viewShift.y) * ks;
    if (Math.abs(viewShift.x) + Math.abs(viewShift.y) > 0.5) camera.setViewOffset(innerWidth, innerHeight, viewShift.x, viewShift.y, innerWidth, innerHeight);
    else if (camera.view?.enabled) camera.clearViewOffset();
    // ombres : à chaque frame quand la vue bouge, sinon toutes les N frames (voitures, métro, passants)
    frameNo++;
    // positions sans le flottement : il ne doit pas compter comme un mouvement (sinon ombre recalculée à chaque frame)
    camNoBob.copy(camera.position).setY(camera.position.y + bob);
    targetNoBob.copy(controls.target).setY(controls.target.y + bob);
    const moved = lastCam.distanceToSquared(camNoBob) > 1e-8 || lastTarget.distanceToSquared(targetNoBob) > 1e-8;
    if (moved || frameNo % profile.shadowEvery === 0) renderer.shadowMap.needsUpdate = true;
    lastCam.copy(camNoBob);
    lastTarget.copy(targetNoBob);

    if (!tag.hidden && arrAt) {
      anchor.copy(arrAt).setY(arrAt.y + 0.3).add(world.position).project(camera);
      tag.style.transform = `translate(-50%, -100%) translate(${((anchor.x + 1) / 2) * innerWidth}px, ${((1 - anchor.y) / 2) * innerHeight}px)`;
    } else if (!tag.hidden && stationAt) {
      const m = metro.markerOf(stationAt);
      if (m) {
        anchor.copy(m).setY(m.y + 0.5).add(world.position).project(camera);
        tag.style.transform = `translate(-50%, -100%) translate(${((anchor.x + 1) / 2) * innerWidth}px, ${((1 - anchor.y) / 2) * innerHeight}px)`;
      }
    } else if (!tag.hidden && island.selected) {
      const box = island.box(island.selected);
      if (box) {
        box.getCenter(anchor);
        anchor.y = box.max.y + 0.5;
        anchor.add(world.position).project(camera);
        tag.style.transform = `translate(-50%, -100%) translate(${((anchor.x + 1) / 2) * innerWidth}px, ${((1 - anchor.y) / 2) * innerHeight}px)`;
      }
    }
    composer.render(dt);
    if (debug) {
      debug.frames++;
      debug.calls = renderer.info.render.calls;
      debug.triangles = renderer.info.render.triangles;
      debug.cpu += performance.now() - t0;
    }
  };

  // ---------- arrivée du ciel (une fois par session ; pas en mouvement réduit, ni sur un lien direct, ni en mesure)
  const params = new URLSearchParams(location.search);
  let seen = false;
  try {
    seen = sessionStorage.getItem('portfolio.intro') === '1';
  } catch {
    /* stockage indisponible : on joue l'intro */
  }
  const wantIntro = params.has('intro') || (!reducedMotion && !seen && !location.hash && !debug);
  const veil = document.querySelector<HTMLElement>('#intro-veil')!;
  let intro: Intro | null = null;
  const onSkip = (): void => intro?.skip();
  const endIntro = (): void => {
    if (!intro) return;
    intro.dispose();
    intro = null;
    Object.assign(scene.fog as THREE.Fog, { near: 40, far: 130 });
    scene.background = null; // retour au ciel CSS (bords jamais visibles depuis la vue d'ouverture)
    controls.enabled = true;
    controls.autoRotate = !reducedMotion;
    document.body.classList.remove('intro');
    for (const ev of ['pointerdown', 'wheel', 'keydown'] as const) removeEventListener(ev, onSkip);
    try {
      sessionStorage.setItem('portfolio.intro', '1');
    } catch {
      /* ignoré */
    }
    setTimeout(() => hint.classList.add('gone'), 9000);
  };
  if (wantIntro) {
    intro = new Intro(HOME.target, HOME.pos, veil);
    scene.background = new THREE.Color();
    scene.add(intro.clouds);
    controls.enabled = false;
    controls.autoRotate = false;
    document.body.classList.add('intro');
    for (const ev of ['pointerdown', 'wheel', 'keydown'] as const) addEventListener(ev, onSkip, { passive: true });
    intro.update(0, camera); // première image déjà vue d'en haut
  } else {
    veil.remove();
    setTimeout(() => hint.classList.add('gone'), 9000);
  }

  const sync = (): void => {
    renderer.setAnimationLoop(document.hidden ? null : frame);
    timer.reset();
  };
  document.addEventListener('visibilitychange', sync);
  sync();
  // attendre les monuments Meshy (6 s au plus : sinon on montre les faits main, remplacés à l'arrivée)
  await Promise.race([monumentsReady, new Promise((r) => setTimeout(r, 6000))]);
  // shaders compilés pendant l'écran d'entrée (en parallèle sur le GPU) : pas de saccade aux premières secondes
  loadText.textContent = t('Derniers réglages…', 'Final touches…');
  await Promise.race([renderer.compileAsync(scene, camera), new Promise((r) => setTimeout(r, 3000))]).catch(() => {});
  loading.classList.add('done');
  // détails (7 Mo) : tout de suite, sauf en qualité basse où on attend le premier zoom rapproché
  loadDetails = (): void => {
    if (detailsAsked) return;
    detailsAsked = true;
    island.loadDetails(`${BASE}models/marseille_details.glb`).catch((e) => console.warn('détails indisponibles', e));
  };
  if (level !== 'low') loadDetails();


  // lien direct vers un lieu : …/#velodrome
  const fromHash = (): void => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && PLACES.some((p) => p.id === id)) select(id);
  };
  addEventListener('hashchange', fromHash);
  fromHash();
}
