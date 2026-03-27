# Git Setup Instructions

## ⚠️ Important: Git Not Currently Installed

Your system does not have Git installed. To complete version control setup, you'll need to install Git first.

## 📥 Install Git

### Windows
1. Visit [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download the latest installer
3. Run the installer with default settings
4. Restart your PowerShell or Command Prompt
5. Verify: `git --version`

### macOS
```bash
# Using Homebrew (if installed)
brew install git

# Or download from git-scm.com/download/mac
```

### Linux
```bash
# Ubuntu/Debian
sudo apt-get install git

# Fedora/RHEL
sudo dnf install git
```

## 🔐 Git Configuration

```bash
# Set your identity (required for commits)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify configuration
git config --global --list
```

## 🚀 Initialize Repository

```bash
cd c:\Users\angel\Desktop\practica1

# Initialize git
git init

# Check status
git status
```

## 📝 Make Initial Commits

### Commit 1: Project Structure
```bash
git add .gitignore package.json build/ src/ templates/ app.py
git commit -m "Initial setup: project structure and build configuration"
```

### Commit 2: Styles
```bash
git add src/styles/
git commit -m "Styles: SCSS modular architecture with 16 components"
```

### Commit 3: Scripts
```bash
git add src/scripts/ build/
git commit -m "Build: SASS compiler and watch mode scripts"
```

### Commit 4: Flask Updates
```bash
git add app.py templates/base.html
git commit -m "Config: Flask static folder configuration for dist/"
```

### Commit 5: Documentation
```bash
git add README.md MODERNIZATION.md
git commit -m "Docs: comprehensive setup and migration documentation"
```

## 🌐 Connect to GitHub

### Create Repository on GitHub

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `smartwatch-ecommerce`
3. Description: "Modern e-commerce platform for smartwatches"
4. Choose: **Public** (for portfolio) or **Private**
5. Do NOT initialize README, .gitignore, or license
6. Click "Create repository"

### Push to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/smartwatch-ecommerce.git

# Rename branch (GitHub default is 'main', we use 'master')
git branch -M master

# Push all commits
git push -u origin master

# Verify
git remote -v
git branch -a
```

## 🔄 Ongoing Workflow

### Before Making Changes
```bash
# Update from remote
git pull origin master
```

### After Making Changes
```bash
# Check what changed
git status

# Stage changes
git add <file>          # Add specific file
git add .               # Add all changes

# Commit with meaningful message
git commit -m "Feature: description of changes"

# Push to GitHub
git push origin master
```

### Create Feature Branches
```bash
# Create new branch
git checkout -b feature/add-product-filters

# Make changes and commit
# ...

# Push branch to GitHub
git push -u origin feature/add-product-filters

# Create Pull Request on GitHub website
```

## 📋 Branch Strategy

```
master (main branch)
├── feature/add-ratings
├── feature/add-search
├── bugfix/fix-cart-bug
└── docs/update-readme
```

**Best Practices:**
- Main branch: Always production-ready
- Feature branches: For new features
- Bugfix branches: For bug fixes
- Document changes in commit messages

## 🔗 Useful Git Commands

```bash
# View commit history
git log --oneline
git log --graph --all

# Undo changes
git restore <file>              # Discard changes to file
git reset HEAD~1                # Undo last commit (keep changes)
git reset --hard HEAD~1         # Undo last commit (discard changes)

# View differences
git diff                        # Changes not staged
git diff --cached               # Changes staged but not committed
git diff master <branch>        # Compare branches

# Stash changes temporarily
git stash                       # Save changes
git stash pop                   # Restore changes
git stash list                  # View all stashes

# Tags for releases
git tag v1.0.0
git push origin v1.0.0
```

## 🛡️ GitHub Security

### Personal Access Token (instead of password)

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token"
3. Select scopes: `repo`, `workflow`
4. Copy the token
5. Use token as password when pushing

### SSH Key (recommended)

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Add to GitHub
# Settings → SSH and GPG keys → New SSH key
# Paste content of ~/.ssh/id_ed25519.pub

# Update remote URL
git remote set-url origin git@github.com:YOUR_USERNAME/smartwatch-ecommerce.git
```

## 📊 GitHub Features to Explore

After pushing:
1. **README.md** - Shows on repo homepage
2. **Issues** - Track bugs and features
3. **Projects** - Kanban board for tasks
4. **Actions** - CI/CD automation
5. **Wiki** - Additional documentation
6. **Releases** - Version milestones

## 🔍 Verify Setup

```bash
# Check Git status
git status

# View remote configuration
git remote -v

# View commit log
git log --oneline -5

# View branches
git branch -a

# Verify files in staging area
git diff --cached --name-only
```

## ✅ Checklist

- [ ] Git installed and verified
- [ ] Global user name and email configured
- [ ] Local repository initialized (`git init`)
- [ ] Initial commits made
- [ ] Remote repository created on GitHub
- [ ] Local repo connected to GitHub (`git remote add origin`)
- [ ] First push completed (`git push -u origin master`)
- [ ] Repository visible on GitHub website

## 🆘 Common Issues

### "Permission denied (publickey)"
- [x] Use HTTPS instead of SSH
- [x] Generate and add SSH key to GitHub

### "fatal: not a git repository"
- [x] Run `git init` in project directory
- [x] Check you're in correct folder

### "Everything up-to-date"
- [x] Verify you made commits: `git log`
- [x] Check remote URL: `git remote -v`

## 📚 Additional Resources

- [Git Official Documentation](https://git-scm.com/doc)
- [GitHub Learning Lab](https://lab.github.com)
- [Pro Git Book (Free)](https://git-scm.com/book)
- [GitHub Guides](https://guides.github.com)

---

**Next Steps**:
1. Install Git
2. Run setup commands above
3. Push repository to GitHub
4. Share link for feedback

