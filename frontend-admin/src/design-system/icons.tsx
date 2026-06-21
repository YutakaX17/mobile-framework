import {
  AppWindow,
  CheckCircle2,
  Gauge,
  ListChecks,
  LogIn,
  LogOut,
  Palette,
  Puzzle,
  Rocket,
  Send,
  Settings2,
  type LucideIcon,
  type LucideProps
} from "lucide-react";

export const iconRegistry = {
  apps: AppWindow,
  dashboard: Gauge,
  deployments: Rocket,
  forms: CheckCircle2,
  login: LogIn,
  modules: Puzzle,
  publish: Send,
  setup: ListChecks,
  signOut: LogOut,
  themes: Palette,
  validate: CheckCircle2,
  workflows: Settings2
} satisfies Record<string, LucideIcon>;

export type IconName = keyof typeof iconRegistry;

export type AdminIconProps = Omit<LucideProps, "aria-label"> & {
  decorative?: boolean;
  label?: string;
  name: IconName;
};

export function getAdminIcon(name: IconName): LucideIcon {
  return iconRegistry[name];
}

export function listAdminIconNames(): IconName[] {
  return Object.keys(iconRegistry).sort() as IconName[];
}

export function AdminIcon({ className = "icon", decorative = true, label, name, size = 18, ...props }: AdminIconProps) {
  const Icon = getAdminIcon(name);

  return (
    <Icon
      aria-hidden={decorative ? true : undefined}
      aria-label={decorative ? undefined : label}
      className={className}
      focusable="false"
      size={size}
      {...props}
    />
  );
}
