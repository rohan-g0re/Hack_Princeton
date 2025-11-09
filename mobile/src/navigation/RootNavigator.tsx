/**
 * Root Navigation - Handles auth flow and main app navigation
 */
import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '../context/AuthContext';
import { ActivityIndicator, View } from 'react-native';

// Auth Screens
import SignInScreen from '../screens/Auth/SignInScreen';
import SignUpScreen from '../screens/Auth/SignUpScreen';

// App Screens
import HomeScreen from '../screens/App/HomeScreen';
import RecipeInputScreen from '../screens/App/RecipeInputScreen';
import IngredientsScreen from '../screens/App/IngredientsScreen';
import AgentProgressScreen from '../screens/App/AgentProgressScreen';
import CartStatusScreen from '../screens/App/CartStatusScreen';
import CheckoutScreen from '../screens/App/CheckoutScreen';

const Stack = createNativeStackNavigator();

export default function RootNavigator() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  return (
    <Stack.Navigator>
      {!user ? (
        // Auth Stack
        <>
          <Stack.Screen 
            name="SignIn" 
            component={SignInScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen 
            name="SignUp" 
            component={SignUpScreen}
            options={{ title: 'Create Account' }}
          />
        </>
      ) : (
        // App Stack
        <>
          <Stack.Screen 
            name="Home" 
            component={HomeScreen}
            options={{ title: 'Grocery SuperApp' }}
          />
          <Stack.Screen 
            name="RecipeInput" 
            component={RecipeInputScreen}
            options={{ title: 'Enter Recipe' }}
          />
          <Stack.Screen 
            name="Ingredients" 
            component={IngredientsScreen}
            options={{ title: 'Select Ingredients' }}
          />
          <Stack.Screen 
            name="AgentProgress" 
            component={AgentProgressScreen}
            options={{ title: 'Finding Items...' }}
          />
          <Stack.Screen 
            name="CartStatus" 
            component={CartStatusScreen}
            options={{ title: 'Your Carts' }}
          />
          <Stack.Screen 
            name="Checkout" 
            component={CheckoutScreen}
            options={{ title: 'Checkout' }}
          />
        </>
      )}
    </Stack.Navigator>
  );
}

