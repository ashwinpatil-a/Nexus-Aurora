// src/firebase.js
import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

// REPLACE THIS WITH YOUR ACTUAL CONFIG FROM FIREBASE CONSOLE
const firebaseConfig = {
  apiKey: "AIzaSyCv3UzYdVc7_s0Yw7RptfMiaBiRF8erfcE",
  authDomain: "nexgen-ab179.firebaseapp.com",
  projectId: "nexgen-ab179",
  storageBucket: "nexgen-ab179.firebasestorage.app",
  messagingSenderId: "618304851920",
  appId: "1:618304851920:web:afec20a6b58b4e91a973d5"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);