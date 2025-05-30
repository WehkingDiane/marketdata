/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 *
*
*const {onRequest} = require("firebase-functions/v2/https");
*const logger = require("firebase-functions/logger");
*/
// Create and deploy your first functions
// https://firebase.google.com/docs/functions/get-started

// exports.helloWorld = onRequest((request, response) => {
//   logger.info("Hello logs!", {structuredData: true});
//   response.send("Hello from Firebase!");
// });
const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();

exports.sendTradeSignal = functions.database
  .ref("/signals/{symbol}/{timestamp}")
  .onCreate(async (snapshot, context) => {
    const signalData = snapshot.val();
    const symbol = context.params.symbol;
    const timestamp = context.params.timestamp;

    const payload = {
      notification: {
        title: `Signal: ${signalData.type.toUpperCase()} ${symbol}`,
        body: `Preis: ${signalData.price}, Zeit: ${timestamp}`,
      },
    };

    // FCM Token(s) abrufen – Beispiel für einen Benutzer
    const tokenSnap = await admin.database().ref("/users/user123/token").once("value");
    const token = tokenSnap.val();

    if (token) {
      await admin.messaging().sendToDevice(token, payload);
      console.log(`Signal für ${symbol} versendet`);
    } else {
      console.log("Kein FCM-Token vorhanden");
    }
  });