import { useAsyncData } from "../../lib/hooks";
import { getEntityFeed, getSourceDetail } from "./api";

export function useEntityFeed() {
  return useAsyncData(getEntityFeed, []);
}

export function useSourceDetail(slug: string | null) {
  return useAsyncData(async () => {
    if (!slug) return null;
    return getSourceDetail(slug);
  }, [slug]);
}
