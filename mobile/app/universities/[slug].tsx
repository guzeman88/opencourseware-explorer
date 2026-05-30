import {
  View,
  Text,
  FlatList,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  Image,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { fetchUniversityCourses } from "@/lib/api";

export default function UniversityCoursesScreen() {
  const { slug } = useLocalSearchParams<{ slug: string }>();
  const router = useRouter();

  const { data, isLoading } = useQuery({
    queryKey: ["uni_courses_mobile", slug],
    queryFn: () =>
      fetchUniversityCourses(slug, {
        page_size: 50,
        sort_by: "view_count",
        sort_dir: "desc",
      }),
    enabled: !!slug,
  });

  const courses = data?.items ?? [];

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e50914" />
      </View>
    );
  }

  return (
    <FlatList
      data={courses}
      keyExtractor={(item) => item.id}
      numColumns={2}
      columnWrapperStyle={styles.row}
      contentContainerStyle={styles.list}
      renderItem={({ item }) => (
        <Pressable
          style={styles.card}
          onPress={() => router.push(`/course/${item.slug}`)}
        >
          <Image
            source={{
              uri:
                item.thumbnail_url ??
                `https://i.ytimg.com/vi/${item.id}/hqdefault.jpg`,
            }}
            style={styles.thumb}
            resizeMode="cover"
          />
          <View style={styles.info}>
            <Text style={styles.title} numberOfLines={2}>
              {item.title}
            </Text>
            <Text style={styles.meta}>{item.total_videos} lectures</Text>
          </View>
        </Pressable>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414" },
  list: { padding: 8, backgroundColor: "#141414", paddingBottom: 24 },
  row: { gap: 8, marginBottom: 8 },
  card: {
    flex: 1,
    backgroundColor: "#1a1a1a",
    borderRadius: 8,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#2a2a2a",
  },
  thumb: { width: "100%", aspectRatio: 16 / 9, backgroundColor: "#222" },
  info: { padding: 8, gap: 3 },
  title: { color: "#fff", fontSize: 12, fontWeight: "600", lineHeight: 16 },
  meta: { color: "#888", fontSize: 11 },
});
