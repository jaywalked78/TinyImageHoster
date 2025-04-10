# TinyImageHoster

A high-performance, lightweight image server for hosting local images with HTTP URLs. Perfect for machine learning workflows that require image URLs like multimodal AI models.

## Features

- Serve images from any local directory with blazing-fast loading
- Parallel processing with ThreadPoolExecutor and async I/O
- Batch processing to optimize performance
- Interactive progress bars for real-time loading feedback
- Load and unload directories on demand
- RESTful API for directory management
- Auto-unload timeout (configurable in `.env` file)
- Environment variable support for flexible configuration
- Support for absolute and relative path resolution

## Quick Start

1. Clone this repository:
```bash
git clone https://github.com/yourusername/TinyImageHoster.git
cd TinyImageHoster
```

2. Create a virtual environment:
```bash
python3 -m venv tinyHosterVenv
```

3. Copy and configure the environment variables:
```bash
cp .env.example .env
# Edit .env to set your preferences and paths
```

4. Load images from a directory:
```bash
./run_with_progress.sh /path/to/your/images
```

5. Use the image URLs in your application:
```
http://localhost:7779/images/<image_name>
```

6. When finished, unload the directory:
```bash
./unload_directory.sh
```

## Performance

The optimized image loader (`load_folder_v2.py`) offers significant performance improvements:

- **Parallel Processing**: Uses ThreadPoolExecutor to load multiple images concurrently
- **Asynchronous I/O**: Implements async processing with asyncio and aiohttp
- **Batch Processing**: Processes images in configurable batches for better throughput
- **Smart Header Checking**: Verifies image availability without downloading full content
- **Real-time Progress Tracking**: Shows actual loading progress with tqdm progress bars

Example performance gains:
- Original sequential loader: ~10 minutes for a typical directory
- Optimized parallel loader: Under 2 seconds for the same directory (up to 300x faster)

## Configuration

### Environment Variables

The application uses the following environment variables (defined in `.env`):

- `IMAGE_SERVER_PORT`: The port to run the image server on (default: 7779)
- `IMAGE_SERVER_HOST`: The host to bind the server to (default: 0.0.0.0)
- `IMAGE_SERVER_TIMEOUT`: Auto-unload timeout in minutes (default: 30, 0 = disabled)
- `FRAME_BASE_DIR`: Base directory for resolving relative paths

### Command-Line Arguments

The `run_with_progress.sh` script accepts the following arguments:

```bash
./run_with_progress.sh <directory_path> [options]
# or
./run_with_progress.sh --dir=<directory_path> [options]
```

Additional options:
- `--server`: Custom server URL (default: http://localhost:7779)
- `--output`: Directory to save JSON output (default: ~/Documents/LightweightImageServer/output/json)
- `--unload`: Unload directory when done
- `--unload-first`: Unload any previous directories before loading new ones
- `--timeout`: Set timeout in minutes (0 to disable)
- `--name`: Custom name for the output JSON file
- `--workers`: Number of concurrent workers (default: 10)
- `--batch-size`: Batch size for image uploads (default: 20)

## Scripts

The following scripts are provided:

- `run_with_progress.sh`: Main script for loading images with real-time progress tracking
- `load_folder_v2.py`: Optimized Python script with parallel/async image loading
- `persistent_run.sh`: Runs the image server in persistent mode
- `unload_directory.sh`: Unloads the current directory from the server

## API Endpoints

The server provides the following endpoints:

- `GET /`: Get information about the currently loaded directory
- `POST /load-directory`: Load a directory of images
- `GET /images/{image_name}`: Get a specific image
- `POST /unload`: Unload the current directory
- `GET /timeout`: Get current timeout settings
- `POST /timeout/{minutes}`: Set a new timeout value

## Output

When loading images, a JSON file is generated in the output directory with:
- URLs for all images
- Server information
- Timeout settings
- Directory information

Example:
```json
{
  "success": true,
  "directory": "/path/to/your/images",
  "timestamp": "2023-11-15 14:30:00",
  "message": "Generated URLs for 150 images",
  "count": 150,
  "image_urls": [
    "http://localhost:7779/images/image1.jpg",
    "http://localhost:7779/images/image2.jpg",
    ...
  ],
  "timeout_minutes": 30,
  "auto_unload_at": "2023-11-15 15:00:00",
  "time_remaining": "29m 45s"
}
```

## Requirements

- Python 3.7+
- Dependencies (installed automatically):
  - tqdm
  - aiohttp
  - aiofiles
  - python-dotenv
  - PIL (optional, for image dimensions)

## License

MIT 