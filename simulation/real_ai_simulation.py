"""
Real-world simulation runner for WishlistOps using live Gemini API.

This script:
1. Prompts for Gemini API key (or accepts it via env var/stdin).
2. Uses REAL Gemini models for text and image generation.
3. Mocks Git, Discord, and Steam to simulate the rest of the workflow.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path so we can import wishlistops modules
sys.path.append(str(Path(__file__).parent.parent))

from wishlistops.models import Config, AIConfig, AnnouncementDraft
from wishlistops.ai_client import AIClient
from simulation.mock_services import MockGitRepo, MockDiscordNotifier, MockSteamPublisher, _now_iso

CONFIG_PATH = Path("wishlistops/config.json")
OUTPUT_PATH = Path("simulation/output_real")

def load_config() -> Config:
    """Load config and override with requested models."""
    if not CONFIG_PATH.exists():
        print(f"Error: Config file not found at {CONFIG_PATH}")
        sys.exit(1)
        
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    
    # Override models as requested by user
    # Note: The AIClient constructs the URL as: f"{self.base_url}/models/{self.config.model_text}:generateContent"
    # So we should provide the model name without 'models/' prefix if the client adds it, 
    # BUT the user specified 'models/gemini-flash-lite-latest'.
    # Let's check ai_client.py again. 
    # It uses: url = f"{self.base_url}/models/{self.config.model_text}:generateContent"
    # If we pass "models/gemini...", it becomes ".../models/models/gemini...".
    # However, the Google GenAI API often accepts "models/" prefix or not. 
    # To be safe and follow the user's exact string, we might need to adjust the client or just pass it.
    # Let's strip 'models/' if present to be safe with the existing client construction.
    
    raw["ai"]["model_text"] = "gemini-flash-lite-latest" # User asked for models/gemini-flash-lite-latest
    raw["ai"]["model_image"] = "imagen-4.0-generate-001" # User asked for models/imagen-4.0-generate-001
    
    # If the user REALLY wants the 'models/' prefix, we can leave it, but standard client usage usually implies just the name.
    # Given the client code: f"{self.base_url}/models/{self.config.model_text}:generateContent"
    # I will use just the name to avoid double 'models/'.
    
    cfg = Config(**raw)
    return cfg

def obtain_api_keys() -> tuple[str, str]:
    """Get API keys from user input."""
    print("\n" + "="*60)
    print("WishlistOps Real-World Simulation")
    print("="*60)
    
    print("Please enter your Gemini API Key for TEXT generation.")
    try:
        text_key = input("Text API Key: ").strip()
    except EOFError:
        sys.exit(1)

    print("\nPlease enter your Gemini API Key for IMAGE generation.")
    print("(Press Enter to use the same key as above)")
    try:
        image_key = input("Image API Key: ").strip()
    except EOFError:
        sys.exit(1)
        
    if not image_key:
        image_key = text_key
        
    if not text_key:
        print("Error: Text API Key is required.")
        sys.exit(1)
        
    return text_key, image_key

async def run_real_simulation():
    # 1. Setup
    text_key, image_key = obtain_api_keys()
    config = load_config()
    OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    
    print("\nStarting Simulation...")
    print(f"Text Model: {config.ai.model_text}")
    print(f"Image Model: {config.ai.model_image}")
    
    # 2. Mock Git
    print("\n[1/5] Simulating Git Activity...")
    repo = MockGitRepo()
    commits = repo.generate_commits(count=6)
    print(f"Generated {len(commits)} mock commits.")
    for c in commits:
        print(f"  - [{c['commit_type']}] {c['message']}")

    # 3. Real AI Generation
    print("\n[2/5] Generating Content with Gemini (Real API)...")
    
    # We need to adapt the mock commits to the format expected by AIClient (which expects 'Commit' objects usually, 
    # but let's see how we can construct the prompt manually or use the client's helper if available).
    # The AIClient.generate_text takes a prompt string.
    # We can reuse the logic from main.py's _build_ai_context, but since we can't easily import the Orchestrator instance,
    # we'll reconstruct the prompt here.
    
    commit_summaries = [f"- [{c['commit_type']}] {c['message']}" for c in commits]
    commits_text = "\n".join(commit_summaries)
    
    prompt = f"""
