/**
 * Ingredients Screen - Select ingredients and platforms
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

export default function IngredientsScreen({ route, navigation }: any) {
  const { sessionId, recipeName, ingredients } = route.params;
  
  const [selectedIngredients, setSelectedIngredients] = useState(
    ingredients.map((_: any, index: number) => index)
  );
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>(['instacart']);
  const [loading, setLoading] = useState(false);

  const toggleIngredient = (index: number) => {
    setSelectedIngredients((prev: number[]) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const togglePlatform = (platform: string) => {
    setSelectedPlatforms((prev) =>
      prev.includes(platform) ? prev.filter((p) => p !== platform) : [...prev, platform]
    );
  };

  const handleStartShopping = async () => {
    if (selectedIngredients.length === 0) {
      Alert.alert('Error', 'Please select at least one ingredient');
      return;
    }

    if (selectedPlatforms.length === 0) {
      Alert.alert('Error', 'Please select at least one platform');
      return;
    }

    const selectedItems = selectedIngredients.map((index: number) => ingredients[index]);

    setLoading(true);
    try {
      const response = await api.startAgents(sessionId, selectedItems, selectedPlatforms);
      
      navigation.navigate('AgentProgress', {
        sessionId,
        jobId: response.job_id,
        platforms: selectedPlatforms,
      });
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Could not start shopping agents'
      );
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <ScrollView style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.recipeName}>{recipeName}</Text>
          <Text style={styles.subtitle}>
            Select the ingredients you want to order
          </Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Ingredients ({selectedIngredients.length} selected)</Text>
          {ingredients.map((ingredient: any, index: number) => (
            <TouchableOpacity
              key={index}
              style={[
                styles.ingredientCard,
                selectedIngredients.includes(index) && styles.ingredientCardSelected,
              ]}
              onPress={() => toggleIngredient(index)}
            >
              <View style={styles.checkbox}>
                {selectedIngredients.includes(index) && (
                  <Text style={styles.checkmark}>✓</Text>
                )}
              </View>
              <View style={styles.ingredientInfo}>
                <Text style={styles.ingredientName}>{ingredient.name}</Text>
                <Text style={styles.ingredientQuantity}>{ingredient.quantity}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Select Platforms</Text>
          {[
            { id: 'instacart', name: 'Instacart', emoji: '🛒' },
            { id: 'ubereats', name: 'UberEats', emoji: '🚗' },
          ].map((platform) => (
            <TouchableOpacity
              key={platform.id}
              style={[
                styles.platformCard,
                selectedPlatforms.includes(platform.id) && styles.platformCardSelected,
              ]}
              onPress={() => togglePlatform(platform.id)}
            >
              <Text style={styles.platformEmoji}>{platform.emoji}</Text>
              <Text style={styles.platformName}>{platform.name}</Text>
              {selectedPlatforms.includes(platform.id) && (
                <Text style={styles.selectedBadge}>Selected</Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <TouchableOpacity
          style={[styles.startButton, loading && styles.startButtonDisabled]}
          onPress={handleStartShopping}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.startButtonText}>
              Start Shopping on {selectedPlatforms.length} Platform{selectedPlatforms.length !== 1 ? 's' : ''}
            </Text>
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
  header: {
    backgroundColor: '#fff',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  recipeName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
  },
  section: {
    marginTop: 20,
    paddingHorizontal: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 10,
  },
  ingredientCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#eee',
  },
  ingredientCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#f0f8ff',
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#007AFF',
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkmark: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  ingredientInfo: {
    flex: 1,
  },
  ingredientName: {
    fontSize: 16,
    fontWeight: '500',
    marginBottom: 2,
  },
  ingredientQuantity: {
    fontSize: 14,
    color: '#666',
  },
  platformCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 10,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#eee',
  },
  platformCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#f0f8ff',
  },
  platformEmoji: {
    fontSize: 32,
    marginRight: 15,
  },
  platformName: {
    fontSize: 18,
    fontWeight: '500',
    flex: 1,
  },
  selectedBadge: {
    backgroundColor: '#007AFF',
    color: '#fff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    fontSize: 12,
    fontWeight: '600',
  },
  footer: {
    padding: 20,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#eee',
  },
  startButton: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  startButtonDisabled: {
    backgroundColor: '#ccc',
  },
  startButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});

