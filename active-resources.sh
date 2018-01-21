#!/usr/bin/env bash
gunicorn  -w 4 -b 0.0.0.0:5000 active-resources:app --log-level DEBUG --timeout 300
