import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { commentAnalysisService, PostCommentAnalysisSummary } from "@/services/commentAnalysisService";
import { ShieldCheck, ShieldAlert, MessageSquare, PieChart, Info, RefreshCw, Smile, Meh, Frown } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { toast } from "sonner";

interface CommentIntelligenceGridProps {
  postId: string;
}

export function CommentIntelligenceGrid({ postId }: CommentIntelligenceGridProps) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<PostCommentAnalysisSummary | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await commentAnalysisService.getPostSummary(postId);
      setData(result);
    } catch (error) {
      console.error("Failed to fetch comment analysis:", error);
      toast.error("Failed to load comment intelligence");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (postId) {
      fetchData();
    }
  }, [postId]);

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 w-full bg-foreground/5 rounded-xl" />
          ))}
        </div>
        <Skeleton className="h-64 w-full bg-foreground/5 rounded-xl" />
      </div>
    );
  }

  if (!data || data.total === 0) {
    return (
      <Card className="p-8 border-dashed border-border/50 bg-foreground/5 flex flex-col items-center justify-center text-center space-y-3">
        <div className="p-3 rounded-full bg-foreground/5 text-muted-foreground/40">
          <MessageSquare className="w-8 h-8" />
        </div>
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground">No comments to analyze yet</p>
          <p className="text-xs text-muted-foreground/60 max-w-[200px]">
            Analysis will appear here once your post receives engagement.
          </p>
        </div>
      </Card>
    );
  }

  const spamRate = Math.round((data.spam_count / data.total) * 100);
  const positiveRate = Math.round((data.sentiment_summary.POSITIVE / (data.total - data.spam_count || 1)) * 100);

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-card/40 border-border/50 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Total Comments</span>
            <MessageSquare className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-2 text-2xl font-bold">{data.total}</div>
        </Card>

        <Card className="p-4 bg-card/40 border-border/50 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Spam Defense</span>
            {data.spam_count > 0 ? (
              <ShieldAlert className="w-4 h-4 text-orange-500" />
            ) : (
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            )}
          </div>
          <div className="mt-2 flex items-end gap-2">
            <div className="text-2xl font-bold">{data.spam_count}</div>
            <div className="text-[10px] font-mono text-muted-foreground pb-1">({spamRate}% Flagged)</div>
          </div>
        </Card>

        <Card className="p-4 bg-card/40 border-border/50 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Brand Sentiment</span>
            <Smile className="w-4 h-4 text-primary" />
          </div>
          <div className="mt-2 flex items-end gap-2">
            <div className="text-2xl font-bold">{positiveRate}%</div>
            <div className="text-[10px] font-mono text-muted-foreground pb-1">Positive</div>
          </div>
        </Card>
      </div>

      {/* Sentiment Breakdown */}
      <Card className="p-6 bg-card/40 border-border/50 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <PieChart className="w-4 h-4 text-primary" />
            <h3 className="text-sm font-semibold tracking-wide">Sentiment Distribution</h3>
          </div>
          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground" onClick={fetchData}>
            <RefreshCw className="w-3 h-3" />
          </Button>
        </div>

        <div className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-mono uppercase tracking-widest text-emerald-500">
              <span>Positive</span>
              <span>{data.sentiment_summary.POSITIVE} comments</span>
            </div>
            <Progress value={positiveRate} className="h-1.5 bg-emerald-500/10" />
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
              <span>Neutral</span>
              <span>{data.sentiment_summary.NEUTRAL} comments</span>
            </div>
            <Progress 
              value={Math.round((data.sentiment_summary.NEUTRAL / (data.total - data.spam_count || 1)) * 100)} 
              className="h-1.5 bg-foreground/5" 
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-[10px] font-mono uppercase tracking-widest text-rose-500">
              <span>Negative</span>
              <span>{data.sentiment_summary.NEGATIVE} comments</span>
            </div>
            <Progress 
              value={Math.round((data.sentiment_summary.NEGATIVE / (data.total - data.spam_count || 1)) * 100)} 
              className="h-1.5 bg-rose-500/10" 
            />
          </div>
        </div>
      </Card>

      {/* Intelligence Feed */}
      <Card className="bg-card/40 border-border/50 overflow-hidden">
        <div className="p-4 border-b border-border/50 bg-foreground/5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-primary" />
            <span className="text-[10px] font-mono font-medium text-muted-foreground uppercase tracking-widest">
              Live Comment Enrichment
            </span>
          </div>
          <Badge variant="outline" className="text-[9px] border-primary/20 text-primary uppercase font-mono">
            AI Enriched
          </Badge>
        </div>
        
        <div className="divide-y divide-border/30 max-h-[400px] overflow-y-auto">
          {data.comments.map((comment) => (
            <div key={comment.id} className={`p-4 space-y-2 transition-colors ${comment.is_spam ? 'bg-orange-500/5' : 'hover:bg-foreground/5'}`}>
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {comment.is_spam ? (
                    <Badge variant="outline" className="bg-orange-500/10 text-orange-500 border-orange-500/20 text-[9px] px-1.5 h-5 font-mono">
                      SPAM ({Math.round(comment.spam_confidence * 100)}%)
                    </Badge>
                  ) : (
                    <Badge variant="outline" className={`text-[9px] px-1.5 h-5 font-mono ${
                      comment.sentiment === 'POSITIVE' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                      comment.sentiment === 'NEGATIVE' ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' :
                      'bg-foreground/5 text-muted-foreground border-border/50'
                    }`}>
                      {comment.sentiment}
                    </Badge>
                  )}
                  <span className="text-[10px] font-mono text-muted-foreground/60">
                    {new Date(comment.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                {!comment.is_spam && (
                  <div className="flex items-center gap-1">
                    {comment.sentiment === 'POSITIVE' && <Smile className="w-3 h-3 text-emerald-500" />}
                    {comment.sentiment === 'NEUTRAL' && <Meh className="w-3 h-3 text-muted-foreground" />}
                    {comment.sentiment === 'NEGATIVE' && <Frown className="w-3 h-3 text-rose-500" />}
                  </div>
                )}
              </div>
              <p className="text-xs text-foreground/90 line-clamp-3 leading-relaxed">
                {comment.text}
              </p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
