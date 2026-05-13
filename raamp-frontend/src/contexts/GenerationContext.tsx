import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { toast } from 'sonner';
import type { ContentGenerationResponse } from '@/services/contentGenerationService';
import type { MediaGenerationResponse } from '@/services/mediaGenerationService';

interface GenerationJob {
  id: string;
  type: 'content' | 'images' | 'video' | 'reel';
  status: 'pending' | 'generating' | 'completed' | 'failed';
  startedAt: number;
  completedAt?: number;
  prompt: string;
  aspectRatio?: string;
  contentType?: string;
  result?: ContentGenerationResponse | MediaGenerationResponse | null;
  error?: string;
}

interface GenerationContextType {
  jobs: GenerationJob[];
  addJob: (job: Omit<GenerationJob, 'id' | 'startedAt' | 'status'>) => string;
  updateJob: (id: string, updates: Partial<GenerationJob>) => void;
  completeJob: (id: string, result: any) => void;
  failJob: (id: string, error: string) => void;
  getJob: (id: string) => GenerationJob | undefined;
  clearCompletedJobs: () => void;
  // Persistent storage for Creative Studio
  savedContent: ContentGenerationResponse | null;
  setSavedContent: (content: ContentGenerationResponse | null) => void;
  savedImages: string[];
  setSavedImages: (images: string[]) => void;
  savedImageAssetMap: Map<string, string>;
  setSavedImageAssetMap: (map: Map<string, string>) => void;
  savedVideos: MediaGenerationResponse | null;
  setSavedVideos: (videos: MediaGenerationResponse | null) => void;
  clearAllGeneration: () => void;
}

const GenerationContext = createContext<GenerationContextType | undefined>(undefined);

const STORAGE_KEY = 'generation_context_state';
const STORAGE_EXPIRY_HOURS = 24;

interface StoredState {
  jobs: GenerationJob[];
  savedContent: ContentGenerationResponse | null;
  savedImages: string[];
  savedImageAssetMap: Record<string, string>;
  savedVideos: MediaGenerationResponse | null;
  timestamp: number;
}

function loadStoredState(): StoredState | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    
    const state: StoredState = JSON.parse(stored);
    
    // Check expiry
    const hoursSince = (Date.now() - state.timestamp) / (1000 * 60 * 60);
    if (hoursSince > STORAGE_EXPIRY_HOURS) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    
    return state;
  } catch (err) {
    console.error('Failed to load stored generation state:', err);
    return null;
  }
}

