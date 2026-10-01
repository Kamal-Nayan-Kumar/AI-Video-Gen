import { useEffect, useState } from "react";
import { getHealth } from "../utils/api";

/** Fetch the backend's capability matrix on mount. */
export function useCapabilities() {
  const [state, setState] = useState({ loading: true, mode: null, online: false, capabilities: null });

  useEffect(() => {
    let cancelled = false;

    getHealth()
      .then((data) => {
        if (cancelled) return;
        setState({
          loading: false,
          mode: data.capabilities?.mode ?? "demo",
          online: true,
          capabilities: data.capabilities ?? {},
        });
      })
      .catch(() => {
        if (!cancelled) setState({ loading: false, mode: null, online: false, capabilities: null });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}