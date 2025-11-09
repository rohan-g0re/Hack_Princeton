/**
 * Checkout Screen - Final review and mock payment
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { api } from '../../services/api';

export default function CheckoutScreen({ route, navigation }: any) {
  const { sessionId, hasDiffs, totalAmount } = route.params;
  const [loading, setLoading] = useState(false);
  const [applyingDiffs, setApplyingDiffs] = useState(false);
  const [diffsApplied, setDiffsApplied] = useState(false);
  const [paymentComplete, setPaymentComplete] = useState(false);
  const [transactionData, setTransactionData] = useState<any>(null);

  const handleApplyChanges = async () => {
    setApplyingDiffs(true);
    try {
      await api.applyDiffs(sessionId);
      setDiffsApplied(true);
      Alert.alert('Success', 'Cart changes applied successfully!');
    } catch (error: any) {
      Alert.alert('Error', 'Could not apply cart changes');
    } finally {
      setApplyingDiffs(false);
    }
  };

  const handlePayNow = async () => {
    if (hasDiffs && !diffsApplied) {
      Alert.alert(
        'Apply Changes First',
        'Please apply your cart changes before proceeding to payment',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: 'Apply & Pay',
            onPress: async () => {
              await handleApplyChanges();
              await processPayment();
            },
          },
        ]
      );
      return;
    }

    await processPayment();
  };

  const processPayment = async () => {
    setLoading(true);
    try {
      const response = await api.checkout(sessionId);
      setTransactionData(response);
      setPaymentComplete(true);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Checkout failed');
    } finally {
      setLoading(false);
    }
  };

  if (paymentComplete && transactionData) {
    return (
      <View style={styles.container}>
        <ScrollView style={styles.content} contentContainerStyle={styles.successContent}>
          <Text style={styles.successEmoji}>✅</Text>
          <Text style={styles.successTitle}>Payment Successful!</Text>
          <Text style={styles.successSubtitle}>
            Your order has been placed
          </Text>

          <View style={styles.transactionCard}>
            <View style={styles.transactionRow}>
              <Text style={styles.transactionLabel}>Transaction ID</Text>
              <Text style={styles.transactionValue}>
                {transactionData.transaction_id}
              </Text>
            </View>
            <View style={styles.transactionRow}>
              <Text style={styles.transactionLabel}>Knot ID</Text>
              <Text style={styles.transactionValue}>
                {transactionData.knot_transaction_id}
              </Text>
            </View>
            <View style={styles.transactionRow}>
              <Text style={styles.transactionLabel}>Total Amount</Text>
              <Text style={[styles.transactionValue, styles.transactionAmount]}>
                ${transactionData.total_amount.toFixed(2)}
              </Text>
            </View>
            <View style={styles.transactionRow}>
              <Text style={styles.transactionLabel}>Date</Text>
              <Text style={styles.transactionValue}>
                {new Date(transactionData.created_at).toLocaleString()}
              </Text>
            </View>
          </View>

          <View style={styles.platformsSection}>
            <Text style={styles.platformsTitle}>Order Summary</Text>
            {transactionData.platforms.map((platform: any) => (
              <View key={platform.platform} style={styles.platformRow}>
                <Text style={styles.platformName}>{platform.platform}</Text>
                <Text style={styles.platformSubtotal}>
                  ${platform.subtotal.toFixed(2)} ({platform.items_count} items)
                </Text>
              </View>
            ))}
          </View>

          <TouchableOpacity
            style={styles.doneButton}
            onPress={() => navigation.navigate('Home')}
          >
            <Text style={styles.doneButtonText}>Done</Text>
          </TouchableOpacity>
        </ScrollView>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Checkout</Text>
          <Text style={styles.headerSubtitle}>Review your order</Text>
        </View>

        {hasDiffs && (
          <View style={styles.warningCard}>
            <Text style={styles.warningEmoji}>⚠️</Text>
            <View style={styles.warningContent}>
              <Text style={styles.warningTitle}>Cart Changes Detected</Text>
              <Text style={styles.warningText}>
                You've made changes to your cart. Apply them before checkout.
              </Text>
              {!diffsApplied ? (
                <TouchableOpacity
                  style={styles.applyButton}
                  onPress={handleApplyChanges}
                  disabled={applyingDiffs}
                >
                  {applyingDiffs ? (
                    <ActivityIndicator size="small" color="#007AFF" />
                  ) : (
                    <Text style={styles.applyButtonText}>Apply Changes</Text>
                  )}
                </TouchableOpacity>
              ) : (
                <Text style={styles.appliedText}>✓ Changes applied</Text>
              )}
            </View>
          </View>
        )}

        <View style={styles.summaryCard}>
          <Text style={styles.summaryTitle}>Order Total</Text>
          <Text style={styles.summaryAmount}>${totalAmount.toFixed(2)}</Text>
          <Text style={styles.summaryNote}>
            This is a mock payment. No actual charges will be made.
          </Text>
        </View>

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>What happens next?</Text>
          <View style={styles.infoStep}>
            <Text style={styles.infoStepNumber}>1</Text>
            <Text style={styles.infoStepText}>
              Your order will be processed on each platform
            </Text>
          </View>
          <View style={styles.infoStep}>
            <Text style={styles.infoStepNumber}>2</Text>
            <Text style={styles.infoStepText}>
              You'll receive confirmation emails
            </Text>
          </View>
          <View style={styles.infoStep}>
            <Text style={styles.infoStepNumber}>3</Text>
            <Text style={styles.infoStepText}>
              Track your orders in respective apps
            </Text>
          </View>
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.payButton, loading && styles.payButtonDisabled]}
          onPress={handlePayNow}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.payButtonText}>Pay ${totalAmount.toFixed(2)}</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
  },
  successContent: {
    padding: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  warningCard: {
    backgroundColor: '#FFF3CD',
    margin: 15,
    padding: 15,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  warningEmoji: {
    fontSize: 24,
    marginRight: 10,
  },
  warningContent: {
    flex: 1,
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 5,
  },
  warningText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  applyButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    padding: 10,
    alignItems: 'center',
  },
  applyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  appliedText: {
    color: '#34C759',
    fontSize: 14,
    fontWeight: '600',
  },
  summaryCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
  },
  summaryTitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 10,
  },
  summaryAmount: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#007AFF',
    marginBottom: 10,
  },
  summaryNote: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
  infoCard: {
    backgroundColor: '#fff',
    margin: 15,
    padding: 20,
    borderRadius: 12,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 15,
  },
  infoStep: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoStepNumber: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#007AFF',
    color: '#fff',
    textAlign: 'center',
    lineHeight: 30,
    fontWeight: 'bold',
    marginRight: 12,
  },
  infoStepText: {
    fontSize: 14,
    color: '#333',
    flex: 1,
  },
  footer: {
    backgroundColor: '#fff',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  payButton: {
    backgroundColor: '#34C759',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  payButtonDisabled: {
    backgroundColor: '#ccc',
  },
  payButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  successEmoji: {
    fontSize: 72,
    marginBottom: 20,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  successSubtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
  },
  transactionCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: '100%',
    marginBottom: 20,
  },
  transactionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 15,
    paddingBottom: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  transactionLabel: {
    fontSize: 14,
    color: '#666',
  },
  transactionValue: {
    fontSize: 14,
    fontWeight: '500',
    maxWidth: '60%',
    textAlign: 'right',
  },
  transactionAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#34C759',
  },
  platformsSection: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: '100%',
    marginBottom: 20,
  },
  platformsTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 15,
  },
  platformRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  platformName: {
    fontSize: 16,
    fontWeight: '500',
    textTransform: 'capitalize',
  },
  platformSubtotal: {
    fontSize: 16,
    color: '#666',
  },
  doneButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 18,
    width: '100%',
    alignItems: 'center',
  },
  doneButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});

