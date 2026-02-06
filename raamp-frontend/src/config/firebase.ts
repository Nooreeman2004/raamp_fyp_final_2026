// Firebase Configuration
import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';
import { getStorage } from 'firebase/storage';
import { getAnalytics } from 'firebase/analytics';

// Your Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyCEwamGOxOTjst79Xr-yHhpWEXcLrJ3Jhs",
  authDomain: "raamp-82bbe.firebaseapp.com",
  projectId: "raamp-82bbe",
  storageBucket: "raamp-82bbe.firebasestorage.app",
  messagingSenderId: "234897097308",
  appId: "1:234897097308:web:040d26581ad5ef5d5b5c99",
  measurementId: "G-Y2GK7GQ27G"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication
export const auth = getAuth(app);

// Initialize Firebase Storage
export const storage = getStorage(app);

// Initialize Analytics (only in browser)
let analytics = null;
if (typeof window !== 'undefined') {
  try {
    analytics = getAnalytics(app);
  } catch (error) {
    console.warn('Firebase Analytics not available:', error);
  }
}

export { analytics };

// Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account', // Always show account selection
});
