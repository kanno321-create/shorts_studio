#!/usr/bin/env bash
# GIT_ASKPASS helper — Phase 8 Wave 1 Pitfall 2 avoidance.
# Returns $GITHUB_TOKEN so `git push` authenticates without embedding credentials in URL.
echo "$GITHUB_TOKEN"
