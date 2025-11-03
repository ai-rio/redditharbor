# RedditHarbor Git Worktree Setup

This repository uses Git worktrees to maintain isolated development environments following Git Flow best practices.

## Worktree Structure

```
/home/carlos/projects/redditharbor/
├── develop                    # Main working directory (develop branch)
├── worktrees/
│   ├── master/               # Production branch (protected)
│   └── streamlit/            # Streamlit dashboard development
└── .git/                     # Main git repository
```

## Branch Types & Usage

### Main Repository (Current Directory)
- **Branch**: `develop`
- **Purpose**: Integration branch for features
- **Usage**: General development, merging completed features

### Worktree: `worktrees/master/`
- **Branch**: `master`
- **Purpose**: Production-ready code (protected)
- **Usage**: View production state, create hotfixes

### Worktree: `worktrees/streamlit/`
- **Branch**: `streamlit-dashboard`
- **Purpose**: Streamlit app development
- **Usage**: Isolated Streamlit dashboard development

## Workflow Commands

### Switch Between Worktrees
```bash
# Main develop branch
cd /home/carlos/projects/redditharbor

# Production branch
cd /home/carlos/projects/redditharbor/worktrees/master

# Streamlit development
cd /home/carlos/projects/redditharbor/worktrees/streamlit
```

### Create New Feature Branch
```bash
cd /home/carlos/projects/redditharbor
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
git push -u origin feature/your-feature-name
```

### Work With Streamlit Dashboard
```bash
cd /home/carlos/projects/redditharbor/worktrees/streamlit
# Make changes to Streamlit app
git add .
git commit -m "feat(streamlit): add dashboard feature"
git push origin streamlit-dashboard
```

### Merge Feature to Develop
```bash
cd /home/carlos/projects/redditharbor
git checkout develop
git pull origin develop
git merge --no-ff feature/your-feature-name
git push origin develop
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

## Best Practices

1. **Isolated Development**: Each worktree maintains its own working directory but shares the same git repository
2. **Protected Branches**: Never commit directly to master/develop from worktrees
3. **Feature Branches**: Always create feature branches from develop
4. **Streamlit Development**: Use the dedicated streamlit worktree for dashboard work
5. **Clean Working Directory**: Each worktree can have different uncommitted changes independently

## Current Branch Status

- **develop**: Latest integration branch (current directory)
- **master**: Production state at commit 10bf4d6
- **streamlit-dashboard**: Dashboard development at commit ca4867d

## Adding New Worktrees

To create a new worktree for a specific branch:

```bash
cd /home/carlos/projects/redditharbor
git worktree add worktrees/branch-name branch-name
```

## Cleaning Up Worktrees

When a worktree is no longer needed:

```bash
git worktree remove worktrees/branch-name
```

## Git Flow Integration

This setup follows Git Flow conventions:
- Features branch from `develop`, merge back to `develop`
- Releases branch from `develop`, merge to `master` and `develop`
- Hotfixes branch from `master`, merge to `master` and `develop`

The worktree structure allows you to work on multiple branches simultaneously without losing context or stashing changes.