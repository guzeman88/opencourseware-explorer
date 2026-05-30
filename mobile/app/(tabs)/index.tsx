import {
  View,
  Text,
  FlatList,
  ActivityIndicator,
  StyleSheet,
  Pressable,
  Image,
} from "react-native";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { fetchCourses } from "@/lib/api";
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
    `https://i.ytimg.com/vi/${course.university_slug}/hqdefault.jpg`;

  return (
    <Pressable style={styles.card} onPress={onPress} android_ripple={{ color: "#333" }}>
      <Image
        source={{ uri: thumb }}
        style={styles.thumbnail}
        resizeMode="cover"
      />
      <View style={styles.cardInfo}>
        <Text style={styles.cardTitle} numberOfLines={2}>
          {course.title}
        </Text>
        <Text style={styles.cardMeta}>
          {course.university_name} · {course.total_videos} lectures
        </Text>
      </View>
    </Pressable>
  );
}

export default function BrowseScreen() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  const {
    data,
    isLoading,
    isError,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ["browse_infinite"],
    queryFn: ({ pageParam = 1 }) =>
      fetchCourses({
        has_video_lectures: true,
        sort_by: "view_count",
        sort_dir: "desc",
        page: pageParam,
        page_size: 24,
      }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.pages ? lastPage.page + 1 : undefined,
  });

  const courses = data?.pages.flatMap((p) => p.items) ?? [];

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e50914" />
      </View>
    );
  }

  if (isError) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Couldn't load courses.</Text>
        <Pressable style={styles.retryBtn} onPress={() => refetch()}>
          <Text style={styles.retryText}>Try again</Text>
        </Pressable>
      </View>
    );
  }

  return (
    <View style={styles.container}>
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
        contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 24 }]}
        showsVerticalScrollIndicator={false}
        onEndReached={() => {
          if (hasNextPage && !isFetchingNextPage) fetchNextPage();
        }}
        onEndReachedThreshold={0.5}
        ListFooterComponent={
          isFetchingNextPage ? (
            <ActivityIndicator
              size="small"
              color="#e50914"
              style={{ marginVertical: 16 }}
            />
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414", gap: 12 },
  list: { paddingHorizontal: 8, paddingTop: 8 },
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
  errorText: { color: "#aaa", fontSize: 15 },
  retryBtn: {
    backgroundColor: "#e50914",
    borderRadius: 8,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  retryText: { color: "#fff", fontWeight: "600" },
});
