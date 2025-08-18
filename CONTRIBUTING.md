# Contributing to NVAITC APS Project Demos

Welcome students! This guide explains how to contribute your projects to this repository.

## For External Students

### 1. Fork the Repository
1. Click the "Fork" button on the main repository page
2. This creates your own copy of the repository

### 2. Clone Your Fork
```bash
git clone https://github.com/YOUR-USERNAME/nvaitc-aps-project-demos.git
cd nvaitc-aps-project-demos
```

### 3. Create Your Project
1. Create a new folder in `projects/`:
   ```bash
   mkdir projects/your-project-name
   ```

2. Follow the project structure:
   ```
   projects/your-project-name/
   ├── README.md          # Project description, setup, usage
   ├── requirements.txt   # Python dependencies (if applicable)
   ├── src/              # Source code
   ├── notebooks/        # Jupyter notebooks (if any)
   └── data/            # Sample data (keep it small!)
   ```

### 4. Project README Template
Your project README.md should include:
- Project title and description
- Hardware/software requirements
- Installation instructions
- Usage examples
- Expected results
- Credits and acknowledgments

### 5. Submit Your Work
1. Commit your changes:
   ```bash
   git add .
   git commit -m "Add [project-name]: Brief description"
   ```

2. Push to your fork:
   ```bash
   git push origin main
   ```

3. Create a Pull Request:
   - Go to your fork on GitHub
   - Click "Pull Request"
   - Provide a clear description

## Guidelines

### DO:
- ✅ Keep projects self-contained in their folder
- ✅ Include clear documentation
- ✅ Test your setup instructions
- ✅ Use relative paths
- ✅ Include a requirements.txt or environment.yml
- ✅ Credit all team members and supervisors

### DON'T:
- ❌ Upload large datasets (>50MB) - use links instead
- ❌ Include sensitive information or credentials
- ❌ Modify other projects
- ❌ Use absolute paths
- ❌ Submit incomplete or non-working code

## Code Review Process
1. NVIDIA team will review your PR
2. We may request changes or clarifications
3. Once approved, your project will be merged
4. Your contribution will be part of the official repository!

## Need Help?
- Check existing projects for examples
- Open an issue for questions
- Contact your NVIDIA supervisor

## License
By contributing, you agree that your contributions will be licensed under the same license as this repository (Apache 2.0). 