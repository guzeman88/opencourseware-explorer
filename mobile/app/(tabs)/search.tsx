import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { searchCourses } from "@/lib/api";

export default function SearchScreen() {
  const [q, setQ] = useState("");
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["search_mobile", q],
    queryFn: () => searchCourses(q, { page_size: 30 }),
    enabled: q.trim().length >= 2,
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

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#e50914" />
        </View>
      ) : q.trim().length < 2 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>Type at least 2 characters to search</Text>
        </View>
      ) : courses.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.hint}>No courses found for "{q}"</Text>
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
              </View>
            </TouchableOpacity>
          )}
          contentContainerStyle={{ paddingBottom: 24 }}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  input: {
    margin: 12,
    backgroundColor: "#222",
    borderWidth: 1,
    borderColor: "#333",
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: "#fff",
    fontSize: 15,
  },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
  hint: { color: "#666", fontSize: 14 },
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
  resultText: { flex: 1, gap: 4 },
  title: { color: "#fff", fontSize: 13, fontWeight: "600", lineHeight: 18 },
  meta: { color: "#888", fontSize: 12 },
});
