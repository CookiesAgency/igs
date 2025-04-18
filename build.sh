#!/bin/bash

echo "▶ Installing Node dependencies"
npm install

echo "▶ Installing Playwright Browsers"
npx playwright install --with-deps