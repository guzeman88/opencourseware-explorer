import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Linking,
} from "react-native";
import { useLocalSearchParams, useNavigation } from "expo-router";
import { useQuery } from "@tanstack/react-query";
import { fetchCourse } from "@/lib/api";
import { useEffect, useState } from "react";
import YoutubeIframe from "react-native-youtube-iframe";

export default function CourseDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const navigation = useNavigation();
  const [activeVideo, setActiveVideo] = useState(0);

  const { data: course, isLoading } = useQuery({
    queryKey: ["course_mobile", id],
    queryFn: () => fetchCourse(id),
    enabled: !!id,
  });

  useEffect(() => {
    if (course) {
      navigation.setOptions({ title: course.title });
    }
  }, [course, navigation]);

  if (isLoading || !course) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e50914" />
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

        <Text style={styles.title}>{course.title}</Text>

        {course.instructor && (
          <Text style={styles.instructor}>by {course.instructor}</Text>
        )}

        {course.description ? (
          <>
            <Text style={styles.sectionTitle}>About</Text>
            <Text style={styles.description}>{course.description}</Text>
          </>
        ) : null}

        {/* External link */}
        {course.source_url && (
          <TouchableOpacity
            style={styles.externalBtn}
            onPress={() => Linking.openURL(course.source_url!)}
          >
            <Text style={styles.externalBtnText}>Open Course Page</Text>
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
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414" },
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
  title: { color: "#fff", fontSize: 20, fontWeight: "700", lineHeight: 26 },
  instructor: { color: "#aaa", fontSize: 14 },
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
});
