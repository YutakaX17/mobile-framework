import { describe, expect, it } from "vitest";

import {
  anonymousAuthState,
  authReducer,
  createDevelopmentAuthUser,
  getLoginRedirectPath,
  getPostLoginPath
} from "./authSession";

describe("auth session", () => {
  it("creates a development user from an email address", () => {
    expect(createDevelopmentAuthUser("jane.admin@example.test")).toMatchObject({
      displayName: "Jane Admin",
      email: "jane.admin@example.test",
      roles: ["platform-admin"]
    });
  });

  it("transitions between anonymous and authenticated states", () => {
    expect(authReducer(anonymousAuthState, { type: "load" }).status).toBe("loading");

    const signedIn = authReducer(anonymousAuthState, {
      type: "sign-in",
      user: createDevelopmentAuthUser("builder@example.test")
    });

    expect(signedIn.status).toBe("authenticated");
    if (signedIn.status === "authenticated") {
      expect(signedIn.user.email).toBe("builder@example.test");
    }
    expect(authReducer(signedIn, { type: "sign-out" })).toEqual(anonymousAuthState);

    const errored = authReducer(anonymousAuthState, { type: "error", message: "Failed" });
    expect(errored).toMatchObject({ error: "Failed", status: "error", user: undefined });
  });

  it("builds login redirects for protected routes", () => {
    expect(getLoginRedirectPath("/forms", "?tab=fields")).toBe("/login?returnTo=%2Fforms%3Ftab%3Dfields");
  });

  it("accepts only local post-login return paths", () => {
    expect(getPostLoginPath("/forms?tab=fields")).toBe("/forms?tab=fields");
    expect(getPostLoginPath("https://example.test/forms")).toBe("/dashboard");
    expect(getPostLoginPath("//example.test/forms")).toBe("/dashboard");
    expect(getPostLoginPath("/login")).toBe("/dashboard");
    expect(getPostLoginPath(undefined)).toBe("/dashboard");
  });
});
