import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchAppDetail, getAppPayload, publishAppRevision, updateAppDraft, type AppDetail } from "../../api/appApi";
import {
  fetchFormDetail,
  getFormPayload,
  publishFormRevision,
  updateFormDraft,
  type FormDetail
} from "../../api/formApi";
import {
  activateDeploymentPackage,
  activePackage,
  compileDeploymentPackage,
  fetchActiveManifest,
  fetchDeploymentPackages,
  fetchModuleStatuses,
  moduleCompatibilityCount,
  nextPatchVersion,
  packageIdFor,
  type DeploymentPackageSummary,
  type ModuleStatus
} from "../../api/practicalMvpApi";
import {
  fetchThemeDetail,
  getThemePayload,
  publishThemeRevision,
  updateThemeDraft,
  type ThemeDetail
} from "../../api/themeApi";
import { useAuthenticatedUser } from "../../auth/AuthProvider";

const FIELD_OPS_THEME_ID = "field_ops";
const FIELD_OPS_FORM_ID = "patient_intake";
const FIELD_OPS_APP_ID = "field_ops_app";

type MvpState = {
  app?: AppDetail;
  error?: string;
  form?: FormDetail;
  manifest?: DeploymentPackageSummary;
  modules: ModuleStatus[];
  packages: DeploymentPackageSummary[];
  status: "error" | "loaded" | "loading" | "publishing";
  theme?: ThemeDetail;
};

const initialMvpState: MvpState = {
  modules: [],
  packages: [],
  status: "loading"
};

