import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'netgo',
  description: 'Lightweight Python search engine toolkit and Wikimedia APIs',
  base: '/netgo/',
  cleanUrls: true,
  lastUpdated: true,

  themeConfig: {
    siteTitle: 'netgo',
    nav: [
      { text: 'Overview', link: '/' },
      { text: 'Search', link: '/netgo.search' },
      { text: 'Page Reading', link: '/netgo.page' },
      { text: 'Sitemaps', link: '/netgo.sitemap' },
      { text: 'Wikimedia', link: '/netgo.wiki' },
      { text: 'Examples', link: '/examples' },
      {
        text: 'v0.4.0',
        items: [
          { text: 'Changelog', link: 'https://github.com/FrancoFantomius/netgo/blob/master/CHANGELOG.md' },
          { text: 'PyPI Package', link: 'https://pypi.org/project/netgo/' },
          { text: 'Source Code', link: 'https://github.com/FrancoFantomius/netgo' }
        ]
      }
    ],

    sidebar: [
      {
        text: 'Core',
        items: [
          { text: 'Overview', link: '/' },
          { text: 'netgo', link: '/netgo' }
        ]
      },
      {
        text: 'Examples & Guides',
        collapsed: false,
        items: [
          { text: 'Code Examples', link: '/examples' }
        ]
      },
      {
        text: 'Search Engines',
        collapsed: false,
        items: [
          { text: 'netgo.search', link: '/netgo.search' },
          { text: 'netgo.search.google', link: '/netgo.search.google' },
          { text: 'netgo.search.bing', link: '/netgo.search.bing' },
          { text: 'netgo.search.models', link: '/netgo.search.models' },
          { text: 'netgo.search.errors', link: '/netgo.search.errors' }
        ]
      },
      {
        text: 'Page Extraction',
        collapsed: false,
        items: [
          { text: 'netgo.page', link: '/netgo.page' },
          { text: 'netgo.page.fetch', link: '/netgo.page.fetch' },
          { text: 'netgo.page.extract', link: '/netgo.page.extract' },
          { text: 'netgo.page.models', link: '/netgo.page.models' },
          { text: 'netgo.page.errors', link: '/netgo.page.errors' }
        ]
      },
      {
        text: 'Sitemaps',
        collapsed: false,
        items: [
          { text: 'netgo.sitemap', link: '/netgo.sitemap' },
          { text: 'netgo.sitemap.fetch', link: '/netgo.sitemap.fetch' },
          { text: 'netgo.sitemap.parse', link: '/netgo.sitemap.parse' },
          { text: 'netgo.sitemap.models', link: '/netgo.sitemap.models' },
          { text: 'netgo.sitemap.errors', link: '/netgo.sitemap.errors' }
        ]
      },
      {
        text: 'Wikimedia & Wikidata',
        collapsed: false,
        items: [
          { text: 'netgo.wiki', link: '/netgo.wiki' },
          { text: 'netgo.wiki.core', link: '/netgo.wiki.core' },
          { text: 'netgo.wiki.client', link: '/netgo.wiki.client' },
          { text: 'netgo.wiki.wikidata', link: '/netgo.wiki.wikidata' },
          { text: 'netgo.wiki.wikimedia', link: '/netgo.wiki.wikimedia' },
          { text: 'netgo.wiki.wiktionary', link: '/netgo.wiki.wiktionary' },
          { text: 'netgo.wiki.models', link: '/netgo.wiki.models' },
          { text: 'netgo.wiki.errors', link: '/netgo.wiki.errors' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/FrancoFantomius/netgo' }
    ],

    search: {
      provider: 'local'
    },

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-present FrancoFantomius'
    }
  }
})
