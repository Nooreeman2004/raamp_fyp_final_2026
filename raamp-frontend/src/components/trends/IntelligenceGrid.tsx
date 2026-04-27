import { useState, useEffect } from "react";
import { trendService } from "@/services/trendService";
import { Copy, RefreshCw, Music, UserCheck, Search, Activity, Play, Megaphone, Hash, HashIcon } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";

interface IntelligenceGridProps {
  trendId: string | null;
  aiAnalysisStatus: "pending" | "ready" | "failed" | null;
  aiAnalysisData: any;
  location: string;
  niche: string;
  userPlatform: string;
  keyword: string;
}

export function IntelligenceGrid({ trendId, aiAnalysisStatus, aiAnalysisData, location, niche, userPlatform, keyword }: IntelligenceGridProps) {
  const [audioData, setAudioData] = useState<any[]>([]);
  const [audioLoading, setAudioLoading] = useState(false);
  const [influencerData, setInfluencerData] = useState<any[]>([]);
  const [influencerLoading, setInfluencerLoading] = useState(false);

  useEffect(() => {
    let active = true;
    const fetchDynamics = async () => {
      setAudioLoading(true);
      setInfluencerLoading(true);
      try {
        const platform = userPlatform || "instagram";
        const geo = String(location || "GLOBAL").trim().toUpperCase();
        // Use keyword if available, otherwise fallback to niche
        const searchTerm = keyword || niche || "trending";

        console.log("🎵 Fetching dynamics with:", { platform, geo, niche, searchTerm });

        const [audioRes, influencerRes] = await Promise.all([
          trendService.getViralAudio(platform, geo, niche, searchTerm).catch((err) => {
            console.error("🎵 Audio fetch error:", err);
            return { recommended_tracks: [] };
          }),
          trendService.getInfluencerRadar(geo, niche, searchTerm).catch((err) => {
            console.error("👥 Influencer fetch error:", err);
            return { influencers: [] };
          }),
        ]);

        console.log("🎵 Raw Audio Response:", audioRes);
        console.log("👥 Raw Influencer Response:", influencerRes);

        let tracks = (audioRes as any)?.recommended_tracks || [];
        let influencers = (influencerRes as any)?.influencers || [];

        console.log("🎵 Extracted tracks:", tracks, "Length:", tracks.length);
        console.log("👥 Extracted influencers:", influencers, "Length:", influencers.length);

        // Fallback: if region-specific feeds are empty for country codes (e.g., PK), retry with GLOBAL.
        if ((geo.length === 2 || geo === "PK") && tracks.length === 0) {
          console.log("🎵 Attempting GLOBAL fallback for audio...");
          const fallbackAudio = await trendService.getViralAudio(platform, "GLOBAL", niche, searchTerm).catch(() => ({ recommended_tracks: [] }));
          console.log("🎵 Fallback Audio Response:", fallbackAudio);
          tracks = (fallbackAudio as any)?.recommended_tracks || tracks;
          console.log("🎵 Tracks after fallback:", tracks, "Length:", tracks.length);
        }
        if ((geo.length === 2 || geo === "PK") && influencers.length === 0) {
          console.log("👥 Attempting GLOBAL fallback for influencers...");
          const fallbackInf = await trendService.getInfluencerRadar("GLOBAL", niche, searchTerm).catch(() => ({ influencers: [] }));
          influencers = (fallbackInf as any)?.influencers || influencers;
        }

        if (active) {
          console.log("🎵 Viral Audio Data Received:", tracks);
          console.log("👥 Influencer Data Received:", influencers);
          setAudioData(tracks);
          setInfluencerData(influencers);
        }
      } catch (err) {
        console.error("Dynamics fetch error", err);
        if (active) {
          toast.warning("Intelligence data unavailable", {
            description: "Viral audio and influencer insights couldn't be loaded."
          });
        }
      } finally {
        if (active) {
            setAudioLoading(false);
            setInfluencerLoading(false);
        }
      }
    };

    // Fetch if we have at least location and niche (keyword is optional)
    if (location && niche) {
      fetchDynamics();
    } else {
      // If we don't have required data, stop loading immediately
      setAudioLoading(false);
      setInfluencerLoading(false);
    }
    
    return () => { active = false; };
  }, [location, niche, userPlatform, keyword]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied!");
  };

  const handleRegenerate = async () => {
    if (!trendId) return;
    toast.info("Regenerating AI Analysis...");
    await trendService.regenerateAIAnalysis(trendId);
    // Let parent component polling handle the status updates
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full">
      {/* Card 1: Campaign Ideas */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-teal-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
             <Megaphone className="w-5 h-5 text-teal-400" />
             <h3 className="font-semibold text-lg">Campaign Ideas</h3>
          </div>
          <button
            onClick={handleRegenerate}
            disabled={!trendId}
            className="text-muted-foreground hover:text-foreground transition-colors disabled:opacity-40"
            title="Regenerate Analysis"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex-1">
          {aiAnalysisStatus !== "ready" ? (
             <div className="space-y-3">
               <Skeleton className="h-16 w-full rounded-xl bg-foreground/5" />
               <Skeleton className="h-16 w-full rounded-xl bg-foreground/5" />
             </div>
          ) : !aiAnalysisData?.campaign_ideas?.length ? (
             <div className="text-sm text-muted-foreground py-4 text-center">No campaign ideas generated yet.</div>
          ) : (
             <div className="space-y-3">
               {aiAnalysisData.campaign_ideas.slice(0, 3).map((idea: any, idx: number) => (
                 <div key={idx} className="bg-background/50 p-3 rounded-lg border border-border/60">
                   <div className="flex justify-between items-start mb-1">
                     <span className="font-medium text-sm text-foreground leading-snug break-words pr-2">
                       {idea.title}
                     </span>
                     <div className="flex gap-1">
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-primary/20 text-primary uppercase font-mono">{idea.platform}</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-700 dark:text-amber-300 uppercase font-mono">{idea.urgency_tag}</span>
                     </div>
                   </div>
                   <p
                     className="text-xs text-muted-foreground leading-relaxed break-words line-clamp-3"
                     title={String(idea.description || "")}
                   >
                     {idea.description}
                   </p>
                 </div>
               ))}
             </div>
          )}
        </div>
      </div>

      {/* Card 2: Trending Hashtags */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-teal-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center mb-4 gap-2">
            <Hash className="w-5 h-5 text-teal-500" />
            <h3 className="font-semibold text-lg">Trending Hashtags</h3>
        </div>
        
        <div className="flex-1">
          {aiAnalysisStatus !== "ready" ? (
             <div className="space-y-4">
                <div><Skeleton className="h-4 w-20 mb-2 bg-foreground/5" /><Skeleton className="h-8 w-full bg-foreground/5" /></div>
             </div>
          ) : !aiAnalysisData?.hashtag_pack ? (
             <div className="text-sm text-muted-foreground py-4 text-center">Run scan to generate hashtags</div>
          ) : (
             <div className="space-y-4">
               {['primary', 'secondary', 'niche'].map((group) => {
                 const tags = aiAnalysisData.hashtag_pack[group];
                 if (!tags || tags.length === 0) return null;
                 return (
                   <div key={group}>
                     <div className="text-[10px] uppercase tracking-widest text-muted-foreground/70 mb-1.5">{group}</div>
                     <div className="flex flex-wrap gap-1.5">
                       {tags.map((tag: string, idx: number) => (
                         <button 
                           key={idx} 
                           onClick={() => copyToClipboard(`#${tag.replace(/^#/, '')}`)}
                           className="px-2 py-1 bg-foreground/5 hover:bg-foreground/10 rounded-md text-xs font-mono text-foreground transition-colors border border-border/60"
                         >
                           #{tag.replace(/^#/, '')}
                         </button>
                       ))}
                     </div>
                   </div>
                 );
               })}
             </div>
          )}
        </div>
      </div>

      {/* Card 3: Trending Audio (Charting) */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-teal-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center mb-4 gap-2">
            <Music className="w-5 h-5 text-teal-500" />
            <h3 className="font-semibold text-lg">Trending Audio (Charting)</h3>
        </div>
        
        <div className="flex-1">
          {audioLoading ? (
             <div className="space-y-3">
               <Skeleton className="h-12 w-full rounded-xl bg-foreground/5" />
               <Skeleton className="h-12 w-full rounded-xl bg-foreground/5" />
             </div>
          ) : audioData.length === 0 ? (
             <div className="text-sm text-muted-foreground py-4 text-center space-y-2">
               <Music className="w-8 h-8 mx-auto opacity-30" />
               <p>Loading trending audio...</p>
               <p className="text-xs opacity-60">This may take a moment</p>
             </div>
          ) : (
             <div className="space-y-3">
                {audioData.slice(0, 3).map((audio, idx) => (
                  <div key={idx} className="flex items-center justify-between bg-background/50 p-3 rounded-lg border border-border/60">
                    <div className="flex items-center gap-3 overflow-hidden">
                      {audio.image ? (
                        <img 
                          src={audio.image} 
                          alt={audio.track_name} 
                          className="w-10 h-10 rounded-md object-cover bg-foreground/10 shrink-0" 
                        />
                      ) : (
                        <div className="w-10 h-10 rounded-md bg-foreground/10 flex items-center justify-center shrink-0">
                          <Music className="w-4 h-4 text-muted-foreground" />
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className="text-sm font-bold text-foreground truncate" title={audio.track_name}>{audio.track_name || audio.title || "Unknown Audio"}</p>
                        <p className="text-xs text-muted-foreground truncate font-medium">{audio.artist || "Unknown Artist"}</p>
                        {audio.source === "spotify_web_api" && (
                          <div className="flex items-center gap-1 mt-0.5">
                            <span className="text-[8px] text-green-600 dark:text-green-400 font-mono uppercase tracking-tighter">Spotify Verified</span>
                          </div>
                        )}
                      </div>
                    </div>
                   <button 
                     onClick={() => copyToClipboard(audio.track_name || audio.title)}
                     className="shrink-0 px-3 py-1.5 bg-primary/20 hover:bg-primary/30 text-primary rounded-lg text-xs font-medium transition-colors"
                   >
                     Copy Name
                   </button>
                 </div>
               ))}
             </div>
          )}
        </div>
      </div>

      {/* Card 4: Content Format */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-teal-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center mb-4 gap-2">
            <Activity className="w-5 h-5 text-teal-400" />
            <h3 className="font-semibold text-lg">Content Format</h3>
        </div>
        
        <div className="flex-1 flex flex-col justify-center">
          {aiAnalysisStatus !== "ready" ? (
             <Skeleton className="h-24 w-full rounded-xl bg-foreground/5" />
          ) : !aiAnalysisData?.content_format_recommendation ? (
             <div className="text-sm text-muted-foreground py-4 text-center">Format recommendations unavailable.</div>
          ) : (
             <div className="space-y-4">
               <div className="flex items-center gap-4">
                  <div className="text-4xl">
                     {aiAnalysisData.content_format_recommendation.primary_format?.toLowerCase().includes('reel') ? '🎬' : 
                      aiAnalysisData.content_format_recommendation.primary_format?.toLowerCase().includes('carousel') ? '📖' : '⭕'}
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Primary Format</div>
                    <div className="text-xl font-bold">{aiAnalysisData.content_format_recommendation.primary_format || "Any Format"}</div>
                  </div>
               </div>
               {aiAnalysisData.content_format_recommendation.reasoning && (
                 <ul className="text-sm text-muted-foreground space-y-1 pl-2">
                   {aiAnalysisData.content_format_recommendation.reasoning.map((r: string, i: number) => (
                     <li key={i} className="flex gap-2 items-start"><span className="text-teal-500 mt-1">•</span> <span>{r}</span></li>
                   ))}
                 </ul>
               )}
               {aiAnalysisData.content_format_recommendation.secondary_format && (
                 <div className="inline-block px-3 py-1 bg-foreground/5 rounded-full text-xs text-muted-foreground">
                   Alternative: {aiAnalysisData.content_format_recommendation.secondary_format}
                 </div>
               )}
             </div>
          )}
        </div>
      </div>

      {/* Card 5: Growth Hacks */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-teal-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center mb-4 gap-2">
            <Search className="w-5 h-5 text-teal-400" />
            <h3 className="font-semibold text-lg">Growth Hacks</h3>
        </div>
        
        <div className="flex-1">
          {aiAnalysisStatus !== "ready" ? (
             <div className="space-y-2">
               <Skeleton className="h-10 w-full rounded-lg bg-foreground/5" />
               <Skeleton className="h-10 w-full rounded-lg bg-foreground/5" />
             </div>
          ) : !aiAnalysisData?.growth_hacks?.length ? (
             <div className="text-sm text-muted-foreground py-4 text-center">No growth hacks generated.</div>
          ) : (
             <div className="space-y-3">
               {aiAnalysisData.growth_hacks.slice(0, 2).map((hack: string, idx: number) => (
                 <div key={idx} className="flex gap-3 bg-background/50 p-3 rounded-lg border border-border/60">
                   <div className="shrink-0 w-6 h-6 rounded-full bg-teal-500/20 text-teal-400 flex items-center justify-center text-xs font-bold">
                     {idx + 1}
                   </div>
                   <p className="text-sm text-foreground/90">{hack}</p>
                 </div>
               ))}
             </div>
          )}
        </div>
      </div>

      {/* Card 6: Competitor Radar */}
      <div className="rounded-xl bg-card/70 border-l-4 border-l-purple-500 border-border/60 p-5 flex flex-col min-h-[200px] shadow-sm">
        <div className="flex items-center mb-4 gap-2">
            <UserCheck className="w-5 h-5 text-purple-400" />
            <h3 className="font-semibold text-lg">Competitor Radar</h3>
        </div>
        
        <div className="flex-1">
          {influencerLoading ? (
             <div className="space-y-3">
               <Skeleton className="h-12 w-full rounded-lg bg-foreground/5" />
               <Skeleton className="h-12 w-full rounded-lg bg-foreground/5" />
             </div>
          ) : influencerData.length === 0 ? (
             <div className="text-sm text-muted-foreground py-4 text-center space-y-2">
               <UserCheck className="w-8 h-8 mx-auto opacity-30" />
               <p>Scanning for competitors...</p>
               <p className="text-xs opacity-60">Checking Instagram activity</p>
             </div>
          ) : (
             <div className="space-y-3">
               {influencerData.slice(0, 3).map((comp, idx) => (
                 <div key={idx} className="flex items-center justify-between bg-background/50 p-3 rounded-lg border border-border/60">
                   <div className="flex items-center gap-3">
                     <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-600 text-white flex items-center justify-center font-bold text-xs shadow-lg">
                       {comp.handle?.charAt(0)?.toUpperCase() || "?"}
                     </div>
                     <div>
                       <p className="text-sm font-medium text-foreground">@{comp.handle}</p>
                       <p className="text-xs text-muted-foreground flex gap-2">
                         <span>{comp.follower_count_formatted || "Local account"}</span>
                         {comp.engagement_rate && <span className="text-purple-400">• {comp.engagement_rate}% Heat</span>}
                       </p>
                     </div>
                   </div>
                   {comp.url && (
                     <a 
                       href={comp.url} 
                       target="_blank" 
                       rel="noreferrer" 
                       className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-foreground/5 hover:bg-foreground/10 text-xs font-medium text-foreground rounded-lg border border-border/60 transition-all hover:scale-105"
                     >
                       <Play className="w-3 h-3 text-purple-400 fill-purple-400" />
                       View Post
                     </a>
                   )}
                 </div>
               ))}
               <p className="text-[10px] text-muted-foreground/60 text-center mt-2 italic">
                 Based on real-time Instagram activity matching your niche and location.
               </p>
             </div>
          )}
        </div>
      </div>

    </div>
  );
}
