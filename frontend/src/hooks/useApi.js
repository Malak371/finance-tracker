import { useCallback, useEffect, useState } from "react";
import api from "../api/api";

/**
 * Fetch `path` (with optional query `params`) and re-fetch whenever they change.
 *
 * Returns { data, error, loading, reload }. While re-fetching, the previous data is kept
 * so the UI doesn't flash back to a spinner; `loading` is only true until the first response.
 */
export function useApi(path, params) {
  const requestKey = JSON.stringify([path, params ?? null]);
  const [version, setVersion] = useState(0);
  const [result, setResult] = useState({ key: null, data: undefined, error: null });

  useEffect(() => {
    let cancelled = false;
    const [requestPath, requestParams] = JSON.parse(requestKey);
    const key = `${requestKey}#${version}`;
    api.get(requestPath, { params: requestParams ?? undefined }).then(
      (response) => !cancelled && setResult({ key, data: response.data, error: null }),
      (error) => !cancelled && setResult((prev) => ({ key, data: prev.data, error })),
    );
    return () => {
      cancelled = true;
    };
  }, [requestKey, version]);

  const reload = useCallback(() => setVersion((v) => v + 1), []);

  return {
    data: result.data,
    error: result.error,
    loading: result.key === null,
    refreshing: result.key !== `${requestKey}#${version}`,
    reload,
  };
}
