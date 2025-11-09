/**
 * Cart Status Screen - View and edit carts from all platforms
 */
import React, { useEffect, useState } from 'react';
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

export default function CartStatusScreen({ route, navigation }: any) {
  const { sessionId } = route.params;
  const [loading, setLoading] = useState(true);
  const [carts, setCarts] = useState<any[]>([]);
  const [totalItems, setTotalItems] = useState(0);
  const [totalAmount, setTotalAmount] = useState(0);
  const [expandedPlatforms, setExpandedPlatforms] = useState<string[]>([]);
  const [removedItems, setRemovedItems] = useState<Record<string, any[]>>({});

  useEffect(() => {
    fetchCartStatus();
  }, []);

  const fetchCartStatus = async () => {
    setLoading(true);
    try {
      const response = await api.getCartStatus(sessionId);
      setCarts(response.carts);
      setTotalItems(response.total_items);
      setTotalAmount(response.total_amount);
    } catch (error: any) {
      Alert.alert('Error', 'Could not fetch cart status');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (platform: string) => {
    setExpandedPlatforms((prev) =>
      prev.includes(platform) ? prev.filter((p) => p !== platform) : [...prev, platform]
    );
  };

  const removeItem = (platform: string, itemIndex: number) => {
    const cart = carts.find((c) => c.platform === platform);
    if (!cart) return;

    const item = cart.items[itemIndex];
    
    Alert.alert(
      'Remove Item',
      `Remove ${item.name} from ${platform}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            // Track removed items
            setRemovedItems((prev) => ({
              ...prev,
              [platform]: [...(prev[platform] || []), item],
            }));

            // Update UI
            setCarts((prevCarts) =>
              prevCarts.map((c) =>
                c.platform === platform
                  ? {
                      ...c,
                      items: c.items.filter((_: any, i: number) => i !== itemIndex),
                      item_count: c.item_count - item.quantity,
                      subtotal: c.subtotal - item.price * item.quantity,
                    }
                  : c
              )
            );

            setTotalItems((prev) => prev - item.quantity);
            setTotalAmount((prev) => prev - item.price * item.quantity);
          },
        },
      ]
    );
  };

  const handleProceedToCheckout = async () => {
    // Save diffs if any items were removed
    const hasDiffs = Object.keys(removedItems).length > 0;
    
    if (hasDiffs) {
      try {
        for (const [platform, items] of Object.entries(removedItems)) {
          const diffs = items.map((item) => ({
            action: 'remove',
            item,
          }));
          await api.saveCartDiffs(sessionId, platform, diffs);
        }
      } catch (error) {
        Alert.alert('Error', 'Could not save cart changes');
        return;
      }
    }

    navigation.navigate('Checkout', {
      sessionId,
      hasDiffs,
      totalAmount,
    });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading carts...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Your Shopping Carts</Text>
          <Text style={styles.headerSubtitle}>
            {totalItems} items across {carts.length} platform{carts.length !== 1 ? 's' : ''}
          </Text>
        </View>

        {carts.map((cart) => {
          const isExpanded = expandedPlatforms.includes(cart.platform);
          return (
            <View key={cart.platform} style={styles.cartCard}>
              <TouchableOpacity
                style={styles.cartHeader}
                onPress={() => toggleExpand(cart.platform)}
              >
                <View style={styles.cartHeaderLeft}>
                  <Text style={styles.cartPlatform}>{cart.platform}</Text>
                  <Text style={styles.cartStats}>
                    {cart.item_count} items • ${cart.subtotal.toFixed(2)}
                  </Text>
                </View>
                <Text style={styles.expandIcon}>{isExpanded ? '▼' : '▶'}</Text>
              </TouchableOpacity>

              {isExpanded && (
                <View style={styles.itemsList}>
                  {cart.items.map((item: any, index: number) => (
                    <View key={index} style={styles.itemCard}>
                      <View style={styles.itemInfo}>
                        <Text style={styles.itemName}>{item.name}</Text>
                        <Text style={styles.itemDetails}>
                          Qty: {item.quantity} • {item.size || 'N/A'}
                        </Text>
                        <Text style={styles.itemPrice}>
                          ${(item.price * item.quantity).toFixed(2)}
                        </Text>
                      </View>
                      <TouchableOpacity
                        style={styles.removeButton}
                        onPress={() => removeItem(cart.platform, index)}
                      >
                        <Text style={styles.removeButtonText}>Remove</Text>
                      </TouchableOpacity>
                    </View>
                  ))}
                </View>
              )}
            </View>
          );
        })}
      </ScrollView>

      <View style={styles.footer}>
        <View style={styles.totalSection}>
          <Text style={styles.totalLabel}>Total</Text>
          <Text style={styles.totalAmount}>${totalAmount.toFixed(2)}</Text>
        </View>
        <TouchableOpacity
          style={styles.checkoutButton}
          onPress={handleProceedToCheckout}
        >
          <Text style={styles.checkoutButtonText}>Proceed to Checkout</Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  content: {
    flex: 1,
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
  cartCard: {
    backgroundColor: '#fff',
    marginTop: 10,
    marginHorizontal: 10,
    borderRadius: 12,
    overflow: 'hidden',
  },
  cartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 15,
  },
  cartHeaderLeft: {
    flex: 1,
  },
  cartPlatform: {
    fontSize: 18,
    fontWeight: '600',
    textTransform: 'capitalize',
    marginBottom: 2,
  },
  cartStats: {
    fontSize: 14,
    color: '#666',
  },
  expandIcon: {
    fontSize: 18,
    color: '#007AFF',
  },
  itemsList: {
    borderTopWidth: 1,
    borderTopColor: '#eee',
    padding: 10,
  },
  itemCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 12,
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    marginBottom: 8,
  },
  itemInfo: {
    flex: 1,
  },
  itemName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 4,
  },
  itemDetails: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  itemPrice: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  removeButton: {
    backgroundColor: '#FF3B30',
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 6,
  },
  removeButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  footer: {
    backgroundColor: '#fff',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  totalSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  totalLabel: {
    fontSize: 18,
    fontWeight: '600',
  },
  totalAmount: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  checkoutButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  checkoutButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});

