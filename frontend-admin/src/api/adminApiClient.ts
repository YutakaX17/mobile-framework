export const DEFAULT_ADMIN_API_BASE_URL = "/api";

export type ApiQueryValue = string | number | boolean | null | undefined;

export type ApiRequestOptions<TBody = unknown> = {
  body?: TBody;
  headers?: HeadersInit;
  method?: string;
  query?: Record<string, ApiQueryValue>;
  signal?: AbortSignal;
};

export type ApiResult<TData> = {
  data: TData;
  headers: Headers;
  status: number;
  url: string;
};

export type AdminApiClient = {
  delete<TData>(path: string, options?: Omit<ApiRequestOptions, "body" | "method">): Promise<ApiResult<TData>>;
  get<TData>(path: string, options?: Omit<ApiRequestOptions, "body" | "method">): Promise<ApiResult<TData>>;
  patch<TData, TBody = unknown>(path: string, body: TBody, options?: Omit<ApiRequestOptions<TBody>, "body" | "method">): Promise<ApiResult<TData>>;
  post<TData, TBody = unknown>(path: string, body: TBody, options?: Omit<ApiRequestOptions<TBody>, "body" | "method">): Promise<ApiResult<TData>>;
  put<TData, TBody = unknown>(path: string, body: TBody, options?: Omit<ApiRequestOptions<TBody>, "body" | "method">): Promise<ApiResult<TData>>;
  request<TData, TBody = unknown>(path: string, options?: ApiRequestOptions<TBody>): Promise<ApiResult<TData>>;
};

export type AdminApiClientConfig = {
  baseUrl?: string;
  fetcher?: typeof fetch;
  headers?: HeadersInit;
};

type AdminApiEnv = {
  VITE_ADMIN_API_BASE_URL?: string;
};

export class ApiClientError extends Error {
  readonly body: unknown;
  readonly status: number;
  readonly statusText: string;
  readonly url: string;

  constructor(response: Response, body: unknown) {
    super(`API request failed with ${response.status} ${response.statusText}`);
    this.name = "ApiClientError";
    this.body = body;
    this.status = response.status;
    this.statusText = response.statusText;
    this.url = response.url;
  }
}

export function resolveAdminApiBaseUrl(env: AdminApiEnv = import.meta.env as AdminApiEnv): string {
  const configured = env.VITE_ADMIN_API_BASE_URL?.trim();
  return normalizeBaseUrl(configured || DEFAULT_ADMIN_API_BASE_URL);
}

export function createAdminApiClient(config: AdminApiClientConfig = {}): AdminApiClient {
  const baseUrl = normalizeBaseUrl(config.baseUrl ?? resolveAdminApiBaseUrl());
  const fetcher = config.fetcher ?? fetch;
  const defaultHeaders = new Headers(config.headers);

  async function request<TData, TBody = unknown>(
    path: string,
    options: ApiRequestOptions<TBody> = {}
  ): Promise<ApiResult<TData>> {
    const headers = mergeHeaders(defaultHeaders, options.headers);
    const init: RequestInit = {
      headers,
      method: options.method ?? "GET",
      signal: options.signal
    };

    if (options.body !== undefined) {
      if (!headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }
      init.body = serializeBody(options.body);
    }

    if (!headers.has("Accept")) {
      headers.set("Accept", "application/json");
    }

    const url = buildApiUrl(baseUrl, path, options.query);
    const response = await fetcher(url, init);
    const data = await parseResponseBody(response);

    if (!response.ok) {
      throw new ApiClientError(response, data);
    }

    return {
      data: data as TData,
      headers: response.headers,
      status: response.status,
      url
    };
  }

  return {
    delete: (path, options) => request(path, { ...options, method: "DELETE" }),
    get: (path, options) => request(path, { ...options, method: "GET" }),
    patch: (path, body, options) => request(path, { ...options, body, method: "PATCH" }),
    post: (path, body, options) => request(path, { ...options, body, method: "POST" }),
    put: (path, body, options) => request(path, { ...options, body, method: "PUT" }),
    request
  };
}

export const adminApiClient = createAdminApiClient();

export function buildApiUrl(baseUrl: string, path: string, query?: Record<string, ApiQueryValue>): string {
  const normalizedBase = normalizeBaseUrl(baseUrl);
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${normalizedBase === "/" ? "" : normalizedBase}${normalizedPath}`;
  const params = new URLSearchParams();

  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) {
      params.set(key, String(value));
    }
  }

  const queryString = params.toString();
  return queryString ? `${url}?${queryString}` : url;
}

function normalizeBaseUrl(baseUrl: string): string {
  const trimmed = baseUrl.trim();
  if (!trimmed) {
    return DEFAULT_ADMIN_API_BASE_URL;
  }
  return trimmed === "/" ? "/" : trimmed.replace(/\/+$/, "");
}

function mergeHeaders(baseHeaders: Headers, requestHeaders: HeadersInit | undefined): Headers {
  const headers = new Headers(baseHeaders);
  new Headers(requestHeaders).forEach((value, key) => headers.set(key, value));
  return headers;
}

function serializeBody(body: unknown): BodyInit {
  if (
    typeof body === "string" ||
    body instanceof Blob ||
    body instanceof FormData ||
    body instanceof URLSearchParams ||
    body instanceof ArrayBuffer
  ) {
    return body;
  }

  return JSON.stringify(body);
}

async function parseResponseBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }

  const contentType = response.headers.get("Content-Type") ?? "";
  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
}
