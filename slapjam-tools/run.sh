#!/bin/sh
# SPDX-License-Identifier: Apache-2.0
# slapjam-tools-v1: collect Slapjam (AI-required itch.io jam) results + public tools-checklist answers,
# then summarise. Made with AI agents for MV2 of Munim, Inc. Predictions: PREREGISTRATION.md (run folder).
set -u
O=/out
cd /work
echo "== unit"
python -m unittest -v test_collect > $O/unittest.log 2>&1
echo "unit exit=$?"; tail -n 3 $O/unittest.log
echo "== collect"
date -u +%Y-%m-%dT%H:%M:%SZ > $O/collect-start.txt
timeout 3600 python collect.py --out $O --delay 2.5 > $O/collect.log 2>&1
echo "collect exit=$?"; tail -n 8 $O/collect.log
date -u +%Y-%m-%dT%H:%M:%SZ > $O/collect-end.txt
echo "== analyze"
python analyze.py $O/entries.csv > $O/analysis.txt 2>&1
echo "analyze exit=$?"; cat $O/analysis.txt
