import fg from "fast-glob";
import { promises as fs } from "fs";
import { createHash } from "crypto";
import path from "path";

export async function scanDatabases(rootDir, includeExts, ignoreDirs) {
  const patterns = includeExts.map(ext => "**/*" + ext);
  const ignore = ignoreDirs.map(d => "**/" + d + "/**");
  const files = await fg(patterns, {
    cwd: rootDir,
    ignore,
    onlyFiles: true,
    dot: false,
    absolute: true,
    followSymbolicLinks: false
  });

  const out = [];
  for (const f of files) {
    try {
      const real = await fs.realpath(f);
      const st = await fs.stat(real);
      const h = createHash("sha256").update(real).digest("hex").slice(0, 12);
      out.push({
        id: h,
        path: real,
        size: st.size,
        mtimeMs: st.mtimeMs,
        project: inferProject(real, rootDir),
        tags: inferTags(real)
      });
    } catch {
      // ignore inaccessible entries
    }
  }
  return out;
}

function inferProject(filePath, rootDir) {
  const rel = path.relative(rootDir, filePath);
  return rel.split(path.sep)[0] || "";
}

function inferTags(filePath) {
  const lower = filePath.toLowerCase();
  const tags = [];
  if (lower.includes("pynance") || lower.includes("py-nance")) tags.push("pynance");
  if (lower.includes(path.sep + "finance" + path.sep)) tags.push("finance");
  if (lower.includes("ai-tools") || lower.includes("ai_tools")) tags.push("ai-tools");
  return tags;
}
