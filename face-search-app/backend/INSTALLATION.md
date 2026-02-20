# Installation Guide

## Prerequisites

Before installing the Python dependencies, you need to install CMake, which is required for building the `dlib` library.

### Installing CMake

#### Windows
1. Download CMake from https://cmake.org/download/
2. Run the installer
3. **Important**: During installation, select "Add CMake to the system PATH for all users" or "Add CMake to the system PATH for the current user"
4. Verify installation by opening a new terminal and running:
   ```
   cmake --version
   ```

#### Linux (Ubuntu/Debian)
```bash
sudo apt install cmake
```

#### Linux (RedHat/CentOS)
```bash
sudo yum install cmake
```

#### macOS
```bash
brew install cmake
```

## Installing Python Dependencies

Once CMake is installed:

1. Activate the virtual environment:
   ```bash
   # Windows
   venv\Scripts\activate
   
   # Unix/MacOS
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Troubleshooting

### CMake Not Found
If you get a "CMake is not installed" error:
- Make sure CMake is in your PATH
- Close and reopen your terminal after installing CMake
- Run `cmake --version` to verify it's accessible

### dlib Build Fails
If dlib fails to build:
- Ensure you have a C++ compiler installed (Visual Studio on Windows, gcc/g++ on Linux)
- On Windows, you may need to install Visual Studio Build Tools

### Alternative: Pre-built Wheels
If building from source fails, you can try installing pre-built wheels:
```bash
pip install dlib-binary
```

Note: This is an unofficial package and may not be as up-to-date as the official dlib.
