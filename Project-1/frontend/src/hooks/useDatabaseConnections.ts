import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "../lib/api";
import type {
  DatabaseConnection,
  DatabaseConnectionCreateInput,
  DatabaseConnectionUpdateInput,
} from "../types";

const QUERY_KEY = ["database-connections"] as const;

export function useDatabaseConnections() {
  const queryClient = useQueryClient();

  const connectionsQuery = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => api.get<DatabaseConnection[]>("/connections"),
  });

  const createConnection = useMutation({
    mutationFn: (payload: DatabaseConnectionCreateInput) =>
      api.post<DatabaseConnection>("/connections", payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const updateConnection = useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: string;
      payload: DatabaseConnectionUpdateInput;
    }) => api.patch<DatabaseConnection>(`/connections/${id}`, payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const deleteConnection = useMutation({
    mutationFn: (id: string) => api.delete<void>(`/connections/${id}`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const testConnection = useMutation({
    mutationFn: (id: string) =>
      api.post<{ success: boolean; message: string }>(`/connections/${id}/test`),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return {
    ...connectionsQuery,
    createConnection,
    updateConnection,
    deleteConnection,
    testConnection,
  };
}
