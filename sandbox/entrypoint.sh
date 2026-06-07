#!/bin/sh
# SwarmForge Sandbox — keeps container alive for exec-based usage
echo "🔒 SwarmForge Sandbox ready."
echo "   This container runs tests, security scans, and benchmarks."
echo "   Use docker exec to interact."
exec tail -f /dev/null
