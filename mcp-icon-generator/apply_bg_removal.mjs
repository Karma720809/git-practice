import fs from "node:fs/promises";
import path from "node:path";
import * as dotenv from "dotenv";

dotenv.config({ path: "/Users/karma/Antigravity/mcp-icon-generator/.env" });
const REMOVE_BG_API_KEY = process.env.REMOVE_BG_API_KEY || "AtwJ7Fd8kStevit642oYFA1D";

const outDir = "/Users/karma/Antigravity/rocket-shop/public";
const images = {
  logo: "/Users/karma/.gemini/antigravity/brain/7bd3af08-9acd-4f85-b0a3-f601ad86bdcd/logo_1776170122487.png",
  cart: "/Users/karma/.gemini/antigravity/brain/7bd3af08-9acd-4f85-b0a3-f601ad86bdcd/cart_1776170138053.png",
  user: "/Users/karma/.gemini/antigravity/brain/7bd3af08-9acd-4f85-b0a3-f601ad86bdcd/user_1776170152754.png",
  hero: "/Users/karma/.gemini/antigravity/brain/7bd3af08-9acd-4f85-b0a3-f601ad86bdcd/hero_1776170169575.png"
};

async function removeBg(blob) {
  const formData = new FormData();
  formData.append("size", "auto");
  formData.append("image_file", blob);
  const response = await fetch("https://api.remove.bg/v1.0/removebg", {
    method: "POST",
    headers: { "X-Api-Key": REMOVE_BG_API_KEY },
    body: formData,
  });
  if (response.ok) return await response.arrayBuffer();
  else throw new Error(await response.text());
}

async function run() {
  await fs.mkdir(outDir, { recursive: true });
  for (const [name, imgPath] of Object.entries(images)) {
    console.log(`Processing ${name}...`);
    try {
      const buffer = await fs.readFile(imgPath);
      const blob = new Blob([buffer], { type: "image/png" });
      const noBgBuffer = await removeBg(blob);
      await fs.writeFile(path.join(outDir, `${name}.png`), Buffer.from(noBgBuffer));
      console.log(`Saved ${name}.png`);
    } catch (e) {
      console.error(`Error on ${name}:`, e.message);
    }
  }
}
run();
