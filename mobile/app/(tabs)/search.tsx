import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { fetchCourses } from "@/lib/api";

const LEVELS = ["All", "undergraduate", "graduate", "professional"] as const;
type Level = (typeof LEVELS)[number];

export default function SearchScreen() {
  const [q, setQ] = useState("");
  const [debouncedQ, setDebouncedQ] = useState("");
  const [level, setLevel] = useState<Level>("All");
  const router = useRouter();
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setDebouncedQ(q), 300);
    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [q]);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["search_mobile", debouncedQ, level],
    queryFn: () =>
      fetchCourses({
        q: debouncedQ,
        level: level === "All" ? undefined : level,
        page_size: 30,
        has_video_lectures: true,
      }),
    enabled: debouncedQ.trim().length >= 2,
  });

  const courses = data?.items ?? [];

  return (
    <View style={styles.container}>
      <TextInput
        style={styles.input}
        placeholder="Search courses..."
        placeholderTextColor="#666"
        value={q}
        onChangeText={setQ}
        returnKeyType="search"
        autoCapitalize="none"
        autoCorrect={false}
      />

      {/* Level filter chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.chips}
      >
        {LEVELS.map((l) => (
          <TouchableOpacity
            key={l}
            style={[styles.chip, level === l && styles.chipActive]}
            onPress={() => setLevel(l)}
          >
            <Text style={[styles.chipText, level === l && styles.chipTextActive]}>
              {l === "All" ? "All levels" : l.charAt(0).toUpperCase() + l.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#e50914" />
        </View>
      ) : isError ? (
        <View style={styles.center}>
          <Text style={styles.hint}>Something went wrong.</Text>
          <TouchableOpacity style={styles.retryBtn} onPress={() => refetch()}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : debouncedQ.trim().length < 2 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>Type at least 2 characters to search</Text>
        </View>
      ) : courses.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>No courses found for "{debouncedQ}"</Text>
        </View>
      ) : (
        <FlatList
          data={courses}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.result}
              onPress={() => router.push(`/course/${item.slug}`)}
            >
              <Image
                source={{
                  uri:
                    item.thumbnail_url ??
                    `https://i.ytimg.com/vi/${item.id}/default.jpg`,
                }}
                style={styles.thumb}
              />
              <View style={styles.resultText}>
                <Text style={styles.title} numberOfLines={2}>
                  {item.title}
                </Text>
                <Text style={styles.meta}>
                  {item.university_name} · {item.total_videos} lectures
                </Text>
                {item.level && (
                  <Text style={styles.level}>{item.level}</Text>
                )}
              </View>
            </TouchableOpacity>
          )}
          contentContainerStyle={{ paddingTop: 4, paddingBottom: 24 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  input: {
    margin: 12,
    marginBottom: 6,
    backgroundColor: "#222",
    borderWidth: 1,
    borderColor: "#333",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: "#fff",
    fontSize: 15,
  },
  chips: { paddingHorizontal: 12, paddingBottom: 10, gap: 8 },
  chip: {
    borderWidth: 1,
    borderColor: "#333",
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 5,
    backgroundColor: "#1a1a1a",
  },
  chipActive: { borderColor: "#e50914", backgroundColor: "#2a0a0a" },
  chipText: { color: "#888", fontSize: 12 },
  chipTextActive: { color: "#e50914" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 12 },
  hint: { color: "#666", fontSize: 14 },
  retryBtn: {
    backgroundColor: "#e50914",
    borderRadius: 8,
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  retryText: { color: "#fff", fontWeight: "600", fontSize: 13 },
  result: {
    flexDirection: "row",
    gap: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#222",
  },
  thumb: {
    width: 90,
    height: 54,
    borderRadius: 4,
    backgroundColor: "#222",
  },
  resultText: { flex: 1, gap: 3 },
  title: { color: "#fff", fontSize: 13, fontWeight: "600", lineHeight: 18 },
  meta: { color: "#888", fontSize: 12 },
  level: { color: "#6ab0f5", fontSize: 11 },
});

