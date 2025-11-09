/**
 * Recipe Input Screen - User enters recipe query
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { api } from '../../services/api';

export default function RecipeInputScreen({ navigation }: any) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGetIngredients = async () => {
    if (!query.trim()) {
      Alert.alert('Error', 'Please enter a recipe name');
      return;
    }

    setLoading(true);
    try {
      const response = await api.getRecipeIngredients(query);
      
      navigation.navigate('Ingredients', {
        sessionId: response.session_id,
        recipeName: response.recipe_name,
        ingredients: response.ingredients,
      });
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Could not fetch ingredients. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <Text style={styles.emoji}>🍳</Text>
        <Text style={styles.title}>What do you want to cook?</Text>
        <Text style={styles.subtitle}>
          Enter a recipe name and we'll find all the ingredients you need
        </Text>

        <TextInput
          style={styles.input}
          placeholder="e.g., Caesar Salad, Pasta Carbonara..."
          value={query}
          onChangeText={setQuery}
          autoFocus
          returnKeyType="search"
          onSubmitEditing={handleGetIngredients}
          editable={!loading}
        />

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleGetIngredients}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Get Ingredients</Text>
          )}
        </TouchableOpacity>

        <View style={styles.examplesSection}>
          <Text style={styles.examplesTitle}>Popular recipes:</Text>
          {['Caesar Salad', 'Pasta Carbonara', 'Chicken Stir Fry', 'Tacos'].map((example) => (
            <TouchableOpacity
              key={example}
              style={styles.exampleChip}
              onPress={() => setQuery(example)}
              disabled={loading}
            >
              <Text style={styles.exampleText}>{example}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  emoji: {
    fontSize: 64,
    textAlign: 'center',
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: 10,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 12,
    padding: 15,
    fontSize: 18,
    marginBottom: 20,
    backgroundColor: '#f9f9f9',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 12,
    padding: 18,
    alignItems: 'center',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
  examplesSection: {
    marginTop: 30,
  },
  examplesTitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 10,
  },
  exampleChip: {
    backgroundColor: '#f0f0f0',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 15,
    marginBottom: 10,
  },
  exampleText: {
    fontSize: 14,
    color: '#333',
  },
});

