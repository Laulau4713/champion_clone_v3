"use client";

import React from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChartDataPoint } from "@/types";
import { cn } from "@/lib/utils";

interface ProgressChartProps {
  data: ChartDataPoint[];
  isLoading?: boolean;
  targetScore?: number;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: Array<{ value: number; payload: ChartDataPoint }>;
  label?: string;
}> = ({ active, payload }) => {
  if (!active || !payload?.[0]) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-xl">
      <p className="text-xs text-slate-400 mb-1">{data.date}</p>
      <p className="text-lg font-bold text-white">{data.score.toFixed(1)}/10</p>
      <p className="text-xs text-slate-500">Session #{data.sessionId}</p>
    </div>
  );
};

export const ProgressChart: React.FC<ProgressChartProps> = ({
  data,
  isLoading,
  targetScore = 8,
}) => {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Progression</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[300px] w-full" />
        </CardContent>
      </Card>
    );
  }

  if (data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Progression</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center text-slate-500">
            Aucune donnée disponible. Commencez un entraînement !
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate trend line
  const avgScore = data.reduce((sum, d) => sum + d.score, 0) / data.length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Progression</CardTitle>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-primary-500" />
            <span className="text-slate-400">Score</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-success-500 opacity-50" style={{ borderStyle: "dashed" }} />
            <span className="text-slate-400">Objectif ({targetScore})</span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart
            data={data}
            margin={{ top: 20, right: 20, left: 0, bottom: 20 }}
          >
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
            <XAxis
              dataKey="date"
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[0, 10]}
              stroke="#64748B"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine
              y={targetScore}
              stroke="#10B981"
              strokeDasharray="5 5"
              strokeOpacity={0.5}
            />
            <ReferenceLine
              y={avgScore}
              stroke="#F59E0B"
              strokeDasharray="3 3"
              strokeOpacity={0.3}
              label={{
                value: `Moy: ${avgScore.toFixed(1)}`,
                position: "right",
                fill: "#F59E0B",
                fontSize: 10,
              }}
            />
            <Line
              type="monotone"
              dataKey="score"
              stroke="#8B5CF6"
              strokeWidth={2}
              dot={{
                fill: "#8B5CF6",
                strokeWidth: 2,
                r: 4,
              }}
              activeDot={{
                fill: "#8B5CF6",
                strokeWidth: 2,
                r: 6,
                stroke: "#fff",
              }}
              fill="url(#scoreGradient)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default ProgressChart;