function saveState(state: Partial<StoredState>) {
  try {
    const current = loadStoredState();
    const updated: StoredState = {
      jobs: state.jobs ?? current?.jobs ?? [],
      savedContent: state.savedContent ?? current?.savedContent ?? null,
      savedImages: state.savedImages ?? current?.savedImages ?? [],
      savedImageAssetMap: state.savedImageAssetMap ?? current?.savedImageAssetMap ?? {},
      savedVideos: state.savedVideos ?? current?.savedVideos ?? null,
      timestamp: Date.now(),
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (err) {
    console.error('Failed to save generation state:', err);
  }
}

export function GenerationProvider({ children }: { children: ReactNode }) {
  const [jobs, setJobs] = useState<GenerationJob[]>([]);
  const [savedContent, setSavedContentState] = useState<ContentGenerationResponse | null>(null);
  const [savedImages, setSavedImagesState] = useState<string[]>([]);
  const [savedImageAssetMap, setSavedImageAssetMapState] = useState<Map<string, string>>(new Map());
  const [savedVideos, setSavedVideosState] = useState<MediaGenerationResponse | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    const stored = loadStoredState();
    if (stored) {
      setJobs(stored.jobs);
      setSavedContentState(stored.savedContent);
      setSavedImagesState(stored.savedImages);
      setSavedImageAssetMapState(new Map(Object.entries(stored.savedImageAssetMap)));
      setSavedVideosState(stored.savedVideos);
      
      // Show toast for any completed jobs
      const completedJobs = stored.jobs.filter(j => j.status === 'completed' && !j.completedAt);
      if (completedJobs.length > 0) {
        toast.success('Generation completed while you were away', {
          description: `${completedJobs.length} generation(s) finished successfully`,
          duration: 5000,
        });
      }
    }
  }, []);

  // Persist state changes
  useEffect(() => {
    saveState({
      jobs,
      savedContent,
      savedImages,
      savedImageAssetMap: Object.fromEntries(savedImageAssetMap),
      savedVideos,
    });
  }, [jobs, savedContent, savedImages, savedImageAssetMap, savedVideos]);

  const addJob = useCallback((jobData: Omit<GenerationJob, 'id' | 'startedAt' | 'status'>) => {
    const id = `${jobData.type}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const newJob: GenerationJob = {
      ...jobData,
      id,
      startedAt: Date.now(),
      status: 'generating',
    };
    setJobs(prev => [...prev, newJob]);
    return id;
  }, []);

  const updateJob = useCallback((id: string, updates: Partial<GenerationJob>) => {
    setJobs(prev => prev.map(job => 
      job.id === id ? { ...job, ...updates } : job
    ));
  }, []);

  const completeJob = useCallback((id: string, result: any) => {
    setJobs(prev => prev.map(job => 
      job.id === id 
        ? { ...job, status: 'completed' as const, result, completedAt: Date.now() } 
        : job
    ));
    
    // Show completion toast
    const job = jobs.find(j => j.id === id);
    if (job) {
      toast.success(`${job.type.charAt(0).toUpperCase() + job.type.slice(1)} Generated!`, {
        description: 'Your content is ready in Creative Studio',
        duration: 5000,
        action: {
          label: 'View',
          onClick: () => {
            window.location.href = '/dashboard/creative';
          },
        },
      });
    }
  }, [jobs]);

  const failJob = useCallback((id: string, error: string) => {
    setJobs(prev => prev.map(job => 
      job.id === id 
        ? { ...job, status: 'failed' as const, error, completedAt: Date.now() } 
        : job
    ));
    
    toast.error('Generation failed', {
      description: error,
      duration: 5000,
    });
  }, []);

  const getJob = useCallback((id: string) => {
    return jobs.find(job => job.id === id);
  }, [jobs]);

  const clearCompletedJobs = useCallback(() => {
    setJobs(prev => prev.filter(job => job.status !== 'completed' && job.status !== 'failed'));
  }, []);

  const setSavedContent = useCallback((content: ContentGenerationResponse | null) => {
    setSavedContentState(content);
  }, []);

  const setSavedImages = useCallback((images: string[]) => {
    setSavedImagesState(images);
  }, []);

  const setSavedImageAssetMap = useCallback((map: Map<string, string>) => {
    setSavedImageAssetMapState(map);
  }, []);

  const setSavedVideos = useCallback((videos: MediaGenerationResponse | null) => {
    setSavedVideosState(videos);
  }, []);

  const clearAllGeneration = useCallback(() => {
    setSavedContentState(null);
    setSavedImagesState([]);
    setSavedImageAssetMapState(new Map());
    setSavedVideosState(null);
    setJobs([]);
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return (
    <GenerationContext.Provider
      value={{
        jobs,
        addJob,
        updateJob,
        completeJob,
        failJob,
        getJob,
        clearCompletedJobs,
        savedContent,
        setSavedContent,
        savedImages,
        setSavedImages,
        savedImageAssetMap,
        setSavedImageAssetMap,
        savedVideos,
        setSavedVideos,
        clearAllGeneration,
      }}
    >
      {children}
    </GenerationContext.Provider>
  );
}

export function useGeneration() {
  const context = useContext(GenerationContext);
  if (!context) {
    throw new Error('useGeneration must be used within GenerationProvider');
  }
  return context;
}
