// Firebase Configuration
const firebaseConfig = {
  apiKey: "AIzaSyCkxx2HOkhUMsVb3ppcvu-33qkJOAwUVJ8",
  authDomain: "pubg-frame-check.firebaseapp.com",
  databaseURL: "https://pubg-frame-check-default-rtdb.firebaseio.com",
  projectId: "pubg-frame-check",
  storageBucket: "pubg-frame-check.firebasestorage.app",
  messagingSenderId: "260382564636",
  appId: "1:260382564636:web:9fff5d76e3246855139ad9"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();