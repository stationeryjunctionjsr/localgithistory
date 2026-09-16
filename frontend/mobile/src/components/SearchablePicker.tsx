import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, TouchableOpacity, Modal, FlatList, Pressable, KeyboardAvoidingView, Platform } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../theme';


interface SearchablePickerProps {
  options: string[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  label: string;
  icon?: string;
}

export default function SearchablePicker({
  options,
  value,
  onChange,
  placeholder = 'Select...',
  disabled = false,
  label,
  icon,
}: SearchablePickerProps) {
  const [visible, setVisible] = useState(false);
  const [search, setSearch] = useState('');
  const inputRef = useRef<TextInput>(null);

  const filtered = options.filter((opt) => opt.toLowerCase().includes(search.toLowerCase()));

  useEffect(() => {
    if (visible) {
      setTimeout(() => inputRef.current?.focus(), 200);
    } else {
      setSearch('');
    }
  }, [visible]);

  return (
    <View className="mb-4">
      <Text className="mb-2 font-medium text-slate-700">{label}</Text>
      <TouchableOpacity
        className={`flex-row items-center rounded-xl px-4 py-3 ${disabled ? 'bg-slate-200' : 'bg-slate-100'}`}
        onPress={() => {
          if (!disabled) setVisible(true);
        }}
        activeOpacity={disabled ? 1 : 0.7}
      >
        {icon && (
          <Ionicons name={icon as any} size={18} color="#64748B" style={{ marginRight: 8 }} />
        )}
        <Text className={`flex-1 ${value ? 'text-slate-800' : 'text-slate-400'}`}>
          {value || placeholder}
        </Text>
        <Ionicons name="chevron-down" size={16} color="#94A3B8" />
      </TouchableOpacity>

      <Modal visible={visible} transparent animationType="slide" statusBarTranslucent>
        <KeyboardAvoidingView
          style={{ flex: 1, justifyContent: 'flex-end' }}
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 24}
        >
        <Pressable style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' }} onPress={() => setVisible(false)}>
          <Pressable
            style={{ maxHeight: '75%', minHeight: '45%', borderTopLeftRadius: 24, borderTopRightRadius: 24, backgroundColor: colors.surface }}
            onPress={(e) => e.stopPropagation()}
          >
            <View className="border-b border-slate-100 px-5 pb-3 pt-5">
              <View className="mb-3 flex-row items-center justify-between">
                <Text className="text-lg font-bold text-slate-800">{label}</Text>
                <TouchableOpacity onPress={() => setVisible(false)}>
                  <Ionicons name="close" size={24} color="#64748B" />
                </TouchableOpacity>
              </View>
              <View className="flex-row items-center rounded-xl bg-slate-100 px-4 py-2.5">
                <Ionicons name="search" size={18} color="#94A3B8" />
                <TextInput
                  ref={inputRef}
                  className="ml-2 flex-1 text-slate-800"
                  placeholder={`Search ${label.toLowerCase()}...`}
                  placeholderTextColor="#94A3B8"
                  value={search}
                  onChangeText={setSearch}
                  autoCapitalize="none"
                />
                {search.length > 0 && (
                  <TouchableOpacity onPress={() => setSearch('')}>
                    <Ionicons name="close-circle" size={18} color="#94A3B8" />
                  </TouchableOpacity>
                )}
              </View>
            </View>
            <FlatList
              data={filtered}
              keyExtractor={(item) => item}
              className="px-2"
              contentContainerStyle={{ paddingBottom: 40, paddingTop: 4 }}
              keyboardShouldPersistTaps="handled"
              renderItem={({ item }) => (
                <TouchableOpacity
                  className={`mx-2 mb-1 rounded-xl px-4 py-3.5 ${item === value ? 'bg-purple-50' : ''}`}
                  onPress={() => {
                    onChange(item);
                    setVisible(false);
                  }}
                  activeOpacity={0.6}
                >
                  <View className="flex-row items-center justify-between">
                    <Text
                      className={`${item === value ? 'font-semibold text-purple-700' : 'text-slate-700'}`}
                    >
                      {item}
                    </Text>
                    {item === value && (
                      <Ionicons name="checkmark-circle" size={20} color="#7C3AED" />
                    )}
                  </View>
                </TouchableOpacity>
              )}
              ListEmptyComponent={
                <View className="items-center py-8">
                  <Text className="text-sm text-slate-400">No results found</Text>
                </View>
              }
            />
          </Pressable>
        </Pressable>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
