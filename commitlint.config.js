module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'scope-empty': [2, 'never'],
    'type-enum': [
      2,
      'always',
      ['feat', 'fix', 'docs', 'perf', 'test', 'build', 'ci', 'chore', 'revert', 'sec', 'refactor'],
    ],
  },
};
