/**
 * WebSocket client for real-time voice training.
 *
 * Provides:
 * - Automatic reconnection
 * - Message type handling
 * - Event callbacks
 */

export type WebSocketMessageType =
  | "connected"
  | "prospect_thinking"
  | "prospect_response"
  | "gauge_update"
  | "reversal"
  | "event"
  | "session_ended"
  | "error"
  | "pong";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  timestamp?: string;
  [key: string]: unknown;
}

export interface ProspectResponse {
  type: "prospect_response";
  text: string;
  audio_base64?: string;
  mood: string;
  jauge: number;
  jauge_delta: number;
  behavioral_cue?: string;
  is_event: boolean;
  event_type?: string;
  feedback?: {
    jauge?: number;
    jauge_delta?: number;
    positive_actions: string[];
    negative_actions: string[];
    tips: string[];
  };
  conversion_possible: boolean;
  timestamp: string;
}

export interface GaugeUpdate {
  type: "gauge_update";
  jauge: number;
  delta: number;
  mood: string;
  timestamp: string;
}

export interface SessionEnded {
  type: "session_ended";
  session_id: number;
  status: string;
  evaluation: {
    overall_score: number;
    final_gauge: number;
    gauge_progression: number;
    positive_actions_count: number;
    negative_actions_count: number;
    converted: boolean;
    points_forts: string[];
    axes_amelioration: string[];
    conseil_principal: string;
    passed: boolean;
  };
  timestamp: string;
}

export interface VoiceWebSocketCallbacks {
  onConnected?: (data: { session_id: number; jauge: number; mood: string }) => void;
  onProspectThinking?: () => void;
  onProspectResponse?: (response: ProspectResponse) => void;
  onGaugeUpdate?: (update: GaugeUpdate) => void;
  onReversal?: (data: { type: string; message: string }) => void;
  onEvent?: (data: { event_type: string; message: string }) => void;
  onSessionEnded?: (data: SessionEnded) => void;
  onError?: (message: string) => void;
  onDisconnect?: () => void;
  onReconnecting?: (attempt: number) => void;
}

export class VoiceWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: number;
  private token: string;
  private callbacks: VoiceWebSocketCallbacks;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isClosing = false;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor(
    sessionId: number,
    token: string,
    callbacks: VoiceWebSocketCallbacks
  ) {
    this.sessionId = sessionId;
    this.token = token;
    this.callbacks = callbacks;
  }

  /**
   * Get WebSocket URL based on environment.
   */
  private getWebSocketUrl(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    // Convert http(s) to ws(s)
    const wsUrl = apiUrl.replace(/^http/, "ws");
    return `${wsUrl}/ws/voice/${this.sessionId}?token=${this.token}`;
  }

  /**
   * Connect to WebSocket server.
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log("[WS] Already connected");
      return;
    }

    this.isClosing = false;
    const url = this.getWebSocketUrl();
    console.log("[WS] Connecting to:", url.replace(/token=.*/, "token=***"));

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log("[WS] Connected");
        this.reconnectAttempts = 0;
        this.startPingInterval();
      };

      this.ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (e) {
          console.error("[WS] Failed to parse message:", e);
        }
      };

      this.ws.onerror = (error) => {
        console.error("[WS] Error:", error);
      };

      this.ws.onclose = (event) => {
        console.log("[WS] Closed:", event.code, event.reason);
        this.stopPingInterval();

        if (!this.isClosing && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          this.callbacks.onReconnecting?.(this.reconnectAttempts);
          console.log(`[WS] Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        } else {
          this.callbacks.onDisconnect?.();
        }
      };
    } catch (e) {
      console.error("[WS] Failed to create WebSocket:", e);
      this.callbacks.onError?.("Failed to connect to server");
    }
  }

  /**
   * Handle incoming message.
   */
  private handleMessage(data: WebSocketMessage): void {
    console.log("[WS] Received:", data.type);

    switch (data.type) {
      case "connected":
        this.callbacks.onConnected?.({
          session_id: data.session_id as number,
          jauge: data.jauge as number,
          mood: data.mood as string,
        });
        break;

      case "prospect_thinking":
        this.callbacks.onProspectThinking?.();
        break;

      case "prospect_response":
        this.callbacks.onProspectResponse?.(data as unknown as ProspectResponse);
        break;

      case "gauge_update":
        this.callbacks.onGaugeUpdate?.(data as unknown as GaugeUpdate);
        break;

      case "reversal":
        this.callbacks.onReversal?.({
          type: data.reversal_type as string,
          message: data.message as string,
        });
        break;

      case "event":
        this.callbacks.onEvent?.({
          event_type: data.event_type as string,
          message: data.message as string,
        });
        break;

      case "session_ended":
        this.callbacks.onSessionEnded?.(data as unknown as SessionEnded);
        break;

      case "error":
        this.callbacks.onError?.(data.message as string);
        break;

      case "pong":
        // Keep-alive response, ignore
        break;

      default:
        console.warn("[WS] Unknown message type:", data.type);
    }
  }

  /**
   * Send user message (text or audio).
   */
  sendMessage(text?: string, audioBase64?: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("[WS] Not connected");
      this.callbacks.onError?.("Not connected to server");
      return;
    }

    this.ws.send(
      JSON.stringify({
        type: "user_message",
        text,
        audio_base64: audioBase64,
      })
    );
  }

  /**
   * End the session.
   */
  endSession(): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error("[WS] Not connected");
      return;
    }

    this.ws.send(JSON.stringify({ type: "end_session" }));
  }

  /**
   * Start ping interval to keep connection alive.
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Every 30 seconds
  }

  /**
   * Stop ping interval.
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Disconnect from WebSocket server.
   */
  disconnect(): void {
    this.isClosing = true;
    this.stopPingInterval();

    if (this.ws) {
      this.ws.close(1000, "Client disconnecting");
      this.ws = null;
    }
  }

  /**
   * Check if connected.
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}
