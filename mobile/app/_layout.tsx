import * as Sentry from "@sentry/react-native";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { useCallback, useState } from "react";
import Constants from "expo-constants";
import { SafeAreaProvider } from "react-native-safe-area-context";

// Sentry: only initialise when DSN is provided (no-op otherwise)
const _sentryDsn =
  Constants.expoConfig?.extra?.sentryDsn ?? process.env.EXPO_PUBLIC_SENTRY_DSN;
if (_sentryDsn) {
  Sentry.init({
    dsn: _sentryDsn,
    tracesSampleRate: 0.2,
    enabled: !__DEV__,
  });
}

export {
  // Catch any errors thrown by the Layout component.
  ErrorBoundary,
} from "expo-router";

export const unstable_settings = {
  initialRouteName: "(tabs)",
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      retry: 2,
    },
  },
});

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <StatusBar style="light" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: "#141414" },
            headerTintColor: "#fff",
            headerTitleStyle: { fontWeight: "bold" },
            contentStyle: { backgroundColor: "#141414" },
          }}
        >
          <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
          <Stack.Screen
            name="course/[id]"
            options={{ title: "Course", presentation: "card" }}
          />
        </Stack>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}
