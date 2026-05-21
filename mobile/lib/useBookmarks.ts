import AsyncStorage from "@react-native-async-storage/async-storage";
import { useState, useEffect, useCallback } from "react";
import type { CourseSummary } from "@/types";

const BOOKMARKS_KEY = "ocw:bookmarks";

async function loadBookmarks(): Promise<CourseSummary[]> {
  try {
    const raw = await AsyncStorage.getItem(BOOKMARKS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

async function saveBookmarks(items: CourseSummary[]): Promise<void> {
  await AsyncStorage.setItem(BOOKMARKS_KEY, JSON.stringify(items));
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<CourseSummary[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    loadBookmarks().then((items) => {
      setBookmarks(items);
      setLoaded(true);
    });
  }, []);

  const isBookmarked = useCallback(
    (id: string) => bookmarks.some((c) => c.id === id),
    [bookmarks]
  );

  const toggle = useCallback(
    async (course: CourseSummary) => {
      const exists = bookmarks.some((c) => c.id === course.id);
      const updated = exists
        ? bookmarks.filter((c) => c.id !== course.id)
        : [course, ...bookmarks];
      setBookmarks(updated);
      await saveBookmarks(updated);
    },
    [bookmarks]
  );

  return { bookmarks, isBookmarked, toggle, loaded };
}
