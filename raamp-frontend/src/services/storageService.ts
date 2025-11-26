import { storage } from '@/config/firebase';
import { ref, uploadBytes, getDownloadURL } from 'firebase/storage';

/**
 * Upload a file to Firebase Storage
 * @param file - The file to upload
 * @param path - The storage path (e.g., 'profile-pictures/user123.jpg')
 * @returns The download URL of the uploaded file
 */
export async function uploadFile(
  file: File,
  path: string
): Promise<string> {
  try {
    // Create a storage reference
    const storageRef = ref(storage, path);
    
    // Upload the file
    const snapshot = await uploadBytes(storageRef, file);
    
    // Get the download URL
    const downloadURL = await getDownloadURL(snapshot.ref);
    
    return downloadURL;
  } catch (error) {
    console.error('Error uploading file:', error);
    throw new Error('Failed to upload file to storage');
  }
}

/**
 * Upload a user profile picture
 * @param file - The image file
 * @param userId - The user's ID or email
 * @returns The download URL of the uploaded profile picture
 */
export async function uploadProfilePicture(
  file: File,
  userId: string
): Promise<string> {
  // Validate file type
  if (!file.type.startsWith('image/')) {
    throw new Error('File must be an image');
  }
  
  // Validate file size (max 5MB)
  const maxSize = 5 * 1024 * 1024; // 5MB
  if (file.size > maxSize) {
    throw new Error('File size must be less than 5MB');
  }
  
  // Generate unique filename
  const timestamp = Date.now();
  const fileExtension = file.name.split('.').pop() || 'jpg';
  const sanitizedUserId = userId.replace(/[^a-zA-Z0-9]/g, '_');
  const fileName = `profile-pictures/${sanitizedUserId}_${timestamp}.${fileExtension}`;
  
  return uploadFile(file, fileName);
}

