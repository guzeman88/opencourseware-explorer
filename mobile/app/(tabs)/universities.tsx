import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "expo-router";
import { fetchUniversities } from "@/lib/api";
import { Ionicons } from "@expo/vector-icons";

const SOURCE_LABELS: Record<string, string> = {
  mit_ocw: "MIT OCW",
  yale_ocw: "Yale",
  stanford: "Stanford",
  nptel: "NPTEL",
  berkeley: "UC Berkeley",
  harvard: "Harvard",
};

export default function UniversitiesScreen() {
  const router = useRouter();
  const { data, isLoading } = useQuery({
    queryKey: ["universities_mobile"],
    queryFn: () => fetchUniversities(1, 50),
  });

  const universities = data?.items ?? [];

  if (isLoading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#e50914" />
      </View>
    );
  }

  return (
    <FlatList
      data={universities}
      keyExtractor={(item) => item.id}
      contentContainerStyle={styles.list}
      renderItem={({ item }) => (
        <TouchableOpacity
          style={styles.row}
          onPress={() =>
            router.push({
              pathname: "/universities/[slug]",
              params: { slug: item.slug },
            })
          }
        >
          <View style={styles.icon}>
            <Ionicons name="school" size={24} color="#e50914" />
          </View>
          <View style={styles.info}>
            <Text style={styles.name}>
              {SOURCE_LABELS[item.source_key] ?? item.name}
            </Text>
            {item.course_count != null && (
              <Text style={styles.count}>{item.course_count} courses</Text>
            )}
          </View>
          <Ionicons name="chevron-forward" size={18} color="#444" />
        </TouchableOpacity>
      )}
      ItemSeparatorComponent={() => <View style={styles.divider} />}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: "#141414" },
  list: { backgroundColor: "#141414", paddingBottom: 24 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    padding: 16,
    backgroundColor: "#141414",
  },
  icon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#2a0a0a",
    alignItems: "center",
    justifyContent: "center",
  },
  info: { flex: 1 },
  name: { color: "#fff", fontSize: 15, fontWeight: "600" },
  count: { color: "#888", fontSize: 12, marginTop: 2 },
  divider: { height: 1, backgroundColor: "#222" },
});
