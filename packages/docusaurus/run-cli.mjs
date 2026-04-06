#!/usr/bin/env node

import * as docusaurusLoggerModule from "@docusaurus/logger"
import { existsSync, mkdirSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import unzipper from "unzipper"

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const logger = docusaurusLoggerModule.logger ?? docusaurusLoggerModule.default ?? docusaurusLoggerModule

const OPS_FRONTIER_PROJECT_ROOT = process.env.OPS_FRONTIER_PROJECT_ROOT || process.cwd()
const OPS_FRONTIER_DOCUSAURUS_PATH = `${OPS_FRONTIER_PROJECT_ROOT}/.docusaurus-template`
const DOCUSAURUS_CONFIG_PATH = join(__dirname, "docusaurus.config.ts")
const SITE_BOOTSTRAP_COMMANDS = new Set(["build", "start"])

function getCliCommand() {
    const cliCommand = process.argv[2]
    if (!cliCommand || cliCommand.startsWith("-")) {
        return undefined
    }
    return cliCommand
}

function ensureDocsPath() {
    const docsPath = process.env.OPS_FRONTIER_DOCS_PATH || `${OPS_FRONTIER_PROJECT_ROOT}/docs`
    process.env.OPS_FRONTIER_DOCS_PATH = docsPath

    if (!existsSync(docsPath)) {
        logger.error(`Error: ${docsPath} does not exist.`)
        process.exit(1)
    }

    logger.info(`Document path set to ${docsPath}`)
}

async function ensureSiteTemplate() {
    if (existsSync(OPS_FRONTIER_DOCUSAURUS_PATH)) {
        logger.info(
            `${OPS_FRONTIER_DOCUSAURUS_PATH} already exists. Not unzipping. If you want to reinitialize, delete the directory and run the command again.`,
        )
        return
    }

    logger.info(`Docusaurus directory does not exist. Creating: ${OPS_FRONTIER_DOCUSAURUS_PATH}`)
    mkdirSync(OPS_FRONTIER_DOCUSAURUS_PATH, { recursive: true })

    const zipFilePath = join(__dirname, "docusaurus-template.zip")
    if (!existsSync(zipFilePath)) {
        logger.error(`Error: ${zipFilePath} not found.`)
        process.exit(1)
    }

    logger.info(`Unzipping ${zipFilePath} to ${OPS_FRONTIER_DOCUSAURUS_PATH}`)
    try {
        const directory = await unzipper.Open.file(zipFilePath)
        await directory.extract({ path: OPS_FRONTIER_DOCUSAURUS_PATH })
        logger.info(`Successfully unzipped ${zipFilePath} to ${OPS_FRONTIER_DOCUSAURUS_PATH}`)
    } catch (error) {
        logger.error(`Error unzipping ${zipFilePath}:`, error)
        process.exit(1)
    }
}

function changeToSiteRoot() {
    try {
        process.chdir(OPS_FRONTIER_DOCUSAURUS_PATH)
        logger.info(`Current directory changed to ${process.cwd()} as docusaurus site root`)
    } catch (error) {
        logger.error(`Error: chdir: ${error}`)
        process.exit(1)
    }
}

function ensureConfigOption() {
    const args = process.argv.slice(2)
    if (args.includes("--config")) {
        return
    }

    process.argv.splice(3, 0, "--config", DOCUSAURUS_CONFIG_PATH)
}

const cliCommand = getCliCommand()
if (cliCommand) {
    ensureDocsPath()

    if (SITE_BOOTSTRAP_COMMANDS.has(cliCommand)) {
        await ensureSiteTemplate()
    }

    changeToSiteRoot()
    ensureConfigOption()
}

await import("@docusaurus/core/bin/docusaurus.mjs")
