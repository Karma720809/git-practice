import fs from "node:fs/promises";
import path from "node:path";
import * as dotenv from "dotenv";

dotenv.config();

const ZHIPU_API_KEY = process.env.ZHIPU_API_KEY;
const REMOVE_BG_API_KEY = process.env.REMOVE_BG_API_KEY;

if (!ZHIPU_API_KEY || !REMOVE_BG_API_KEY) {
  console.error("Missing keys");
  process.exit(1);
}

const symbols = [
  { name: "logo", query: "SpaceX style sleek silver rocket, clean, high-tech" },
  { name: "cart", query: "SpaceX style sleek silver shopping cart, glowing minimalistic, high-tech" },
  { name: "user", query: "SpaceX style futuristic astronaut helmet user profile, minimalistic, high-tech" }
];

const OUTPUT_DIR = "/Users/karma/Antigravity/rocket-shop/public";

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

async function generateImageWithZhipu(symbol) {
  const prompt = `A premium, ultra-high-resolution 3D icon of a modern minimalist ${symbol}, perfectly isolated on a pure white background. The subject is made of beautiful, smooth, slightly glossy white plastic and metallic chrome accents. Professional, soft studio lighting with a clean, smooth drop shadow. Rendered in 8k, Octane Render style, flawless and immaculate material surface. The perspective is a clean isometric overhead view, designed specifically as a high-quality UI asset. Pure white background only. No clutter.`;
  const response = await fetch("https://open.bigmodel.cn/api/paas/v4/images/generations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${ZHIPU_API_KEY}`,
    },
    body: JSON.stringify({ model: "cogview-3-flash", prompt: prompt }),
  });
  if (!response.ok) throw new Error(await response.text());
  const data = await response.json();
  const imgResponse = await fetch(data.data[0].url);
  return await imgResponse.blob();
}

async function run() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });
  for (const item of symbols) {
    console.log(`Generating ${item.name}.png...`);
    try {
      const imgBlob = await generateImageWithZhipu(item.query);
      const noBgBuffer = await removeBg(imgBlob);
      await fs.writeFile(path.join(OUTPUT_DIR, `${item.name}.png`), Buffer.from(noBgBuffer));
      console.log(`Saved ${item.name}.png`);
    } catch (e) {
      console.error(`Error on ${item.name}:`, e.message);
    }
  }
}

run();