You are writing a Steam announcement for the game "{config.steam.app_name}".

GAME CONTEXT:
- Steam App ID: {config.steam.app_id}
- Game Name: {config.steam.app_name}

WRITING STYLE:
- Tone: {config.voice.tone}
- Personality: {config.voice.personality}
- NEVER use these phrases: {', '.join(config.voice.avoid_phrases)}

RECENT CHANGES:
{commits_text}

REQUIREMENTS:
- Write an engaging announcement about these changes
- Title must be under {config.voice.max_title_length} characters
- Body must be under {config.voice.max_body_length} characters
- Focus on player-facing improvements
- Be specific about what changed

FORMAT:
Title: [Your Title Here]
Body: [Your Body Here]
"""
    
    # Use existing AIClient for text (Gemini 1.5 Pro/Flash works fine with it)
    # But use google-genai SDK for Imagen 4.0 as requested
    from google import genai
    from google.genai import types
    
    async with AIClient(api_key=text_key, config=config.ai) as ai:
        try:
            print("  > Sending text generation request...")
            text_result = await ai.generate_text(prompt=prompt)
            print("  Text generated successfully!")
            print(f"  Title: {text_result.title}")
            print(f"  Body length: {len(text_result.body)} chars")
            
            # Save text
            with open(OUTPUT_PATH / "announcement.txt", "w", encoding="utf-8") as f:
                f.write(f"TITLE: {text_result.title}\n\n{text_result.body}")
                
            # Image Generation with Google GenAI SDK
            print("\n[3/5] Generating Banner with Imagen 4.0 (Google GenAI SDK)...")
            image_prompt = f"Game announcement banner for {config.steam.app_name}: {text_result.title}. Art style: {config.branding.art_style}"
            
            print("  > Sending image generation request...")
            
            # Run sync SDK call in thread to avoid blocking async loop
            def generate_image_sync():
                client = genai.Client(api_key=image_key)
                response = client.models.generate_images(
                    model='imagen-4.0-generate-001', # User specified model
                    prompt=image_prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9"
                    )
                )
                return response.generated_images[0].image
            
            try:
                generated_image = await asyncio.to_thread(generate_image_sync)
                print("  Image generated successfully!")
                
                # Save image
                image_path = OUTPUT_PATH / "banner.png"
                generated_image.save(image_path)
                print(f"  Saved to: {image_path}")
                
            except Exception as e:
                print(f"  Image generation failed: {e}")
                # Don't return, continue to Discord simulation
            
        except Exception as e:
            print(f"\nAI Generation Failed: {e}")
            return

    # 4. Mock Discord
    if 'text_result' in locals():
        print("\n[4/5] Simulating Discord Notification...")
        discord = MockDiscordNotifier()
        discord.send_preview(text_result.title, text_result.body)
        print("  > Preview sent to #dev-announcements")
        print("  > User 'henry' approved the draft.")
        
        # 5. Mock Steam
        print("\n[5/5] Simulating Steam Upload...")
        steam = MockSteamPublisher(app_id=config.steam.app_id, avoid_phrases=config.voice.avoid_phrases)
        compliance = steam.validate(text_result.title, text_result.body)
        
        # Use placeholder image if generation failed
        final_image_path = image_path if 'image_path' in locals() and image_path.exists() else Path("placeholder.png")
        
        if compliance["overall_pass"]:
            publish_info = steam.publish(text_result.title, text_result.body, final_image_path)
            print("  Steam Validation Passed")
            print(f"  Published to Steam: {publish_info['steam_url']}")
        else:
            print("  Steam Validation Failed:", compliance)

    print("\n" + "="*60)
    print("Simulation Complete!")
    print(f"Artifacts available in: {OUTPUT_PATH}")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(run_real_simulation())
