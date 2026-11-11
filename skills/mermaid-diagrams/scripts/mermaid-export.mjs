#!/usr/bin/env node

/**
 * mermaid-export.mjs — Convert Mermaid diagrams to images.
 *
 * Wraps @mermaid-js/mermaid-cli (mmdc) with automatic dependency
 * management and a simplified interface for common export tasks.
 *
 * Usage:
 *   node mermaid-export.mjs <input> <output> [options]
 *
 * Input:
 *   .mmd file     — A standalone Mermaid diagram file.
 *   .md file      — A Markdown file; all ```mermaid blocks are extracted
 *                   and exported individually.
 *
 * Output:
 *   file path     — Output file (format inferred from extension: .png, .svg, .pdf).
 *   directory     — When input is .md, each diagram is exported to this
 *                   directory as diagram-1.<format>, diagram-2.<format>, etc.
 *
 * Options:
 *   --format <fmt>       Output format: png, svg, pdf (default: inferred from output extension, or png)
 *   --theme <name>       Mermaid theme: default, dark, forest, neutral (default: default)
 *   --background <color> Background color, e.g. "white", "transparent", "#f0f0f0" (default: white)
 *   --scale <number>     Pixel scale factor for PNG output (default: 2)
 *   --config <path>      Path to a Mermaid JSON config file
 *   --puppeteer <path>   Path to a Puppeteer config JSON file
 *   --width <pixels>     Viewport width in pixels (default: 800)
 *   --quiet              Suppress informational output
 *   --help               Show this help message
 *
 * Examples:
 *   node mermaid-export.mjs diagram.mmd diagram.png
 *   node mermaid-export.mjs diagram.mmd diagram.svg --theme dark
 *   node mermaid-export.mjs README.md ./images/ --format png --scale 3
 *   node mermaid-export.mjs flow.mmd flow.pdf --background transparent
 *
 * Dependencies:
 *   - Node.js >= 18.19
 *   - @mermaid-js/mermaid-cli (installed automatically on first run via npx)
 */

import { execFileSync, execSync } from "node:child_process";
import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from "node:fs";
import { resolve, extname, basename, join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { randomBytes } from "node:crypto";

// ---------------------------------------------------------------------------
// Argument parsing
// ---------------------------------------------------------------------------

function printHelp() {
  const lines = readFileSync(new URL(import.meta.url), "utf8")
    .split("\n")
    .slice(2); // skip shebang and blank
  const helpLines = [];
  for (const line of lines) {
    if (line.startsWith(" */")) break;
    helpLines.push(line.replace(/^ \* ?/, ""));
  }
  console.log(helpLines.join("\n"));
}

function parseArgs(argv) {
  const positional = [];
  const opts = {
    format: null,
    theme: "default",
    background: "white",
    scale: 2,
    config: null,
    puppeteer: null,
    width: 800,
    quiet: false,
  };

  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    } else if (arg === "--quiet") {
      opts.quiet = true;
    } else if (arg === "--format" && i + 1 < argv.length) {
      opts.format = argv[++i];
    } else if (arg === "--theme" && i + 1 < argv.length) {
      opts.theme = argv[++i];
    } else if (arg === "--background" && i + 1 < argv.length) {
      opts.background = argv[++i];
    } else if (arg === "--scale" && i + 1 < argv.length) {
      opts.scale = Number(argv[++i]);
    } else if (arg === "--config" && i + 1 < argv.length) {
      opts.config = resolve(argv[++i]);
    } else if (arg === "--puppeteer" && i + 1 < argv.length) {
      opts.puppeteer = resolve(argv[++i]);
    } else if (arg === "--width" && i + 1 < argv.length) {
      opts.width = Number(argv[++i]);
    } else if (!arg.startsWith("-")) {
      positional.push(arg);
    } else {
      console.error(`Unknown option: ${arg}`);
      process.exit(1);
    }
    i++;
  }

  if (positional.length < 2) {
    console.error("Error: Both <input> and <output> are required.\n");
    printHelp();
    process.exit(1);
  }

  return { input: resolve(positional[0]), output: resolve(positional[1]), ...opts };
}

