import type { AdminRoute } from "../routes";

type UnauthorizedViewProps = {
  route: AdminRoute;
};

export function UnauthorizedView({ route }: UnauthorizedViewProps) {
  return (
    <section className="empty-state" aria-labelledby={`${route.label}-unauthorized-title`}>
      <p className="eyebrow">Permission required</p>
      <h2 id={`${route.label}-unauthorized-title`}>{route.label} is protected</h2>
      <p>Your current role does not include the capabilities required for this workspace.</p>
    </section>
  );
}
