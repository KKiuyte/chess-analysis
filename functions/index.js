// Lance le job Cloud Run « analyse » quand une demande requests/{pseudo} passe à « pending »
// (création par l'appli, ou relance d'une mise à jour).
const { onDocumentWritten } = require("firebase-functions/v2/firestore");
const { logger } = require("firebase-functions");
const { JobsClient } = require("@google-cloud/run").v2;
const { FieldValue } = require("firebase-admin/firestore");
require("firebase-admin/app").initializeApp();

const REGION = "europe-west1";
const JOB = `projects/analyse-echecs/locations/${REGION}/jobs/analyse`;
const jobs = new JobsClient();

exports.lancerAnalyse = onDocumentWritten({ document: "requests/{pseudo}", region: REGION }, async (event) => {
  const before = event.data?.before?.data();
  const after = event.data?.after?.data();
  if (!after || after.status !== "pending") return;
  // Déjà « pending » avant : ne relancer que si la demande a été renouvelée (nouvelle date).
  if (before?.status === "pending" && before.created?.isEqual?.(after.created)) return;
  const pseudo = event.params.pseudo;
  try {
    await jobs.runJob({ name: JOB, overrides: { containerOverrides: [{ args: [pseudo] }] } });
    await event.data.after.ref.update({ status: "queued", step: "En file d'attente", error: null, updatedAt: FieldValue.serverTimestamp() });
    logger.info(`analyse lancée pour ${pseudo}`);
  } catch (e) {
    logger.error(`lancement impossible pour ${pseudo}`, e);
    await event.data.after.ref.update({
      status: "error", error: "Impossible de lancer l'analyse pour l'instant.",
      finished: FieldValue.serverTimestamp(), updatedAt: FieldValue.serverTimestamp(),
    });
  }
});

// Mise à jour automatique chaque nuit à 4 h (heure de Paris) : une demande « pending » par pseudo dont
// un compte s'est connecté depuis moins de 30 jours (users/{uid}.seen, écrit par l'appli), sauf analyse
// déjà en cours. Le job s'arrête aussitôt s'il n'y a aucune nouvelle partie ; le bilan IA garde ses
// propres règles (20 nouvelles parties ou 7 jours), la relance nocturne ne coûte donc aucun jeton de plus.
const { onSchedule } = require("firebase-functions/v2/scheduler");
const { getFirestore, Timestamp } = require("firebase-admin/firestore");
const ACTIVE_DAYS = 30;

exports.relanceNocturne = onSchedule({ schedule: "0 4 * * *", timeZone: "Europe/Paris", region: REGION }, async () => {
  const db = getFirestore();
  const limit = Date.now() - ACTIVE_DAYS * 86400e3;
  const seen = {};                       // pseudo → dernière connexion (tous comptes confondus)
  for (const d of (await db.collection("users").get()).docs) {
    const { pseudo, seen: s } = d.data();
    if (pseudo && s?.toMillis) seen[pseudo] = Math.max(seen[pseudo] || 0, s.toMillis());
  }
  let launched = 0, skipped = 0;
  for (const [pseudo, t] of Object.entries(seen)) {
    if (t < limit) { skipped++; continue; }
    const ref = db.collection("requests").doc(pseudo);
    const r = (await ref.get()).data();
    if (r && ["pending", "queued", "running"].includes(r.status)) { skipped++; continue; }
    await ref.set({ pseudo, status: "pending", auto: true, created: Timestamp.now() }, { merge: true });
    launched++;
  }
  logger.info(`relance nocturne : ${launched} lancée(s), ${skipped} ignorée(s)`);
});
