import React, { useEffect } from 'react';
import { StatusBar, View, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import Icon from 'react-native-vector-icons/Ionicons';

// Screens
import MatchesScreen from './src/screens/MatchesScreen';
import HistoryScreen from './src/screens/HistoryScreen';
import MatchAnalysisScreen from './src/screens/MatchAnalysisScreen';
import { Colors } from './src/constants/colors';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000,
    },
  },
});

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

function MatchesStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerShown: false,
        cardStyle: { backgroundColor: Colors.bg },
      }}>
      <Stack.Screen name="MatchesList" component={MatchesScreen} />
      <Stack.Screen 
        name="MatchAnalysis" 
        component={MatchAnalysisScreen}
        options={{
          presentation: 'modal',
          cardStyle: { backgroundColor: Colors.bg },
        }}
      />
    </Stack.Navigator>
  );
}

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: Colors.accent,
        tabBarInactiveTintColor: Colors.textMuted,
        tabBarStyle: {
          backgroundColor: Colors.bgSecondary,
          borderTopWidth: 1,
          borderTopColor: Colors.border,
          elevation: 0,
          height: 60,
          paddingBottom: 8,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          marginBottom: 2,
        },
        tabBarIcon: ({ color, size }) => {
          let iconName: string;
          if (route.name === 'Matches') {
            iconName = 'calendar-outline';
          } else {
            iconName = 'time-outline';
          }
          return <Icon name={iconName} size={size} color={color} />;
        },
      })}>
      <Tab.Screen 
        name="Matches" 
        component={MatchesStack} 
        options={{ title: 'Matches' }}
      />
      <Tab.Screen 
        name="History" 
        component={HistoryScreen} 
        options={{ title: 'History' }}
      />
    </Tab.Navigator>
  );
}

export default function App() {
  return (
    <GestureHandlerRootView style={styles.container}>
      <SafeAreaProvider>
        <QueryClientProvider client={queryClient}>
          <StatusBar barStyle="light-content" backgroundColor={Colors.bg} />
          <NavigationContainer>
            <TabNavigator />
          </NavigationContainer>
        </QueryClientProvider>
      </SafeAreaProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
