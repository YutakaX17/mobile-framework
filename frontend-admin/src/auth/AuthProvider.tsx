import { createContext, type PropsWithChildren, useContext, useEffect, useMemo, useReducer } from "react";

import { authApi, type AuthApi } from "./authApi";
import { anonymousAuthState, authReducer, type AdminAuthUser, type AuthState } from "./authSession";

type AuthContextValue = {
  signIn(username: string, password: string): Promise<void>;
  signOut(): Promise<void>;
  state: AuthState;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children, client = authApi }: PropsWithChildren<{ client?: AuthApi }>) {
  const [state, dispatch] = useReducer(authReducer, anonymousAuthState);

  useEffect(() => {
    let isActive = true;
    dispatch({ type: "load" });
    client
      .currentSession()
      .then((user) => {
        if (isActive) {
          dispatch({ type: "sign-in", user });
        }
      })
      .catch(() => {
        if (isActive) {
          dispatch({ type: "sign-out" });
        }
      });
    return () => {
      isActive = false;
    };
  }, [client]);

  const value = useMemo<AuthContextValue>(
    () => ({
      async signIn(username: string, password: string) {
        dispatch({ type: "load" });
        try {
          const user = await client.login({ password, username });
          dispatch({ type: "sign-in", user });
        } catch {
          dispatch({ type: "error", message: "Sign in failed. Check your username and password." });
          throw new Error("Sign in failed.");
        }
      },
      async signOut() {
        await client.logout();
        dispatch({ type: "sign-out" });
      },
      state
    }),
    [client, state]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthSession(): AuthContextValue {
  const value = useContext(AuthContext);

  if (!value) {
    throw new Error("useAuthSession must be used inside AuthProvider.");
  }

  return value;
}

export function useAuthenticatedUser(): AdminAuthUser | undefined {
  return useAuthSession().state.user;
}
