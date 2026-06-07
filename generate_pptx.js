const pptxgen = require('pptxgenjs');

let pres = new pptxgen();

// Slide 1: Title
let slide1 = pres.addSlide();
slide1.addText('SwarmForge Ultimate', { x: 1, y: 1, w: 8, h: 1, fontSize: 44, bold: true, align: 'center' });
slide1.addText('Autonomous Multi-Agent Software Development Pipeline\n\n(Add Title Slide Image Here)', { x: 1, y: 2.5, w: 8, h: 2, fontSize: 24, align: 'center' });

// Slide 2: What is SwarmForge
let slide2 = pres.addSlide();
slide2.addText('What is SwarmForge?', { x: 0.5, y: 0.5, w: 9, h: 1, fontSize: 36, bold: true });
slide2.addText('SwarmForge Ultimate is an advanced, multi-agent AI pipeline designed to act as a fully autonomous software engineering team. It doesn\'t just generate code; it architects, builds, reviews, tests, and secures full applications in real-time.\n\n(Add Image Here: e.g., A screenshot of the SwarmForge Dashboard)', { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 20 });

// Slide 3: The Problem It Solves
let slide3 = pres.addSlide();
slide3.addText('The Problem It Solves', { x: 0.5, y: 0.5, w: 9, h: 1, fontSize: 36, bold: true });
slide3.addText('• Context Loss: Traditional LLMs lose track of complex architectures.\n• Lack of Verification: Generated code often contains bugs or security flaws.\n• Workflow Friction: Switching between chat interfaces, editors, and terminals breaks developer flow.\n\n(Add Image Here: e.g., chaotic nature of standard AI chat vs pipeline)', { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 20, bullet: true });

// Slide 4: Core Architecture
let slide4 = pres.addSlide();
slide4.addText('Core Architecture & Agent Roles', { x: 0.5, y: 0.5, w: 9, h: 1, fontSize: 36, bold: true });
slide4.addText('Our pipeline is divided into specialized autonomous agents:\n1. Meta-Agent (The Manager): Plans the architecture and delegates tasks.\n2. Coder Agents (Frontend, Backend, DB): Write the actual code.\n3. Reviewer & QA Agents: Inspect code for quality and write unit tests.\n4. Security & Performance Agents: Scan for vulnerabilities.\n\n(Add Image Here: e.g., An architectural diagram)', { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 20 });

// Slide 5: Key Features
let slide5 = pres.addSlide();
slide5.addText('Key Features', { x: 0.5, y: 0.5, w: 9, h: 1, fontSize: 36, bold: true });
slide5.addText('• The Blackboard System: Shared memory (Redis+Postgres) for all agents.\n• Quality Gates: Code must pass threshold scores for coverage, security, and performance.\n• Interactive Workspace: Integrated Monaco editor and PTY Sandbox Terminal.\n\n(Add Image Here: e.g., Screenshot of Workspace tab)', { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 20, bullet: true });

// Slide 6: Tech Stack
let slide6 = pres.addSlide();
slide6.addText('Tech Stack', { x: 0.5, y: 0.5, w: 9, h: 1, fontSize: 36, bold: true });
slide6.addText('• Backend: FastAPI, PostgreSQL, Redis, Asyncio, LiteLLM\n• Frontend: React, Vite, Zustand, xterm.js, Monaco\n• Infrastructure: Docker Compose, NGINX, Prometheus, Grafana\n• AI Models: Groq (Llama-3), OpenRouter (DeepSeek R1, Qwen 2.5 Coder)\n\n(Add Image Here: e.g., Collage of logos)', { x: 0.5, y: 1.5, w: 9, h: 3, fontSize: 20, bullet: true });

pres.writeFile({ fileName: 'SwarmForge_Presentation.pptx' }).then(() => {
    console.log('Done!');
});