export function SetupWizardView() {
  const user = useAuthenticatedUser();
  const tenant = user?.tenant?.slug ?? "demo";
  const [state, setState] = useState<MvpState>(initialMvpState);

  const loadMvpState = useCallback(async () => {
    setState((current) => ({ ...current, error: undefined, status: "loading" }));
    try {
      const [modules, theme, form, app, packages, manifest] = await Promise.all([
        fetchModuleStatuses(undefined, tenant),
        fetchThemeDetail(FIELD_OPS_THEME_ID, undefined, tenant),
        fetchFormDetail(FIELD_OPS_FORM_ID, undefined, tenant),
        fetchAppDetail(FIELD_OPS_APP_ID, undefined, tenant),
        fetchDeploymentPackages(undefined, tenant),
        fetchActiveManifest(FIELD_OPS_APP_ID, undefined, tenant)
      ]);
      setState({ app, form, manifest, modules, packages, status: "loaded", theme });
    } catch (error) {
      setState({
        ...initialMvpState,
        error: readableError(error),
        status: "error"
      });
    }
  }, [tenant]);

  useEffect(() => {
    void loadMvpState();
  }, [loadMvpState]);

  const publishDemoPackage = useCallback(async () => {
    if (!state.theme || !state.form || !state.app) {
      return;
    }

    setState((current) => ({ ...current, error: undefined, status: "publishing" }));
    try {
      const themePayload = getThemePayload(state.theme);
      const formPayload = getFormPayload(state.form);
      const appPayload = getAppPayload(state.app);

      if (!themePayload || !formPayload || !appPayload) {
        throw new Error("Seeded Field Ops builder payloads are incomplete.");
      }

      const nextVersion = nextPatchVersion(appPayload.version);
      const themeUpdate = await updateThemeDraft(
        FIELD_OPS_THEME_ID,
        {
          ...themePayload,
          accessibility: {
            ...themePayload.accessibility,
            validated: true
          },
          version: nextVersion
        },
        undefined,
        tenant
      );
      const theme = await publishThemeRevision(
        FIELD_OPS_THEME_ID,
        themeUpdate.draft_revision.revision,
        undefined,
        tenant
      );

      const formUpdate = await updateFormDraft(
        FIELD_OPS_FORM_ID,
        {
          ...formPayload,
          description: "Practical MVP patient intake form.",
          version: nextVersion
        },
        undefined,
        tenant
      );
      const form = await publishFormRevision(FIELD_OPS_FORM_ID, formUpdate.draft_revision.revision, undefined, tenant);

      const appUpdate = await updateAppDraft(
        FIELD_OPS_APP_ID,
        {
          ...appPayload,
          description: "Practical MVP Field Ops app.",
          version: nextVersion
        },
        undefined,
        tenant
      );
      const app = await publishAppRevision(FIELD_OPS_APP_ID, appUpdate.draft_revision.revision, undefined, tenant);

      const packageId = packageIdFor(FIELD_OPS_APP_ID, nextVersion);
      const compiled = await compileDeploymentPackage(
        {
          app_id: FIELD_OPS_APP_ID,
          channel: "dev",
          form_ids: [FIELD_OPS_FORM_ID],
          package_id: packageId,
          runtime_max_version: "0.1.0",
          runtime_min_version: "0.1.0",
          theme_id: FIELD_OPS_THEME_ID
        },
        undefined,
        tenant
      );
      const activated = await activateDeploymentPackage(compiled.package_id, undefined, tenant);
      const [modules, packages, manifest] = await Promise.all([
        fetchModuleStatuses(undefined, tenant),
        fetchDeploymentPackages(undefined, tenant),
        fetchActiveManifest(FIELD_OPS_APP_ID, undefined, tenant)
      ]);

      setState({
        app,
        form,
        manifest: manifest ?? activated,
        modules,
        packages,
        status: "loaded",
        theme
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        error: readableError(error),
        status: "error"
      }));
    }
  }, [state.app, state.form, state.theme, tenant]);

  const fieldOps = state.modules.find((module) => module.module_id === "field_ops");
  const currentPackage = state.manifest ?? activePackage(state.packages);
  const appPayload = state.app ? getAppPayload(state.app) : undefined;
  const formPayload = state.form ? getFormPayload(state.form) : undefined;

  return (
    <section className="setup-workflow-view" aria-labelledby="setup-title">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Practical MVP</p>
          <h2 id="setup-title">Field Ops setup</h2>
        </div>
        <div className="topbar-actions">
          <button type="button" onClick={loadMvpState}>
            Refresh
          </button>
          <button
            className="primary-action"
            disabled={state.status === "publishing" || state.status === "loading"}
            type="button"
            onClick={publishDemoPackage}
          >
            {state.status === "publishing" ? "Publishing" : "Publish dev package"}
          </button>
        </div>
      </header>

      {state.error ? (
        <section className="empty-state" role="alert">
          <h3>Setup flow could not continue</h3>
          <p>{state.error}</p>
        </section>
      ) : null}

      <section className="wizard-grid" aria-label="MVP setup steps">
        <WizardStep
          detail={user?.tenant ? `${user.tenant.name} (${user.tenant.slug})` : "Tenant context is loading"}
          status={user?.tenant ? "ready" : "blocked"}
          title="Tenant"
        />
        <WizardStep
          detail={fieldOps ? `${fieldOps.name} ${fieldOps.version}` : "Field Ops is not registered"}
          status={fieldOps?.status === "enabled" ? "ready" : "blocked"}
          title="Plugin"
        />
        <WizardStep
          detail={fieldOps?.templates?.forms?.length ? "Template form available" : "No form template found"}
          status={fieldOps?.templates?.forms?.length ? "ready" : "blocked"}
          title="Template"
        />
        <WizardStep
          detail={state.theme?.current_revision?.version ?? "Theme not loaded"}
          status={state.theme?.current_revision?.status === "published" ? "ready" : "draft"}
          title="Theme"
        />
        <WizardStep
          detail={formPayload ? `${formPayload.fields.length} fields` : "Form not loaded"}
          status={state.form?.current_revision?.status === "published" ? "ready" : "draft"}
          title="Form"
        />
        <WizardStep
          detail={appPayload ? `${appPayload.screens.length} screen, ${appPayload.navigation.length} navigation item` : "App not loaded"}
          status={state.app?.current_revision?.status === "published" ? "ready" : "draft"}
          title="App"
        />
        <WizardStep
          detail={appPayload?.screens[0]?.display?.title ?? appPayload?.screens[0]?.name ?? "Preview not ready"}
          status={appPayload ? "ready" : "blocked"}
          title="Preview"
        />
        <WizardStep
          detail={`${moduleCompatibilityCount(state.modules)}/${state.modules.length} modules compatible`}
          status={state.modules.length > 0 && moduleCompatibilityCount(state.modules) === state.modules.length ? "ready" : "blocked"}
          title="Validate"
        />
        <WizardStep
          detail={currentPackage ? `${currentPackage.package_id} on ${currentPackage.channel}` : "No active dev package"}
          status={currentPackage?.status === "active" ? "ready" : "draft"}
          title="Publish"
        />
      </section>

      <section className="mobile-instructions" aria-label="Mobile connection">
        <h3>Mobile connection</h3>
        <dl className="property-list">
          <div>
            <dt>Tenant</dt>
            <dd>{tenant}</dd>
          </div>
          <div>
            <dt>Manifest</dt>
            <dd>/api/mobile/packages/manifest/?tenant={tenant}&amp;app_id={FIELD_OPS_APP_ID}&amp;channel=dev</dd>
          </div>
          <div>
            <dt>Package</dt>
            <dd>{currentPackage ? `/api/mobile/packages/${currentPackage.package_id}/download/?tenant=${tenant}` : "not active"}</dd>
          </div>
          <div>
            <dt>Sync</dt>
            <dd>Pending M5 sync backend</dd>
          </div>
        </dl>
      </section>
    </section>
  );
}

