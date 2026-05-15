import { defineNitroConfig } from "nitro/config";

export default defineNitroConfig({
  // Build Vercel-native output so routes are served by server functions.
  preset: "vercel",
});
