import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { mergeChildren } from './merge';

const HEIGHT = 0.2; // figurine « mascotte » : ≈ 3 étages de la ville

/** Trystan (modèle Meshy d'après sa photo, squelette et animations Meshy), sur le parvis de Notre-Dame :
 *  il respire, et fait coucou de temps en temps ou au clic. */
export class Trystan {
  readonly group = Object.assign(new THREE.Group(), { name: 'trystan' });
  private mixer: THREE.AnimationMixer | null = null;
  private idle: THREE.AnimationAction | null = null;
  private wave: THREE.AnimationAction | null = null;
  private nextWave = 3;
  private meshes: THREE.Mesh[] = [];

  async load(url: string): Promise<void> {
    const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url);
    const model = gltf.scene;
    // mise à l'échelle d'après la vraie hauteur du modèle (Meshy le sort en mètres)
    const h = new THREE.Box3().setFromObject(model).getSize(new THREE.Vector3()).y || 1;
    model.scale.setScalar(HEIGHT / h);
    // blocs fixes fusionnés sous chaque os animé : 134 maillages → quelques dizaines
    const animated = new Set(gltf.animations.flatMap((a) => a.tracks.map((t) => t.name.split('.')[0])));
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      const mat = m.isMesh ? (m.material as THREE.MeshStandardMaterial) : null;
      if (mat && !mat.map) mat.flatShading = true; // blocs unis seulement ; le modèle texturé garde son lissage
    });
    mergeChildren(model, (o) => animated.has(o.name));
    model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      m.castShadow = true;
      this.meshes.push(m);
    });
    this.group.add(model);
    this.mixer = new THREE.AnimationMixer(model);
    const clip = (n: string) => gltf.animations.find((a) => a.name === n);
    const idle = clip('idle'), wave = clip('coucou');
    if (idle) { this.idle = this.mixer.clipAction(idle); this.idle.play(); }
    if (wave) {
      this.wave = this.mixer.clipAction(wave);
      this.wave.setLoop(THREE.LoopRepeat, 2);
      this.wave.clampWhenFinished = false;
      this.mixer.addEventListener('finished', () => { this.wave!.fadeOut(0.3); this.idle?.reset().fadeIn(0.3).play(); });
    }
  }

  /** Pose la figurine en (x, y, z), tournée vers la direction (dx, dz). */
  place(x: number, y: number, z: number, dx: number, dz: number): void {
    this.group.position.set(x, y, z);
    this.group.rotation.y = Math.atan2(dx, dz); // la façade du modèle regarde +z
  }

  coucou(): void {
    if (!this.wave || this.wave.isRunning()) return;
    this.idle?.fadeOut(0.25);
    this.wave.reset().fadeIn(0.25).play();
    this.nextWave = 9 + Math.random() * 6;
  }

  hit(raycaster: THREE.Raycaster): boolean {
    return this.meshes.length > 0 && raycaster.intersectObjects(this.meshes, false).length > 0;
  }

  update(dt: number): void {
    if (!this.mixer) return;
    this.nextWave -= dt;
    if (this.nextWave <= 0) this.coucou();
    this.mixer.update(dt);
  }
}
