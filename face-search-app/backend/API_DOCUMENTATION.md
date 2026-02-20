# API Documentation

## Image Upload API

### POST /api/upload

Upload an image file for face recognition processing.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body:
  - `file`: Image file (JPEG, PNG, or WebP format)

**Validation:**
- File format must be JPEG (.jpg, .jpeg), PNG (.png), or WebP (.webp)
- File size must not exceed 10MB
- File must be present in the request

**Response (Success - 200):**
```json
{
  "success": true,
  "imageId": "550e8400-e29b-41d4-a716-446655440000",
  "previewUrl": "/api/preview/550e8400-e29b-41d4-a716-446655440000",
  "error": null
}
```

**Response (Error - 400):**
```json
{
  "success": false,
  "imageId": null,
  "previewUrl": null,
  "error": "Unsupported file format. Supported formats: .jpg, .jpeg, .png, .webp"
}
```

**Response (File Too Large - 413):**
```json
{
  "success": false,
  "imageId": null,
  "previewUrl": null,
  "error": "File size exceeds maximum limit of 10MB"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/image.jpg"
```

**Example using Python requests:**
```python
import requests

with open('image.jpg', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)
    result = response.json()
    print(f"Image ID: {result['imageId']}")
```

---

### GET /api/preview/{imageId}

Retrieve a preview of an uploaded image.

**Request:**
- Method: `GET`
- URL Parameter: `imageId` - Unique identifier returned from upload

**Response (Success - 200):**
- Content-Type: `image/jpeg`, `image/png`, or `image/webp`
- Body: Image file data

**Response (Not Found - 404):**
```json
{
  "error": "Image not found"
}
```

**Example:**
```bash
curl http://localhost:5000/api/preview/550e8400-e29b-41d4-a716-446655440000 \
  --output preview.jpg
```

---

## Running the Server

1. Activate the virtual environment:
```bash
# Windows
backend\venv\Scripts\activate

# Linux/Mac
source backend/venv/bin/activate
```

2. Start the Flask server:
```bash
cd backend
python app.py
```

The server will start on `http://localhost:5000`

---

## Testing

Run the test suite:
```bash
python -m pytest tests/test_upload.py -v
```

Run with coverage:
```bash
python -m pytest tests/test_upload.py --cov=backend --cov-report=html
```

## Face Search API

### POST /api/search

Start a face search task to find matching faces in a folder.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "imageId": "550e8400-e29b-41d4-a716-446655440000",
  "faceId": "face-uuid-from-detection",
  "searchFolder": "/path/to/search/folder",
  "threshold": 0.6
}
```

**Parameters:**
- `imageId` (required): Unique identifier of the uploaded image
- `faceId` (required): Unique identifier of the face to search for
- `searchFolder` (required): Path to the folder to search in
- `threshold` (optional): Similarity threshold (0-1), default is 0.6

**Response (Success - 200):**
```json
{
  "taskId": "task-uuid",
  "status": "pending"
}
```

**Response (Error - 400):**
```json
{
  "error": "imageId is required"
}
```

**Response (Not Found - 404):**
```json
{
  "error": "Image not found for imageId: xxx"
}
```

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "imageId": "550e8400-e29b-41d4-a716-446655440000",
    "faceId": "face-uuid",
    "searchFolder": "/path/to/photos",
    "threshold": 0.7
  }'
```

---

### GET /api/search/{taskId}

Get the status and progress of a search task.

**Request:**
- Method: `GET`
- URL Parameter: `taskId` - Unique identifier of the search task

**Response (Success - 200):**

For pending/running tasks:
```json
{
  "taskId": "task-uuid",
  "status": "running",
  "progress": {
    "current": 15,
    "total": 100,
    "percentage": 15.0,
    "currentFile": "/path/to/current/image.jpg"
  },
  "createdAt": 1234567890.123
}
```

For completed/cancelled tasks:
```json
{
  "taskId": "task-uuid",
  "status": "completed",
  "progress": {
    "current": 100,
    "total": 100,
    "percentage": 100.0,
    "currentFile": null
  },
  "createdAt": 1234567890.123,
  "results": [
    {
      "imagePath": "/path/to/matched/image.jpg",
      "similarity": 0.85,
      "faceLocation": {
        "x": 100,
        "y": 150,
        "width": 200,
        "height": 200
      },
      "thumbnailUrl": null
    }
  ]
}
```