// ---------------------------------------------------------------------------
// Mermaid block extraction from Markdown
// ---------------------------------------------------------------------------

function extractMermaidBlocks(markdownContent) {
  const blocks = [];
  const regex = /```mermaid\s*\n([\s\S]*?)```/g;
  let match;
  while ((match = regex.exec(markdownContent)) !== null) {
    blocks.push(match[1].trim());
  }
  return blocks;
}

// ---------------------------------------------------------------------------
// mmdc invocation
// ---------------------------------------------------------------------------

function resolveNpxPath() {
  // Prefer global mmdc if available; fall back to npx
  try {
    execFileSync("mmdc", ["--version"], { stdio: "pipe" });
    return "mmdc";
  } catch {
    return null; // will use npx
  }
}

function runMmdc(inputPath, outputPath, opts) {
  const args = [
    "-i", inputPath,
    "-o", outputPath,
    "-t", opts.theme,
    "-b", opts.background,
    "--scale", String(opts.scale),
    "-w", String(opts.width),
  ];

  if (opts.config) {
    args.push("-c", opts.config);
  }
  if (opts.puppeteer) {
    args.push("-p", opts.puppeteer);
  }

  const mmdcBin = resolveNpxPath();

  if (mmdcBin) {
    execFileSync(mmdcBin, args, { stdio: opts.quiet ? "pipe" : "inherit" });
  } else {
    // Use npx to auto-install and run mmdc
    const npxArgs = ["--yes", "@mermaid-js/mermaid-cli", ...args];
    const npxCmd = process.platform === "win32" ? "npx.cmd" : "npx";
    execFileSync(npxCmd, npxArgs, { stdio: opts.quiet ? "pipe" : "inherit" });
  }
}

// ---------------------------------------------------------------------------
// Temp file helpers
// ---------------------------------------------------------------------------

function tempFile(ext) {
  const id = randomBytes(8).toString("hex");
  return join(tmpdir(), `mermaid-export-${id}${ext}`);
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const inputExt = extname(opts.input).toLowerCase();

  if (!existsSync(opts.input)) {
    console.error(`Error: Input file not found: ${opts.input}`);
    process.exit(1);
  }

  const content = readFileSync(opts.input, "utf8");

  // Determine export format
  const outputExt = extname(opts.output).toLowerCase();
  const format = opts.format || (outputExt ? outputExt.slice(1) : "png");
  const validFormats = ["png", "svg", "pdf"];
  if (!validFormats.includes(format)) {
    console.error(`Error: Unsupported format "${format}". Use: ${validFormats.join(", ")}`);
    process.exit(1);
  }

  if (inputExt === ".md" || inputExt === ".markdown") {
    // Markdown mode: extract all mermaid blocks
    const blocks = extractMermaidBlocks(content);
    if (blocks.length === 0) {
      console.error("Error: No ```mermaid blocks found in the Markdown file.");
      process.exit(1);
    }

    // Output must be a directory
    const outDir = opts.output;
    mkdirSync(outDir, { recursive: true });

    if (!opts.quiet) {
      console.log(`Found ${blocks.length} diagram(s) in ${basename(opts.input)}`);
    }

    for (let i = 0; i < blocks.length; i++) {
      const tmpInput = tempFile(".mmd");
      const outFile = join(outDir, `diagram-${i + 1}.${format}`);
      try {
        writeFileSync(tmpInput, blocks[i], "utf8");
        runMmdc(tmpInput, outFile, { ...opts, format });
        if (!opts.quiet) {
          console.log(`  ✓ ${basename(outFile)}`);
        }
      } finally {
        if (existsSync(tmpInput)) unlinkSync(tmpInput);
      }
    }
  } else {
    // Single .mmd file mode
    const outFile = outputExt ? opts.output : `${opts.output}.${format}`;
    mkdirSync(dirname(outFile), { recursive: true });
    runMmdc(opts.input, outFile, { ...opts, format });
    if (!opts.quiet) {
      console.log(`✓ ${basename(outFile)}`);
    }
  }
}

main();
