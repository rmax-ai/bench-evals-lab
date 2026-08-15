import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

interface EvalConfig {
  name: string;
  models: string[];
  metrics: Record<string, string>;
}

interface Summary {
  name: string;
  models: string[];
  timestamp: string;
  metrics: Record<string, number | null>;
}

const configPath = new URL("../config/default.json", import.meta.url);
const config = JSON.parse(await readFile(configPath, "utf8")) as EvalConfig;
const timestamp = new Date();
const date = timestamp.toISOString().slice(0, 10);
const slug = config.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "eval";
const resultsDir = join("results", `${date}-${slug}`);

const summary: Summary = {
  name: config.name,
  models: config.models,
  timestamp: timestamp.toISOString(),
  metrics: Object.fromEntries(Object.keys(config.metrics).map((metric) => [metric, null])),
};

await mkdir(resultsDir, { recursive: true });
const summaryPath = join(resultsDir, "summary.json");
await writeFile(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");

console.log(`API_KEY: ${process.env.API_KEY === undefined ? "unset" : "set"}`);
console.log(summaryPath);
