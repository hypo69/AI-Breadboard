# Skill Factory

Utility package and agent skill for scaffolding, managing, and packaging AI Breadboard agent skills.

## Overview
Skill Factory provides tools to create standardized skills in `skills/<skill_name>/` and package them into distributable `.skill` files.

## Directory Structure
```
skills/skill-factory/
├── README.md             # Package documentation
├── SKILL.md              # Agent skill guidelines and triggers
└── scripts/
    ├── init_skill.py     # Skill folder scaffolding utility
    └── pack.py           # Skill packaging utility
```

## Commands
- Initialize new skill: `python skills/skill-factory/scripts/init_skill.py <name>`
- Package skill: `python skills/skill-factory/scripts/pack.py <name>`
