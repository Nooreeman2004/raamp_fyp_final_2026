import { signInWithPopup, UserCredential } from 'firebase/auth';
import { auth, googleProvider } from '@/config/firebase';
import type { GoogleAuthResult } from '@/types';

// Note: GoogleAuthResult is now centralized in @/types/auth.types.ts

/**
 * Sign in with Google using Firebase popup
 */
export const signInWithGoogle = async (): Promise<GoogleAuthResult> => {
  try {
    const result: UserCredential = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    
    // Get ID token to send to backend
    const idToken = await user.getIdToken();
    
    return {
      uid: user.uid,
      email: user.email!,
      displayName: user.displayName!,
      photoURL: user.photoURL,
      idToken,
    };
  } catch (error: any) {
    console.error('Google sign-in error:', error);
    throw new Error(error.message || 'Failed to sign in with Google');
  }
};

/**
 * Sign out from Firebase
 */
export const signOut = async (): Promise<void> => {
  await auth.signOut();
};
