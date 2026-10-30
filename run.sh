#!/bin/bash

TODAY=$(date +%Y-%m-%d)

pixi run bot >> "$PWD/log-$TODAY.log" 2>&1
