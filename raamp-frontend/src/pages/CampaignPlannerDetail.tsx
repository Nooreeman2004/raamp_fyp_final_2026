import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "@/components/Layout";
import Reveal from "@/components/ui/Reveal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw, Sparkles, TrendingUp } from "lucide-react";
import { campaignPlannerService, CampaignPlanDetailResponse, PlannedPostItem } from "@/services/campaignPlannerService";
import { PlannedPostDrawer } from "@/components/campaign-planner/PlannedPostDrawer";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

function startOfMonth(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), 1);
}
function endOfMonth(d: Date) {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0);
}
function addMonths(d: Date, n: number) {
  return new Date(d.getFullYear(), d.getMonth() + n, 1);
}
function ymd(d: Date) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export default function CampaignPlannerDetail() {
  const { id } = useParams();
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState<CampaignPlanDetailResponse | null>(null);
  const [cursorMonth, setCursorMonth] = useState<Date>(new Date());
  const [selected, setSelected] = useState<PlannedPostItem | null>(null);

  const fetchPlan = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await campaignPlannerService.getPlan(id);
      setPlan(res);
      // Only set initial cursor month if we don't have one yet or it's a new plan
      if (!plan) {
        const sd = res?.start_date ? new Date(res.start_date) : null;
        if (sd && !Number.isNaN(sd.getTime())) {
          setCursorMonth(startOfMonth(sd));
        }
      }
    } catch (e: any) {
      toast.error("Failed to load campaign plan", { description: e?.message || "Please try again." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlan();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Auto-polling if plan is still running
  useEffect(() => {
    if (plan?.generation_status === "running") {
      const interval = setInterval(() => {
        fetchPlan();
      }, 5000);
      return () => clearInterval(interval);
    }
  }, [plan?.generation_status, id]);

  const allowedMonths = useMemo(() => {
    const sd = plan?.start_date ? new Date(plan.start_date) : null;
    const ed = plan?.end_date ? new Date(plan.end_date) : null;
    if (!sd || !ed || Number.isNaN(sd.getTime()) || Number.isNaN(ed.getTime())) return [];
    const start = startOfMonth(sd);
    const end = startOfMonth(ed);
    const out: Date[] = [];
    let cur = start;
    // inclusive months; cap as safety
    for (let i = 0; i < 48; i++) {
      out.push(cur);
      if (cur.getFullYear() === end.getFullYear() && cur.getMonth() === end.getMonth()) break;
      cur = addMonths(cur, 1);
    }
    return out;
  }, [plan?.start_date, plan?.end_date]);

  const cursorKey = useMemo(() => {
    const d = startOfMonth(cursorMonth);
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }, [cursorMonth]);

  const minMonth = allowedMonths[0];
  const maxMonth = allowedMonths.length ? allowedMonths[allowedMonths.length - 1] : null;
  const canPrev = !!minMonth && startOfMonth(cursorMonth).getTime() > startOfMonth(minMonth).getTime();
  const canNext = !!maxMonth && startOfMonth(cursorMonth).getTime() < startOfMonth(maxMonth).getTime();

  // Clamp cursorMonth into allowed range once plan loads/updates.
  useEffect(() => {
    if (!allowedMonths.length) return;
    const cur = startOfMonth(cursorMonth);
    const min = startOfMonth(allowedMonths[0]);
    const max = startOfMonth(allowedMonths[allowedMonths.length - 1]);
    if (cur.getTime() < min.getTime()) setCursorMonth(min);
    else if (cur.getTime() > max.getTime()) setCursorMonth(max);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allowedMonths.length, plan?.start_date, plan?.end_date]);

  const monthDays = useMemo(() => {
    const base = startOfMonth(cursorMonth);
    const last = endOfMonth(cursorMonth);
    const days: Date[] = [];
    const startDow = base.getDay(); // 0 Sun
    for (let i = 0; i < startDow; i++) {
      days.push(new Date(base.getFullYear(), base.getMonth(), base.getDate() - (startDow - i)));
    }
    for (let d = 1; d <= last.getDate(); d++) {
      days.push(new Date(base.getFullYear(), base.getMonth(), d));
    }
    while (days.length % 7 !== 0) {
      const tail = days[days.length - 1];
      days.push(new Date(tail.getFullYear(), tail.getMonth(), tail.getDate() + 1));
    }
    return days;
  }, [cursorMonth]);

  const byDay = useMemo(() => {
    const map: Record<string, PlannedPostItem[]> = {};
    (plan?.posts || []).forEach((p) => {
      const key = ymd(new Date(p.scheduled_time));
      map[key] = map[key] || [];
      map[key].push(p);
    });
    Object.keys(map).forEach((k) => map[k].sort((a, b) => +new Date(a.scheduled_time) - +new Date(b.scheduled_time)));
    return map;
  }, [plan?.posts]);

  const name = 
    (typeof plan?.generated === 'object' && plan.generated !== null && 'campaign_name' in plan.generated)
      ? String(plan.generated.campaign_name)
      : "Campaign Plan";

  return (
    <Layout
      breadcrumbItems={[
        { label: "Dashboard", href: "/dashboard" },
        { label: "Campaign Planner", href: "/dashboard/campaign-planner" },
        { label: name },
      ]}
    >
      <div className="space-y-6 px-6 pt-6 pb-24">
        <Reveal variant="fadeInUp">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent flex items-center gap-3">
                <CalendarDays className="w-8 h-8 text-primary shadow-[0_0_20px_rgba(0,224,208,0.2)]" />
                {name}
              </h1>
              <div className="space-y-1">
                <p className="text-xs font-mono text-muted-foreground/70 uppercase tracking-widest flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  Brand-driven calendar
                </p>
                <p className="text-[11px] font-mono text-muted-foreground/60 leading-relaxed">
                  This calendar is generated from Brand DNA. Trend-driven opportunities live in{" "}
                  <Link to="/dashboard/trends" className="underline underline-offset-4">
                    Trend Arbitrage
                  </Link>{" "}
                  <TrendingUp className="inline w-3 h-3 ml-1" />.
                </p>
              </div>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                className="bg-foreground/5 border-border/50 hover:bg-foreground/10 transition-colors"
                onClick={() => setCursorMonth(addMonths(cursorMonth, -1))}
                disabled={!canPrev}
              >
                <ChevronLeft className="w-4 h-4 mr-2" /> Prev
              </Button>
              <Button
                variant="outline"
                className="bg-foreground/5 border-border/50 hover:bg-foreground/10 transition-colors"
                onClick={() => setCursorMonth(addMonths(cursorMonth, 1))}
                disabled={!canNext}
              >
                Next <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
              <Button
                variant="outline"
                size="icon"
                className="bg-foreground/5 border-border/50 hover:bg-foreground/10 transition-colors"
                onClick={fetchPlan}
                disabled={loading}
                title="Refresh Page"
              >
                <RefreshCw className={`w-4 h-4 shadow-[0_0_10px_rgba(255,255,255,0.1)] ${loading ? "animate-spin" : ""}`} />
              </Button>
            </div>
          </div>
        </Reveal>

        <Reveal variant="fadeInUp" delay={0.1}>
          <Card className="p-4 bg-card/40 border-border/50">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest">
                {cursorMonth.toLocaleString(undefined, { month: "long", year: "numeric" })} · Timezone: {plan?.timezone || "UTC"}
              </div>
              {allowedMonths.length > 1 && (
                <div className="w-full md:w-[260px]">
                  <Select
                    value={cursorKey}
                    onValueChange={(v) => {
                      const [yy, mm] = v.split("-").map((x) => Number(x));
                      if (!yy || !mm) return;
                      setCursorMonth(new Date(yy, mm - 1, 1));
                    }}
                  >
                    <SelectTrigger className="bg-foreground/5 border-border/50 h-9">
                      <SelectValue placeholder="Select month" />
                    </SelectTrigger>
                    <SelectContent>
                      {allowedMonths.map((m) => {
                        const k = `${m.getFullYear()}-${String(m.getMonth() + 1).padStart(2, "0")}`;
                        return (
                          <SelectItem key={k} value={k}>
                            {m.toLocaleString(undefined, { month: "long", year: "numeric" })}
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </Card>
        </Reveal>

        <div className="grid grid-cols-7 gap-2">
          {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((d) => (
            <div key={d} className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-widest px-1">
              {d}
            </div>
          ))}

          {monthDays.map((d) => {
            const inMonth = d.getMonth() === cursorMonth.getMonth();
            const items = byDay[ymd(d)] || [];
            return (
              <Card
                key={d.toISOString()}
                className={`min-h-[110px] p-2 bg-card/30 border-border/50 ${inMonth ? "" : "opacity-50"}`}
              >
                <div className="flex items-center justify-between">
                  <div className="text-[10px] font-mono text-muted-foreground/70">{d.getDate()}</div>
                  {items.length > 0 && (
                    <div className="text-[9px] font-mono text-primary/80 uppercase tracking-widest">{items.length} posts</div>
                  )}
                </div>
                <div className="mt-2 space-y-1">
                  {items.slice(0, 3).map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setSelected(p)}
                      className="w-full text-left text-[11px] font-mono text-foreground/90 bg-foreground/5 hover:bg-foreground/10 border border-border/50 rounded-md px-2 py-1 line-clamp-2"
                      title={p.title}
                    >
                      {p.title}
                    </button>
                  ))}
                  {items.length > 3 && (
                    <div className="text-[10px] font-mono text-muted-foreground/60">+{items.length - 3} more</div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      <PlannedPostDrawer
        open={!!selected}
        item={selected}
        timezone={plan?.timezone || "UTC"}
        onOpenChange={(v) => {
          if (!v) setSelected(null);
        }}
        onUpdated={fetchPlan}
      />
    </Layout>
  );
}

