import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/providers/auth-provider";
import type { CourseSummary } from "@/types";

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` };
}

/** Fetch the full list of saved courses once; reused by all status checks. */
export function useLibrary() {
  const { token } = useAuth();
  return useQuery({
    queryKey: ["library"],
    queryFn: async () => {
      const { data } = await apiClient.get<CourseSummary[]>("/users/me/library", {
        headers: authHeader(token!),
      });
      return data;
    },
    enabled: !!token,
    staleTime: 30_000,
  });
}

/**
 * Derive saved status from the shared library list — no extra per-card request.
 * Returns undefined while loading, true/false once the library is known.
 */
export function useLibraryStatus(courseId: string) {
  const { token } = useAuth();
  const { data: library } = useLibrary();
  if (!token) return { data: false as boolean };
  if (library === undefined) return { data: undefined };
  return { data: library.some((c) => c.id === courseId) };
}

export function useLibraryToggle(courseId: string) {
  const { token } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (currentlySaved: boolean) => {
      if (currentlySaved) {
        await apiClient.delete(`/users/me/library/${courseId}`, {
          headers: authHeader(token!),
        });
        return false;
      } else {
        await apiClient.post(
          "/users/me/library",
          { course_id: courseId },
          { headers: authHeader(token!) }
        );
        return true;
      }
    },
    onMutate: async (currentlySaved) => {
      await queryClient.cancelQueries({ queryKey: ["library"] });
      // Optimistically update the library list
      const previous = queryClient.getQueryData<CourseSummary[]>(["library"]);
      if (previous !== undefined) {
        if (currentlySaved) {
          queryClient.setQueryData(
            ["library"],
            previous.filter((c) => c.id !== courseId)
          );
        }
        // For "add", we'd need the full course object — skip optimistic add,
        // just invalidate after settle.
      }
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous !== undefined) {
        queryClient.setQueryData(["library"], context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["library"] });
    },
  });
}

