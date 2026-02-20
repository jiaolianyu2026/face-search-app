---
inclusion: always
---

# Product Overview

Face Recognition Search Application - a web application that enables users to upload images containing faces, detect facial features, and search for matching faces across a specified folder of images.

## Core Functionality

- Upload images (JPEG, PNG, WebP) up to 10MB
- Detect faces and extract 128-dimensional feature vectors
- Search folders for matching faces using similarity threshold (default 0.6)
- Track search progress with real-time updates
- Cache face features for performance optimization

## Key Workflows

1. Upload image → Detect faces → Select target face
2. Start search task → Monitor progress → Review matches
3. Cancel long-running searches gracefully

## Data Models

- Face: Detected face with bounding box and 128D feature vector
- SearchTask: Asynchronous search with status tracking (pending/running/completed/cancelled)
- Match: Search result with similarity score and location
- Progress: Real-time progress tracking for long operations
