// Figurine de Trystan en costume (Meshy : photo du CV → image stylisée → tenue changée → 3D → squelette → animations Idle + Wave_One_Hand)
// → public/models/trystan.glb. Clips renommés comme les attend src/trystan.ts (idle, coucou), texture 1024 webp, meshopt.
// Usage : node scripts/build_perso.mjs   (source hors git : blender/model-try/meshy-1119/perso_costume_anim.glb)
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { dedup, prune, quantize, textureCompress, meshopt } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const SRC = 'blender/model-try/meshy-1119/perso_costume_anim.glb'; // version en costume et mocassins
const OUT = 'public/models/trystan.glb';
const NOMS = { Idle: 'idle', Wave_One_Hand: 'coucou' };
await MeshoptDecoder.ready;
await MeshoptEncoder.ready;
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
const doc = await io.read(SRC);
for (const a of doc.getRoot().listAnimations()) a.setName(NOMS[a.getName()] ?? a.getName());
for (const n of doc.getRoot().listNodes()) if (n.getMesh()) n.setName('trystan_corps');
await doc.transform(
  dedup(),
  textureCompress({ encoder: sharp, targetFormat: 'webp', resize: [1024, 1024] }),
  quantize(),
  meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
  prune(),
);
doc.createExtension(EXTMeshoptCompression).setRequired(true);
await io.write(OUT, doc);
console.log(`${SRC} -> ${OUT} : clips ${doc.getRoot().listAnimations().map((a) => a.getName()).join(', ')}`);
