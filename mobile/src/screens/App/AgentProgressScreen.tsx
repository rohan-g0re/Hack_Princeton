/**
 * Agent Progress Screen - Real-time agent progress via WebSocket
 */
import React, { useEffect, useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { WebSocketService } from '../../services/websocket';

export default function AgentProgressScreen({ route, navigation }: any) {
  const { sessionId, jobId, platforms } = route.params;
  const [updates, setUpdates] = useState<any[]>([]);
  const [platformStatus, setPlatformStatus] = useState<Record<string, string>>({});
  const wsService = useRef(new WebSocketService());

  useEffect(() => {
    // Initialize platform status
    const initialStatus: Record<string, string> = {};
    platforms.forEach((platform: string) => {
      initialStatus[platform] = 'pending';
    });
    setPlatformStatus(initialStatus);

    // Connect WebSocket
    const ws = wsService.current;
    ws.connect(sessionId);

    ws.onMessage((data) => {
      console.log('WebSocket message:', data);
      
      setUpdates((prev) => [...prev, data]);

      if (data.type === 'agent_update') {
        setPlatformStatus((prev) => ({
          ...prev,
          [data.platform]: data.status,
        }));
      }

      if (data.type === 'job_completed') {
        // Navigate to cart status after a delay
        setTimeout(() => {
          navigation.replace('CartStatus', { sessionId });
        }, 2000);
      }
    });

    return () => {
      ws.disconnect();
    };
  }, [sessionId, platforms, navigation]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return '#007AFF';
      case 'completed':
        return '#34C759';
      case 'failed':
        return '#FF3B30';
      default:
        return '#999';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      default:
        return '⏳';
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Finding your items...</Text>
        <Text style={styles.subtitle}>Job ID: {jobId}</Text>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.platformsSection}>
          {platforms.map((platform: string) => {
            const status = platformStatus[platform] || 'pending';
            return (
              <View
                key={platform}
                style={[
                  styles.platformCard,
                  { borderLeftColor: getStatusColor(status) },
                ]}
              >
                <Text style={styles.platformIcon}>{getStatusIcon(status)}</Text>
                <View style={styles.platformInfo}>
                  <Text style={styles.platformName}>{platform}</Text>
                  <Text style={[styles.platformStatus, { color: getStatusColor(status) }]}>
                    {status}
                  </Text>
                </View>
                {status === 'running' && (
                  <ActivityIndicator size="small" color={getStatusColor(status)} />
                )}
              </View>
            );
          })}
        </View>

        <View style={styles.updatesSection}>
          <Text style={styles.updatesTitle}>Live Updates</Text>
          {updates.length === 0 ? (
            <View style={styles.emptyState}>
              <ActivityIndicator size="large" color="#007AFF" />
              <Text style={styles.emptyText}>Waiting for updates...</Text>
            </View>
          ) : (
            updates.map((update, index) => (
              <View key={index} style={styles.updateCard}>
                <Text style={styles.updateTime}>
                  {new Date().toLocaleTimeString()}
                </Text>
                <Text style={styles.updateMessage}>{update.message}</Text>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 12,
    color: '#666',
  },
  content: {
    flex: 1,
  },
  platformsSection: {
    padding: 20,
  },
  platformCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderLeftWidth: 4,
  },
  platformIcon: {
    fontSize: 32,
    marginRight: 15,
  },
  platformInfo: {
    flex: 1,
  },
  platformName: {
    fontSize: 18,
    fontWeight: '600',
    textTransform: 'capitalize',
    marginBottom: 2,
  },
  platformStatus: {
    fontSize: 14,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  updatesSection: {
    padding: 20,
    paddingTop: 0,
  },
  updatesTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    marginTop: 10,
    fontSize: 14,
    color: '#666',
  },
  updateCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  updateTime: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  updateMessage: {
    fontSize: 14,
    color: '#333',
  },
});