export function ModuleStatusView() {
  const tenant = useAuthenticatedUser()?.tenant?.slug ?? "demo";
  const [state, setState] = useState<{ error?: string; modules: ModuleStatus[]; status: "error" | "loaded" | "loading" }>({
    modules: [],
    status: "loading"
  });

  useEffect(() => {
    fetchModuleStatuses(undefined, tenant)
      .then((modules) => setState({ modules, status: "loaded" }))
      .catch((error) => setState({ error: readableError(error), modules: [], status: "error" }));
  }, [tenant]);

  return (
    <section className="module-status-view" aria-labelledby="module-status-title">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Plugin status</p>
          <h2 id="module-status-title">Modules</h2>
        </div>
        <span className="queue-count">{state.modules.length} registered</span>
      </header>
      {state.error ? <p className="error-message">{state.error}</p> : null}
      <section className="module-grid" aria-label="Registered modules">
        {state.modules.map((module) => (
          <article className="module-card" key={`${module.module_id}-${module.version}`}>
            <div>
              <h3>{module.name}</h3>
              <p>{module.module_id}</p>
            </div>
            <span className={`status ${module.status === "enabled" ? "status-ready" : "status-draft"}`}>
              {module.status}
            </span>
            <dl className="property-list">
              <div>
                <dt>Version</dt>
                <dd>{module.version}</dd>
              </div>
              <div>
                <dt>Runtime</dt>
                <dd>
                  {module.runtime_min_version} - {module.runtime_max_version}
                </dd>
              </div>
              <div>
                <dt>Compatibility</dt>
                <dd>{module.compatibility.message}</dd>
              </div>
            </dl>
          </article>
        ))}
      </section>
    </section>
  );
}

export function PackageReleaseView() {
  const tenant = useAuthenticatedUser()?.tenant?.slug ?? "demo";
  const [state, setState] = useState<{
    error?: string;
    manifest?: DeploymentPackageSummary;
    packages: DeploymentPackageSummary[];
    status: "error" | "loaded" | "loading";
  }>({ packages: [], status: "loading" });

  useEffect(() => {
    Promise.all([
      fetchDeploymentPackages(undefined, tenant),
      fetchActiveManifest(FIELD_OPS_APP_ID, undefined, tenant)
    ])
      .then(([packages, manifest]) => setState({ manifest, packages, status: "loaded" }))
      .catch((error) => setState({ error: readableError(error), packages: [], status: "error" }));
  }, [tenant]);

  const currentPackage = state.manifest ?? activePackage(state.packages);

  return (
    <section className="package-release-view" aria-labelledby="package-release-title">
      <header className="section-heading">
        <div>
          <p className="eyebrow">Deployment manager</p>
          <h2 id="package-release-title">Dev package release</h2>
        </div>
        <span className="queue-count">{state.packages.length} packages</span>
      </header>
      {state.error ? <p className="error-message">{state.error}</p> : null}
      <section className="release-panel" aria-label="Active package">
        <h3>{currentPackage?.package_id ?? "No active package"}</h3>
        <dl className="property-list">
          <div>
            <dt>Channel</dt>
            <dd>{currentPackage?.channel ?? "dev"}</dd>
          </div>
          <div>
            <dt>App version</dt>
            <dd>{currentPackage?.app_version ?? "not published"}</dd>
          </div>
          <div>
            <dt>Hash</dt>
            <dd>{currentPackage?.hash ?? "not available"}</dd>
          </div>
          <div>
            <dt>Signature</dt>
            <dd>{currentPackage?.signature_status ?? (currentPackage?.signature ? "present" : "missing")}</dd>
          </div>
          <div>
            <dt>Runtime</dt>
            <dd>
              {currentPackage
                ? `${currentPackage.runtime_min_version} - ${currentPackage.runtime_max_version}`
                : "not available"}
            </dd>
          </div>
          <div>
            <dt>Published</dt>
            <dd>{currentPackage ? formatDate(currentPackage.updated_at) : "not available"}</dd>
          </div>
        </dl>
      </section>
    </section>
  );
}

type WizardStepProps = {
  detail: string;
  status: "blocked" | "draft" | "ready";
  title: string;
};

function WizardStep({ detail, status, title }: WizardStepProps) {
  return (
    <article className="wizard-step">
      <span className={`status status-${status}`}>{status}</span>
      <h3>{title}</h3>
      <p>{detail}</p>
    </article>
  );
}

function readableError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return "Unexpected error.";
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}