**Response (Not Found - 404):**
```json
{
  "error": "Search task not found: task-uuid"
}
```

**Status Values:**
- `pending`: Task is queued but not yet started
- `running`: Task is currently processing
- `completed`: Task finished successfully
- `cancelled`: Task was cancelled by user

**Example using curl:**
```bash
curl http://localhost:5000/api/search/task-uuid
```

**Example polling for completion:**
```python
import requests
import time

task_id = "task-uuid"
while True:
    response = requests.get(f'http://localhost:5000/api/search/{task_id}')
    data = response.json()
    
    print(f"Status: {data['status']}, Progress: {data['progress']['percentage']}%")
    
    if data['status'] in ['completed', 'cancelled']:
        print(f"Found {len(data['results'])} matches")
        break
    
    time.sleep(1)
```

---

### POST /api/search/{taskId}/cancel

Cancel a running search task.

**Request:**
- Method: `POST`
- URL Parameter: `taskId` - Unique identifier of the search task

**Response (Success - 200):**
```json
{
  "taskId": "task-uuid",
  "status": "cancelled",
  "message": "Search task cancelled successfully"
}
```

**Response (Not Found - 404):**
```json
{
  "error": "Search task not found: task-uuid"
}
```

**Response (Cannot Cancel - 400):**
```json
{
  "error": "Cannot cancel task with status: completed"
}
```

**Notes:**
- Only tasks with status `pending` or `running` can be cancelled
- Cancelled tasks will retain any partial results found before cancellation
- The cancellation is graceful - the current image being processed will complete

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/search/task-uuid/cancel
```

**Example using Python requests:**
```python
import requests

task_id = "task-uuid"
response = requests.post(f'http://localhost:5000/api/search/{task_id}/cancel')
result = response.json()

if response.status_code == 200:
    print(f"Task cancelled: {result['message']}")
else:
    print(f"Error: {result['error']}")
```

---

## Complete Search Workflow Example

Here's a complete example of the search workflow with progress tracking:

```python
import requests
import time

# 1. Upload an image
with open('target_face.jpg', 'rb') as f:
    files = {'file': f}
    upload_response = requests.post('http://localhost:5000/api/upload', files=files)
    image_id = upload_response.json()['imageId']

# 2. Detect faces
detect_response = requests.post(
    'http://localhost:5000/api/detect',
    json={'imageId': image_id}
)
faces = detect_response.json()['faces']
face_id = faces[0]['faceId']  # Use first detected face

# 3. Start search
search_response = requests.post(
    'http://localhost:5000/api/search',
    json={
        'imageId': image_id,
        'faceId': face_id,
        'searchFolder': '/path/to/photos',
        'threshold': 0.6
    }
)
task_id = search_response.json()['taskId']

# 4. Poll for progress
while True:
    status_response = requests.get(f'http://localhost:5000/api/search/{task_id}')
    status_data = status_response.json()
    
    progress = status_data['progress']
    print(f"Progress: {progress['current']}/{progress['total']} ({progress['percentage']:.1f}%)")
    
    if progress['currentFile']:
        print(f"Processing: {progress['currentFile']}")
    
    if status_data['status'] in ['completed', 'cancelled']:
        break
    
    time.sleep(0.5)

# 5. Get results
if status_data['status'] == 'completed':
    results = status_data['results']
    print(f"\nFound {len(results)} matching images:")
    for match in results:
        print(f"  - {match['imagePath']} (similarity: {match['similarity']:.2f})")
