# vue-lsp

The official `typescript-lsp` server, plus `.vue` files. It loads
`@vue/typescript-plugin` into `typescript-language-server`, so LSP answers
cover the `<script>` blocks of Vue single-file components. It gives no
answers inside `<template>` or `<style>`.

Disable `typescript-lsp@claude-plugins-official` while this is enabled, so two
servers do not both claim `.ts` files.

## Requirements

Both are global npm packages under nvm (Node v22.17.0):

```bash
npm install -g typescript-language-server typescript
npm install -g @vue/typescript-plugin@3.3.6
```

Keep `@vue/typescript-plugin` at the same version as the project's `vue-tsc`.
The plugin path in `.claude-plugin/plugin.json` is absolute, so update it
after a Node version change under nvm.
