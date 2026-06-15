import { createContext, type PropsWithChildren, useContext, useMemo, useReducer } from "react";

import {
  anonymousAuthState,
  authReducer,
  createDevelopmentAuthUser,
  type AdminAuthUser,
  type AuthState
} from "./authSession";

type AuthContextValue = {
  signIn(email: string): void;
  signOut(): void;
  state: AuthState;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: PropsWithChildren) {
  const [state, dispatch] = useReducer(authReducer, anonymousAuthState);
  const value = useMemo<AuthContextValue>(
    () => ({
      signIn(email: string) {
        dispatch({ type: "sign-in", user: createDevelopmentAuthUser(email) });
      },
      signOut() {
        dispatch({ type: "sign-out" });
      },
      state
    }),
    [state]
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
