import raampIcon from "@/assets/raamp-icon-transparent.png";
import { cn } from "@/lib/utils";

type BrandMarkVariant = "navbar" | "drawer" | "sidebar";

export function BrandMark({
  variant = "navbar",
  size = 40,
  className,
}: {
  variant?: BrandMarkVariant;
  size?: number;
  className?: string;
}) {
  const base =
    "relative grid place-items-center overflow-hidden rounded-2xl border shadow-[0_10px_30px_rgba(0,0,0,0.28)]";
  const variantClass = (() => {
    // Strong-brand default: solid teal badge (looks like a real app mark).
    if (variant === "sidebar") return "bg-primary border-primary/50";
    if (variant === "drawer") return "bg-primary border-primary/50";
    return "bg-primary border-primary/50";
  })();

  return (
    <div
      className={cn(base, variantClass, className)}
      style={{ width: size, height: size }}
      aria-label="RAAMP"
    >
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-35 bg-[radial-gradient(60%_60%_at_25%_25%,rgba(255,255,255,0.55)_0%,rgba(255,255,255,0)_60%)]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 ring-1 ring-inset ring-white/20"
      />
      <img
        src={raampIcon}
        alt="RAAMP"
        className="relative z-10 w-[72%] h-[72%] object-contain drop-shadow-[0_8px_18px_rgba(0,0,0,0.35)]"
        draggable={false}
      />
    </div>
  );
}

