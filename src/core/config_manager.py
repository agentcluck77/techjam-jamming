"""
Configuration Manager for Lawyer Agent System Prompts
Loads configurable system prompts from knowledge base
"""
import os
from typing import Optional

# Configuration storage paths
CONFIG_DIR = "data/config"
SYSTEM_PROMPT_FILE = f"{CONFIG_DIR}/system_prompt.md"
KNOWLEDGE_BASE_FILE = f"{CONFIG_DIR}/knowledge_base.md"

def get_system_prompt() -> str:
    """
    Get current system prompt from configuration
    NO FALLBACKS - uses exactly what's configured
    
    Returns:
        System prompt content from knowledge base configuration
    """
    if not os.path.exists(SYSTEM_PROMPT_FILE):
        raise RuntimeError(f"System prompt not found at {SYSTEM_PROMPT_FILE}. Please create the file with your system prompt configuration.")
    
    with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read().strip()

def get_knowledge_base() -> str:
    """
    Get current knowledge base from configuration
    NO FALLBACKS - uses exactly what's configured
    
    Returns:
        Knowledge base content from knowledge base configuration
    """
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    else:
        # Initialize with default only on first run
        default_kb = get_default_knowledge_base()
        with open(KNOWLEDGE_BASE_FILE, 'w', encoding='utf-8') as f:
            f.write(default_kb)
        return default_kb

def get_default_system_prompt() -> str:
    """DEPRECATED: Default system prompt - use system_prompt.md instead"""
    raise RuntimeError("Default system prompt deprecated. System prompt must be configured in data/config/system_prompt.md")

def get_default_knowledge_base() -> str:
    """Get default knowledge base content"""
    return """# TikTok Terminology

## Core Platform Terms
- **ASL** = American Sign Language
- **FYP** = For You Page (personalized recommendation feed)
- **LIVE** = live streaming feature
- **algo** = algorithm (recommendation system)

## Content Features
- **duet** = collaborative video feature allowing response videos
- **stitch** = video response feature for remixing content
- **sound sync** = audio synchronization feature
- **green screen** = background replacement feature
- **beauty filter** = appearance enhancement filter
- **AR effects** = augmented reality effects

## Creator & Commerce
- **Creator Fund** = monetization program for content creators
- **creator marketplace** = brand partnership platform
- **TikTok Shop** = e-commerce integration platform
- **branded content** = sponsored content feature

## Business & Analytics
- **pulse** = analytics dashboard for creators and businesses
- **spark ads** = advertising platform for businesses
- **brand takeover** = full-screen advertisement format
- **top view** = premium ad placement option

## Feature Components
- **jellybean** = individual feature component within the platform
- **hashtag challenge** = trending challenge campaign format"""