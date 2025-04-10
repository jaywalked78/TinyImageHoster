# Changelog

All notable changes to the TinyImageHoster project will be documented in this file.

## [2.0.0] - 2025-04-10

### Added
- Parallel image processing using ThreadPoolExecutor
- Asynchronous I/O with aiohttp and asyncio
- Batch processing for optimized performance
- Real-time progress tracking with tqdm progress bars
- Smart environment variable handling via .env file
- Support for relative path resolution via FRAME_BASE_DIR
- Enhanced verbose debugging with detailed progress information
- Support for custom worker count and batch size configuration
- Command-line arguments for fine-tuning performance
- Detailed performance metrics during loading process

### Changed
- Completely rewrote image loading logic for parallel processing
- Restructured directory handling for better path resolution
- Improved error handling with better error messages
- Enhanced JSON output with more detailed information
- Server startup procedure to ensure proper environment variables
- Optimized HTTP requests to only verify headers instead of downloading entire images

### Fixed
- Issue with server startup in virtual environments
- Path resolution problems with relative directories
- Proper error handling when directories don't exist
- Improved virtual environment detection and activation

### Performance
- Reduced loading time from ~10 minutes to under 2 seconds for typical directories
- Improved memory usage through streaming responses
- Reduced CPU usage by optimizing HTTP requests

## [1.0.0] - 2023-10-01

### Initial Release
- Basic image server functionality
- Sequential image loading
- RESTful API for directory management
- Auto-unload timeout feature
- Simple command-line interface
- Support for loading directories and generating URLs 