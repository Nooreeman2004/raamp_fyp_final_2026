import { Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useNavigate } from "react-router-dom";

export function TrendHistoryTable({ trendHistory }: { trendHistory: any[] }) {
  const navigate = useNavigate();

  if (trendHistory.length === 0) {
    return (
      <div className="p-20 border border-dashed border-border/30 rounded-2xl text-center opacity-30 w-full">
        <Database className="w-10 h-10 mx-auto mb-4" />
        <p className="text-[10px] font-mono uppercase tracking-[0.3em]">No previous executions logged</p>
      </div>
    );
  }

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border/50 bg-white/[0.015]">
      <table className="w-full text-left text-sm text-muted-foreground whitespace-nowrap">
        <thead className="bg-foreground/5 text-xs uppercase font-mono tracking-widest text-white/50">
          <tr>
            <th className="px-6 py-4 font-semibold w-[30%]">Keyword</th>
            <th className="px-6 py-4 font-semibold w-[20%]">Executed at</th>
            <th className="px-6 py-4 font-semibold w-[20%]">Context</th>
            <th className="px-6 py-4 font-semibold w-[15%]">Source</th>
            <th className="px-6 py-4 font-semibold text-right w-[15%]">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border/20">
          {trendHistory.map((history, idx) => {
            const location = String(history.location || "—");
            const niche = String(history.niche || "—");
            const source = String(history.trend_source || "execute").toUpperCase();

            return (
              <tr
                key={history.id || idx}
                className={`hover:bg-white/[0.04] transition-colors ${idx % 2 === 0 ? "bg-white/[0.01]" : "bg-transparent"}`}
              >
                <td className="px-6 py-4 font-bold font-heading text-foreground uppercase tracking-widest">
                  {history.trend_keyword || "—"}
                </td>
                <td className="px-6 py-4 font-mono text-xs">
                  {history.timestamp ? new Date(history.timestamp).toLocaleString() : "—"}
                </td>
                <td className="px-6 py-4">
                  <div className="flex flex-col">
                    <span className="text-xs text-white/80">{niche}</span>
                    <span className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">{location}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <Badge variant="outline" className="font-mono text-[10px] tracking-widest uppercase bg-white/5 border-white/10 text-white/60">
                    {source}
                  </Badge>
                </td>
                <td className="px-6 py-4 text-right">
                  <Button 
                    variant="link" 
                    className="p-0 h-auto text-[10px] font-black text-primary hover:text-white uppercase tracking-widest"
                    onClick={() => navigate("/dashboard/creative", { state: { prefillPrompt: history.generated_prompt } })}
                    disabled={!history.generated_prompt}
                  >
                    View Details →
                  </Button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
