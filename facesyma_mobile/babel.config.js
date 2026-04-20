module.exports = {
  presets: ['module:@react-native/babel-preset'],
  plugins: [
    ['module-resolver', {
      root: ['./src'],
      extensions: ['.ios.js', '.android.js', '.js', '.ts', '.tsx', '.json'],
      alias: {
        '@screens':    './src/screens',
        '@components': './src/components',
        '@services':   './src/services',
        '@store':      './src/store',
        '@utils':      './src/utils',
      },
    }],
    'react-native-reanimated/plugin',
  ],
};
