import {
  View,
  Text,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  TouchableOpacity,
  Image,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { fetchFeaturedCourses, fetchCourses } from "@/lib/api";
import type { CourseSummary } from "@/types";

function CourseCard({
  course,
  onPress,
}: {
  course: CourseSummary;
  onPress: () => void;
}) {
  const thumb =
    course.thumbnail_url ??
    (course.youtube_playlist_id
      ? `https://i.ytimg.com/vi_webp/${course.youtube_playlist_id}/mqdefault.webp`
      : undefined);

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.8}>
      <Image
        source={thumb ? { uri: thumb } : require("../../assets/placeholder.png")}
        style={styles.thumbnail}
        resizeMode="cover"
        defaultSource={require("../../assets/placeholder.png")}
      />
      <View style={styles.cardInfo}>
        <Text style={styles.cardTitle} numberOfLines={2}>
          {course.title}
        </Text>
        <Text style={styles.cardMeta}>
          {course.university_name} · {course.total_videos} lectures
        </Text>
      </View>
    </TouchableOpacity>
  );
}

export default function BrowseScreen() {
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["featured"],
    queryFn: () => fetchFeaturedCourses(30),
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
    <View style={styles.container}>
      <Text style={styles.heading}>Featured Courses</Text>
      <FlatList
        data={courses}
        keyExtractor={(item) => item.id}
        numColumns={2}
        columnWrapperStyle={styles.row}
        renderItem={({ item }) => (
          <CourseCard
            course={item}
            onPress={() => router.push(`/course/${item.slug}`)}
          />
        )}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414" },
  heading: {
    fontSize: 20,
    fontWeight: "700",
    color: "#fff",
    paddingHorizontal: 12,
    paddingTop: 16,
    paddingBottom: 8,
  },
  list: { paddingHorizontal: 8, paddingBottom: 24 },
  row: { gap: 8, marginBottom: 8 },
  card: {
    flex: 1,
    backgroundColor: "#1a1a1a",
    borderRadius: 8,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "#2a2a2a",
  },
  thumbnail: { width: "100%", aspectRatio: 16 / 9, backgroundColor: "#222" },
  cardInfo: { padding: 8, gap: 4 },
  cardTitle: { color: "#fff", fontSize: 12, fontWeight: "600", lineHeight: 16 },
  cardMeta: { color: "#888", fontSize: 11 },
});
