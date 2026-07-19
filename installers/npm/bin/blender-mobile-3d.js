#!/usr/bin/env node
import process from "node:process";

import { main } from "../src/main.js";

const code = await main();
process.exitCode = typeof code === "number" ? code : 0;
