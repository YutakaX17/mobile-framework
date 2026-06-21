export type AdminAuthUser = {
  displayName: string;
  email: string;
  roles: string[];
  tenant?: AdminAuthTenant;
  tenants?: AdminAuthTenant[];
  username?: string;
};

export type AdminAuthTenant = {
  id: string;
  name: string;
  slug: string;
  status: string;
};

export type AuthState =
  | {
      error: undefined;
      status: "loading";
      user: undefined;
    }
  | {
      error: undefined;
      status: "anonymous";
      user: undefined;
    }
  | {
      error: undefined;
      status: "authenticated";
      user: AdminAuthUser;
    }
  | {
      error: string;
      status: "error";
      user: undefined;
    };

export type AuthAction =
  | {
      type: "load";
    }
  | {
      type: "sign-in";
      user: AdminAuthUser;
    }
  | {
      type: "sign-out";
    }
  | {
      message: string;
      type: "error";
    };

export const anonymousAuthState: AuthState = {
  error: undefined,
  status: "anonymous",
  user: undefined
};

export const loadingAuthState: AuthState = {
  error: undefined,
  status: "loading",
  user: undefined
};

export const defaultAdminUser: AdminAuthUser = {
  displayName: "Admin Builder",
  email: "admin@example.test",
  roles: ["platform-admin"]
};

export function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "load":
      return loadingAuthState;
    case "sign-in":
      return {
        error: undefined,
        status: "authenticated",
        user: action.user
      };
    case "sign-out":
      return anonymousAuthState;
    case "error":
      return {
        error: action.message,
        status: "error",
        user: undefined
      };
    default:
      return state;
  }
}

export function createDevelopmentAuthUser(email: string): AdminAuthUser {
  const normalizedEmail = email.trim() || defaultAdminUser.email;
  const displayName = normalizedEmail.split("@")[0]?.replace(/[._-]+/g, " ") || defaultAdminUser.displayName;

  return {
    ...defaultAdminUser,
    displayName: toTitleCase(displayName),
    email: normalizedEmail
  };
}

export function getLoginRedirectPath(pathname: string, search = ""): string {
  const returnTo = `${pathname}${search}`;
  return `/login?returnTo=${encodeURIComponent(returnTo)}`;
}

export function getPostLoginPath(returnTo: string | null | undefined): string {
  if (!returnTo || !returnTo.startsWith("/") || returnTo.startsWith("//") || returnTo.startsWith("/login")) {
    return "/dashboard";
  }

  return returnTo;
}

function toTitleCase(value: string): string {
  return value
    .split(" ")
    .filter(Boolean)
    .map((part) => `${part.charAt(0).toUpperCase()}${part.slice(1)}`)
    .join(" ");
}
