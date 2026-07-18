module.exports = ({ config }) => ({
  ...config,
  extra: {
    ...(config.extra || {}),
    apiUrl: process.env.EXPO_PUBLIC_API_URL || '',
    // Set EXPO_PUBLIC_MAINTENANCE_MODE=true during scheduled mobile upgrades
    maintenanceMode: process.env.EXPO_PUBLIC_MAINTENANCE_MODE === 'true',
  },
});
