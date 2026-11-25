// Adapted from shadcn/ui (MIT). See THIRD_PARTY_NOTICES.md.
import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "radix-ui";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-violet-400 disabled:pointer-events-none disabled:opacity-40 [&_svg]:size-4",
  { variants: {
    variant: { default: "bg-violet-500 text-white hover:bg-violet-400", outline: "border border-white/15 bg-white/3 hover:bg-white/8", ghost: "hover:bg-white/6 text-zinc-300" },
    size: { default: "h-10 px-4", sm: "h-8 px-3", icon: "size-10" },
  }, defaultVariants: { variant: "default", size: "default" } },
);

function Button({ className, variant, size, asChild = false, ...props }:
  React.ComponentProps<"button"> & VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot.Root : "button";
  return <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />;
}
export { Button, buttonVariants };
