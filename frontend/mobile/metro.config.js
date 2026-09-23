const { getDefaultConfig } = require('expo/metro-config');
const { withNativeWind } = require('nativewind/metro');
const path = require('path');

// Ensure Metro resolves the shared api-client package
const projectRoot = __dirname;
const workspaceRoot = path.resolve(projectRoot, '..');

const config = getDefaultConfig(projectRoot);
const apiClientPath = path.resolve(workspaceRoot, 'packages', 'api-client');
const i18nPath = path.resolve(workspaceRoot, 'packages', 'i18n');
config.watchFolders = [projectRoot, apiClientPath, i18nPath];
config.resolver = config.resolver || {};
config.resolver.nodeModulesPaths = [
  path.join(projectRoot, 'node_modules'),
  path.join(workspaceRoot, 'node_modules'),
  path.join(workspaceRoot, 'packages', 'api-client', 'node_modules'),
  path.join(workspaceRoot, 'packages', 'i18n', 'node_modules'),
];
config.resolver.extraNodeModules = {
  ...config.resolver.extraNodeModules,
  '@sj/api-client': path.join(workspaceRoot, 'packages', 'api-client'),
  '@sj/i18n': path.join(workspaceRoot, 'packages', 'i18n'),
};

module.exports = withNativeWind(config, { input: './global.css' });
