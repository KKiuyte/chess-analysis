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
