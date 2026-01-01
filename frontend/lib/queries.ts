import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getChampions,
  getChampion,
  uploadChampion,
  analyzeChampion,
  deleteChampion,
  getScenarios,
  startTraining,
  respondTraining,
  endTraining,
  getTrainingSessions,
  healthCheck,
  learningAPI,
} from './api';

// Query keys
export const queryKeys = {
  health: ['health'] as const,
  champions: ['champions'] as const,
  champion: (id: number) => ['champion', id] as const,
  scenarios: (championId: number) => ['scenarios', championId] as const,
  sessions: ['sessions'] as const,
  skillsProgress: ['skillsProgress'] as const,
  userProgress: ['userProgress'] as const,
};

// Health
export const useHealth = () =>
  useQuery({
    queryKey: queryKeys.health,
    queryFn: healthCheck,
    refetchInterval: 30000,
  });

// Champions
export const useChampions = () =>
  useQuery({
    queryKey: queryKeys.champions,
    queryFn: getChampions,
  });

export const useChampion = (id: number) =>
  useQuery({
    queryKey: queryKeys.champion(id),
    queryFn: () => getChampion(id),
    enabled: !!id,
  });

export const useUploadChampion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadChampion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.champions });
    },
  });
};

export const useAnalyzeChampion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: analyzeChampion,
    onSuccess: (_, championId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.champion(championId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.champions });
    },
  });
};

export const useDeleteChampion = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteChampion,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.champions });
    },
  });
};

// Scenarios
export const useScenarios = (championId: number, count = 3) =>
  useQuery({
    queryKey: queryKeys.scenarios(championId),
    queryFn: () => getScenarios(championId, count),
    enabled: !!championId,
  });

// Training
export const useStartTraining = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: startTraining,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
  });
};

export const useRespondTraining = () =>
  useMutation({
    mutationFn: respondTraining,
  });

export const useEndTraining = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: endTraining,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.sessions });
    },
  });
};

export const useTrainingSessions = () =>
  useQuery({
    queryKey: queryKeys.sessions,
    queryFn: getTrainingSessions,
  });

// Learning Progress
export const useUserProgress = () =>
  useQuery({
    queryKey: queryKeys.userProgress,
    queryFn: () => learningAPI.getProgress(),
  });

export const useSkillsProgress = () =>
  useQuery({
    queryKey: queryKeys.skillsProgress,
    queryFn: async () => {
      const res = await learningAPI.getSkillsProgress();
      return res.data;
    },
  });
