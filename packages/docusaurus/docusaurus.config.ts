import { existsSync } from "node:fs"
import { join } from "node:path"
import { themes as prismThemes } from "prism-react-renderer"
import type { Config, PresetConfig } from "@docusaurus/types"
import type * as Preset from "@docusaurus/preset-classic"
import type { NavbarItem } from "@docusaurus/theme-common"
import simplePlantUML from "@akebifiky/remark-simple-plantuml"
import sidebars from "./sidebars"
import type * as Redocusaurus from "redocusaurus"

const originalItems: Array<NavbarItem> = [
    {
        type: "docSidebar",
        sidebarId: "reference",
        position: "left",
        label: "リファレンス",
    },
    {
        type: "docSidebar",
        sidebarId: "release",
        position: "left",
        label: "リリース",
    },
    {
        href: "https://github.com/procube-open/docusaurus-template",
        label: "GitHub",
        position: "right",
    },
]

// sidebars のキーのリストを取得
const sidebarIds = Object.keys(sidebars)
const openApiPath = join(process.env.OPS_FRONTIER_PROJECT_ROOT || process.cwd(), "openapi")

// sidebarId が sidebars に含まれるものだけをフィルタリング
const filteredItems = originalItems.filter((item) => {
    if (item.type === "docSidebar") {
        return sidebarIds.includes(item.sidebarId as string)
    }
    return true // docSidebar 以外のアイテムはそのまま残す
})

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

const classicPreset = [
    "@docusaurus/preset-classic",
    {
        docs: {
            path: process.env.OPS_FRONTIER_DOCS_PATH || "docs",
            sidebarPath: "./sidebars.ts",
            remarkPlugins: [[simplePlantUML, { baseUrl: "https://www.plantuml.com/plantuml/svg" }]],
            // _で始まるファイルも通常のドキュメントとして扱う
            exclude: [],
        },
        blog: false,
        theme: {
            customCss: "./src/css/custom.css",
        },
    },
] satisfies PresetConfig

const presets: Config["presets"] = [classicPreset]

if (existsSync(openApiPath)) {
    presets.push([
        "redocusaurus",
        {
            openapi: {
                path: openApiPath,
                routeBasePath: "/api",
            },
            theme: {
                primaryColor: "#1890ff",
            },
        },
    ] satisfies Redocusaurus.PresetEntry)
}

const config: Config = {
    title: "[Enter Title Here]",
    tagline: "[Enter Title Here]",
    favicon: "img/favicon.ico",

    // Set the production url of your site here
    url: "https://procube-open.github.io",
    // Set the /<baseUrl>/ pathname under which your site is served
    // For GitHub pages deployment, it is often '/<projectName>/'
    baseUrl: "/docusaurus-template/",

    // GitHub pages deployment config.
    // If you aren't using GitHub pages, you don't need these.
    organizationName: "procube-open", // Usually your GitHub org/user name.
    projectName: "docusaurus-template", // Usually your repo name.

    onBrokenLinks: "throw",
    onBrokenMarkdownLinks: "warn",

    // Even if you don't use internationalization, you can use this field to set
    // useful metadata like html lang. For example, if your site is Chinese, you
    // may want to replace "en" with "zh-Hans".
    i18n: {
        defaultLocale: "ja",
        locales: ["ja"],
    },

    presets,

    themeConfig: {
        // Replace with your project's social card
        image: "img/devsecops.svg",
        navbar: {
            title: "",
            logo: {
                alt: "Logo",
                src: "img/logo-text.png",
            },
            items: filteredItems,
        },
        footer: {
            style: "dark",
            copyright: `Copyright © ${new Date().getFullYear()} Procube Co,Ltd. Built on ${new Date(
                process.env.BUILD_DATE || new Date().toISOString(),
            ).toLocaleString("ja-JP", {
                year: "numeric",
                month: "2-digit",
                day: "2-digit",
                hour: "2-digit",
                minute: "2-digit",
                timeZone: "Asia/Tokyo",
            })}.`,
        },
        prism: {
            theme: prismThemes.github,
            darkTheme: prismThemes.dracula,
        },
    } satisfies Preset.ThemeConfig,
}

export default config
