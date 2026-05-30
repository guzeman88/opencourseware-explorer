import {
  View,
  Text,
  FlatList,
  Pressable,
  Image,
  StyleSheet,
} from "react-native";
import { useRouter } from "expo-router";
import { useBookmarks } from "@/lib/useBookmarks";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function SavedScreen() {
  const { bookmarks } = useBookmarks();
  const router = useRouter();
  const insets = useSafeAreaInsets();

  if (bookmarks.length === 0) {
    return (
      <View style={styles.empty}>
        <Text style={styles.emptyIcon}>🔖</Text>
        <Text style={styles.emptyTitle}>No saved courses</Text>
        <Text style={styles.emptyHint}>
          Tap the bookmark icon on any course to save it here.
        </Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
    <FlatList
      data={bookmarks}
      keyExtractor={(item) => item.id}
      contentContainerStyle={[styles.list, { paddingBottom: insets.bottom + 24 }]}
      showsVerticalScrollIndicator={false}
      renderItem={({ item }) => (
        <Pressable
          style={styles.row}
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
            <Text style={styles.meta}>
              {item.university_name} · {item.total_videos} lectures
            </Text>
          </View>
        </Pressable>
      )}
    />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#141414" },
  list: { backgroundColor: "#141414", paddingTop: 8 },
  empty: {
    flex: 1,
    backgroundColor: "#141414",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    padding: 32,
  },
  emptyIcon: { fontSize: 48 },
  emptyTitle: { color: "#fff", fontSize: 18, fontWeight: "600" },
  emptyHint: { color: "#666", fontSize: 13, textAlign: "center", lineHeight: 18 },
  row: {
    flexDirection: "row",
    gap: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#222",
    backgroundColor: "#141414",
  },
  thumb: { width: 90, height: 54, borderRadius: 4, backgroundColor: "#222" },
  info: { flex: 1, gap: 4, justifyContent: "center" },
  title: { color: "#fff", fontSize: 13, fontWeight: "600", lineHeight: 18 },
  meta: { color: "#888", fontSize: 12 },
});
