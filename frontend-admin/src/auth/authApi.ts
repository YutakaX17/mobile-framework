import { adminApiClient, type AdminApiClient } from "../api/adminApiClient";
import type { AdminAuthTenant, AdminAuthUser } from "./authSession";

type BackendUser = {
  display_name: string;
  email: string;
  id: number;
  is_staff: boolean;
  username: string;
};

type BackendTenantAssignment = {
  permissions: string[];
  role: {
    name: string;
    slug: string;
  };
  tenant: AdminAuthTenant;
};

type CsrfResponse = {
  csrf_token: string;
};

type LoginResponse = {
  user: BackendUser;
};

type SessionResponse = {
  user: BackendUser;
};

type TenantsResponse = {
  tenants: BackendTenantAssignment[];
};

export type LoginCredentials = {
  password: string;
  username: string;
};

export type AuthApi = {
  currentSession(): Promise<AdminAuthUser>;
  login(credentials: LoginCredentials): Promise<AdminAuthUser>;
  logout(): Promise<void>;
};

export function createAuthApi(client: AdminApiClient = adminApiClient): AuthApi {
  async function buildUser(user: BackendUser): Promise<AdminAuthUser> {
    const tenants = await client.get<TenantsResponse>("/auth/tenants/");
    const assignments = tenants.data.tenants;

    return {
      displayName: user.display_name,
      email: user.email,
      roles: frontendRolesFromAssignments(assignments),
      tenant: assignments[0]?.tenant,
      tenants: assignments.map((assignment) => assignment.tenant),
      username: user.username
    };
  }

  return {
    async currentSession() {
      const response = await client.get<SessionResponse>("/auth/session/");
      return buildUser(response.data.user);
    },
    async login(credentials) {
      const csrf = await client.get<CsrfResponse>("/auth/csrf/");
      const response = await client.post<LoginResponse, LoginCredentials>("/auth/login/", credentials, {
        headers: {
          "X-CSRFToken": csrf.data.csrf_token
        }
      });
      return buildUser(response.data.user);
    },
    async logout() {
      const csrf = await client.get<CsrfResponse>("/auth/csrf/");
      await client.post<{ status: string }, Record<string, never>>(
        "/auth/logout/",
        {},
        {
          headers: {
            "X-CSRFToken": csrf.data.csrf_token
          }
        }
      );
    }
  };
}

export const authApi = createAuthApi();

export function frontendRolesFromAssignments(assignments: BackendTenantAssignment[]): string[] {
  const roleSlugs = new Set(assignments.map((assignment) => assignment.role.slug));
  const permissions = new Set(assignments.flatMap((assignment) => assignment.permissions));
  const roles = new Set<string>();

  if (roleSlugs.has("admin")) {
    roles.add("platform-admin");
  }
  if (
    roleSlugs.has("configurator") ||
    permissions.has("builder.theme.manage") ||
    permissions.has("builder.form.manage") ||
    permissions.has("builder.app.manage")
  ) {
    roles.add("builder");
  }
  if (permissions.has("builder.package.publish")) {
    roles.add("operator");
  }

  return [...roles].sort();
}
