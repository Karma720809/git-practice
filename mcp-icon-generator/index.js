#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "node:fs/promises";
import * as dotenv from "dotenv";

dotenv.config();

const ZHIPU_API_KEY = process.env.ZHIPU_API_KEY;
const REMOVE_BG_API_KEY = process.env.REMOVE_BG_API_KEY;

if (!REMOVE_BG_API_KEY) {
  console.error("Missing REMOVE_BG_API_KEY in environment");
  process.exit(1);
}

// 1. Create a standard MCP server instance
const server = new Server(
  {
    name: "mcp-icon-generator",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Helper function: Use remove.bg API to remove background
async function removeBg(blob) {
  const formData = new FormData();
  formData.append("size", "auto");
  formData.append("image_file", blob);

  const response = await fetch("https://api.remove.bg/v1.0/removebg", {
    method: "POST",
    headers: { "X-Api-Key": REMOVE_BG_API_KEY },
    body: formData,
  });

  if (response.ok) {
    return await response.arrayBuffer();
  } else {
    const errorText = await response.text();
    throw new Error(`Remove.bg Error ${response.status}: ${response.statusText} - ${errorText}`);
  }
}

// Helper function: Use Zhipu AI to generate an image
async function generateImageWithZhipu(symbol) {
  if (!ZHIPU_API_KEY) {
    throw new Error("Missing ZHIPU_API_KEY in environment. Please add it to your .env file.");
  }

  // The premium prompt optimized for high-quality white-background icons
  const prompt = `A premium, ultra-high-resolution 3D icon of a modern minimalist ${symbol}, perfectly isolated on a pure white background. The subject is made of beautiful, smooth, slightly glossy white plastic and metallic chrome accents, featuring a very subtle modern logo. Professional, soft studio lighting with a clean, smooth drop shadow. Rendered in 8k, Octane Render style, flawless and immaculate material surface. The perspective is a clean isometric overhead view, designed specifically as a high-quality UI asset. Pure white background only. No clutter.`;

  const response = await fetch("https://open.bigmodel.cn/api/paas/v4/images/generations", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${ZHIPU_API_KEY}`,
    },
    body: JSON.stringify({
      model: "cogview-3-plus",
      prompt: prompt
    }),
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Zhipu AI API error: ${err}`);
  }

  const data = await response.json();
  const imageUrl = data.data[0].url;
  
  // Download the generated image
  const imgResponse = await fetch(imageUrl);
  if (!imgResponse.ok) {
    throw new Error(`Failed to download image from Zhipu`);
  }
  return await imgResponse.blob();
}

// 2. Handlers: Registering Tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "generate_transparent_icon",
        description: "Generates a premium 3D icon for a specific symbol, removes its background, and saves it locally.",
        inputSchema: {
          type: "object",
          properties: {
            symbol: {
              type: "string",
              description: "The object or symbol to create an icon for (e.g., 'rocket', 'wallet', 'credit card')",
            },
            outputPath: {
              type: "string",
              description: "Optional local file path to save the resulting PNG image to. Defaults to ./{symbol}_icon.png.",
            }
          },
          required: ["symbol"],
        },
      },
    ],
  };
});

// 3. Handlers: Executing Tool Logic
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name !== "generate_transparent_icon") {
    throw new Error(`Unknown tool: ${request.params.name}`);
  }

  const symbol = request.params.arguments?.symbol;
  let outputPath = request.params.arguments?.outputPath;
  if (!outputPath) {
    const safeSymbol = symbol.replace(/\s+/g, "_");
    outputPath = `./${safeSymbol}_icon.png`;
  }

  try {
     // Step 1: Generate Image using Zhipu AI (CogView)
    const sourceImageBlob = await generateImageWithZhipu(symbol);

    // Step 2: Remove background using remove.bg API
    const transparentImageBuffer = await removeBg(sourceImageBlob);

    // Step 3: Save to disk
    await fs.writeFile(outputPath, Buffer.from(transparentImageBuffer));

    return {
      content: [
        {
          type: "text",
          text: `Successfully generated icon for '${symbol}' with transparent background.\nSaved at: ${outputPath}`,
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error generating icon: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// 4. Start the server using stdio transport
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Icon Generator Server running on stdio");
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