```

---

## Image Export API

### POST /api/export

Export (copy) matched images to a target directory.

**Request:**
- Method: `POST`
- Content-Type: `application/json`
- Body:
```json
{
  "imagePaths": [
    "/path/to/image1.jpg",
    "/path/to/image2.png",
    "/path/to/image3.webp"
  ],
  "targetFolder": "/path/to/export/folder"
}
```

**Parameters:**
- `imagePaths` (required): Array of image file paths to export
- `targetFolder` (required): Destination folder path

**Validation:**
- `imagePaths` must be a non-empty array
- `targetFolder` must exist and be a directory
- `targetFolder` must be writable

**Response (Success - 200):**
```json
{
  "successCount": 2,
  "failedCount": 1,
  "errors": [
    {
      "path": "/path/to/missing.jpg",
      "error": "Source file does not exist"
    }
  ]
}
```

**Response (Error - 400):**
```json
{
  "error": "imagePaths is required"
}
```

**Response (Not Found - 404):**
```json
{
  "error": "Target folder does not exist: /path/to/folder"
}
```

**Response (Forbidden - 403):**
```json
{
  "error": "Target folder is not writable: /path/to/folder"
}
```

**Features:**
- Files are copied with metadata preservation (timestamps, permissions)
- Automatic filename conflict resolution (adds _1, _2, etc. suffixes)
- Partial success handling (continues on individual file errors)
- Detailed error reporting for failed exports

**Example using curl:**
```bash
curl -X POST http://localhost:5000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "imagePaths": ["/photos/img1.jpg", "/photos/img2.png"],
    "targetFolder": "/exports"
  }'
```

**Example using Python requests:**
```python
import requests

response = requests.post(
    'http://localhost:5000/api/export',
    json={
        'imagePaths': [
            '/path/to/matched/image1.jpg',
            '/path/to/matched/image2.png'
        ],
        'targetFolder': '/path/to/export/folder'
    }
)

result = response.json()
print(f"Successfully exported: {result['successCount']}")
print(f"Failed: {result['failedCount']}")

if result['errors']:
    print("Errors:")
    for error in result['errors']:
        print(f"  - {error['path']}: {error['error']}")
```

**Filename Conflict Resolution:**

When a file with the same name already exists in the target folder:
- Original file: `photo.jpg` (already exists)
- First export: `photo_1.jpg`
- Second export: `photo_2.jpg`
- And so on...

The original file is never overwritten.

---

## Complete Search and Export Workflow Example

Here's a complete example combining search and export:

```python
import requests
import time

# 1. Upload an image
with open('target_face.jpg', 'rb') as f:
    files = {'file': f}
    upload_response = requests.post('http://localhost:5000/api/upload', files=files)
    image_id = upload_response.json()['imageId']

# 2. Detect faces
detect_response = requests.post(
    'http://localhost:5000/api/detect',
    json={'imageId': image_id}
)
faces = detect_response.json()['faces']
face_id = faces[0]['faceId']  # Use first detected face

# 3. Start search
search_response = requests.post(
    'http://localhost:5000/api/search',
    json={
        'imageId': image_id,
        'faceId': face_id,
        'searchFolder': '/path/to/photos',
        'threshold': 0.6
    }
)
task_id = search_response.json()['taskId']

# 4. Poll for progress
while True:
    status_response = requests.get(f'http://localhost:5000/api/search/{task_id}')
    status_data = status_response.json()
    
    progress = status_data['progress']
    print(f"Progress: {progress['current']}/{progress['total']} ({progress['percentage']:.1f}%)")
    
    if progress['currentFile']:
        print(f"Processing: {progress['currentFile']}")
    
    if status_data['status'] in ['completed', 'cancelled']:
        break
    
    time.sleep(0.5)

# 5. Get results and export
if status_data['status'] == 'completed':
    results = status_data['results']
    print(f"\nFound {len(results)} matching images:")
    for match in results:
        print(f"  - {match['imagePath']} (similarity: {match['similarity']:.2f})")
    
    # 6. Export matched images
    if results:
        image_paths = [match['imagePath'] for match in results]
        export_response = requests.post(
            'http://localhost:5000/api/export',
            json={
                'imagePaths': image_paths,
                'targetFolder': '/path/to/export/folder'
            }
        )
        
        export_result = export_response.json()
        print(f"\nExport complete:")
        print(f"  Successfully exported: {export_result['successCount']}")
        print(f"  Failed: {export_result['failedCount']}")
        
        if export_result['errors']:
            print("  Errors:")
            for error in export_result['errors']:
                print(f"    - {error['path']}: {error['error']}")
```
