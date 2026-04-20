import raampIcon from "@/assets/raamp-icon-transparent.bak.png";
import raampLogoTransparent from "@/assets/raamp-logo-v6-transparent.png";
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
  const isBadge = variant === "sidebar" || variant === "drawer";
  const base = isBadge
    ? "relative grid place-items-center overflow-hidden rounded-2xl border shadow-[0_10px_30px_rgba(0,0,0,0.28)]"
    : "relative grid place-items-center overflow-hidden";

  const variantClass = isBadge ? "bg-primary border-primary/50" : "";

  const src = isBadge ? raampIcon : raampLogoTransparent;
  const imgClass = isBadge
    ? "relative z-10 w-[72%] h-[72%] object-contain drop-shadow-[0_8px_18px_rgba(0,0,0,0.35)]"
    : "relative z-10 w-full h-full object-contain";

  return (
    <div
      className={cn(base, variantClass, className)}
      style={{ width: size, height: size }}
      aria-label="RAAMP"
    >
      {isBadge && (
        <>
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-35 bg-[radial-gradient(60%_60%_at_25%_25%,rgba(255,255,255,0.55)_0%,rgba(255,255,255,0)_60%)]"
          />
          <div
            aria-hidden="true"
            className="absolute inset-0 ring-1 ring-inset ring-white/20"
          />
        </>
      )}
      <img
        src={src}
        alt="RAAMP"
        className={imgClass}
        draggable={false}
      />
    </div>
  );
}

