import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  Linking,
} from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { fetchCourse } from "@/lib/api";
import { useBookmarks } from "@/lib/useBookmarks";
import { useState } from "react";
import YoutubeIframe from "react-native-youtube-iframe";
import { Ionicons } from "@expo/vector-icons";

export default function CourseDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const [activeVideo, setActiveVideo] = useState(0);
  const { isBookmarked, toggle } = useBookmarks();

  const { data: course, isLoading, isError, refetch } = useQuery({
    queryKey: ["course_mobile", id],
    queryFn: () => fetchCourse(id),
    enabled: !!id,
  });

  const bookmarked = course ? isBookmarked(course.id) : false;

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e50914" />
      </View>
    );
  }

  if (isError || !course) {
    return (
      <View style={styles.center}>
        <Text style={styles.errorText}>Couldn't load this course.</Text>
        <TouchableOpacity style={styles.retryBtn} onPress={() => refetch()}>
          <Text style={styles.retryText}>Try again</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.backBtn} onPress={() => router.back()}>
          <Text style={styles.backText}>Go back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const currentVideo = course.videos[activeVideo];
  const videoId =
    currentVideo?.youtube_id ?? course.youtube_playlist_id;

  return (
    <ScrollView style={styles.container}>
      {/* Video player */}
      {videoId && (
        <YoutubeIframe
          height={220}
          videoId={
            currentVideo
              ? currentVideo.youtube_id
              : undefined
          }
          playList={
            !currentVideo && course.youtube_playlist_id
              ? course.youtube_playlist_id
              : undefined
          }
        />
      )}

      <View style={styles.content}>
        {/* Meta */}
        <View style={styles.meta}>
          <Text style={styles.university}>{course.university_name}</Text>
          <View style={styles.levelBadge}>
            <Text style={styles.levelText}>{course.level}</Text>
          </View>
        </View>

        <View style={styles.titleRow}>
          <Text style={styles.title}>{course.title}</Text>
          <Pressable onPress={() => toggle(course)} hitSlop={8}>
            <Ionicons
              name={bookmarked ? "bookmark" : "bookmark-outline"}
              size={24}
              color={bookmarked ? "#e50914" : "#888"}
            />
          </Pressable>
        </View>

        {course.instructor && (
          <Text style={styles.instructor}>by {course.instructor}</Text>
        )}

        {/* Subject tags */}
        {course.subjects && course.subjects.length > 0 && (
          <View style={styles.subjects}>
            {course.subjects.map((s) => (
              <View key={s.id} style={styles.subjectBadge}>
                <Text style={styles.subjectText}>{s.name}</Text>
              </View>
            ))}
          </View>
        )}

        {course.description ? (
          <>
            <Text style={styles.sectionTitle}>About</Text>
            <Text style={styles.description}>{course.description}</Text>
          </>
        ) : null}

        {/* Stats row */}
        {(course.total_videos > 0 || course.view_count > 0) && (
          <View style={styles.statsRow}>
            {course.total_videos > 0 && (
              <Text style={styles.stat}>{course.total_videos} lectures</Text>
            )}
            {course.view_count > 0 && (
              <Text style={styles.stat}>{course.view_count.toLocaleString()} views</Text>
            )}
          </View>
        )}

        {/* External link */}
        {course.source_url && (
          <TouchableOpacity
            style={styles.externalBtn}
            onPress={() => Linking.openURL(course.source_url!)}
          >
            <Text style={styles.externalBtnText}>Open Course Page ↗</Text>
          </TouchableOpacity>
        )}

        {/* Video list */}
        {course.videos.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>
              Lectures ({course.videos.length})
            </Text>
            {course.videos.map((video, i) => (
              <TouchableOpacity
                key={video.id}
                style={[
                  styles.videoRow,
                  i === activeVideo && styles.videoRowActive,
                ]}
                onPress={() => setActiveVideo(i)}
              >
                <Text style={styles.videoNum}>{i + 1}</Text>
                <Text style={styles.videoTitle} numberOfLines={2}>
                  {video.title}
                </Text>
              </TouchableOpacity>
            ))}
          </>
        )}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414", gap: 12 },
  content: { padding: 16, gap: 12 },
  meta: { flexDirection: "row", alignItems: "center", gap: 8 },
  university: { color: "#e50914", fontWeight: "600", fontSize: 13 },
  levelBadge: {
    backgroundColor: "#2a2a2a",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  levelText: { color: "#aaa", fontSize: 11 },
  titleRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  title: { flex: 1, color: "#fff", fontSize: 20, fontWeight: "700", lineHeight: 26 },
  instructor: { color: "#aaa", fontSize: 14 },
  subjects: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  subjectBadge: {
    backgroundColor: "#1e2a3a",
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  subjectText: { color: "#6ab0f5", fontSize: 11 },
  statsRow: { flexDirection: "row", gap: 16 },
  stat: { color: "#888", fontSize: 12 },
  sectionTitle: { color: "#fff", fontSize: 16, fontWeight: "600", marginTop: 8 },
  description: { color: "#ccc", fontSize: 14, lineHeight: 20 },
  externalBtn: {
    borderWidth: 1,
    borderColor: "#e50914",
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: "center",
    marginVertical: 4,
  },
  externalBtnText: { color: "#e50914", fontWeight: "600" },
  videoRow: {
    flexDirection: "row",
    gap: 10,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#222",
    alignItems: "flex-start",
  },
  videoRowActive: { backgroundColor: "#1e0000" },
  videoNum: { color: "#666", width: 24, fontSize: 12, paddingTop: 2 },
  videoTitle: { flex: 1, color: "#ddd", fontSize: 13, lineHeight: 18 },
  errorText: { color: "#aaa", fontSize: 15 },
  retryBtn: {
    backgroundColor: "#e50914",
    borderRadius: 8,
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  retryText: { color: "#fff", fontWeight: "600" },
  backBtn: { paddingVertical: 8 },
  backText: { color: "#888", fontSize: 14 },
});
