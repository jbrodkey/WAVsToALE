#!/usr/bin/env python3
"""
Ultra-minimal MasterMob approach to avoid segmentation fault
Uses only pyaaf2 built-in methods, minimal manual structure
"""

import aaf2
import wave
import os

def create_minimal_master_aaf(wav_file_path, output_aaf_path):
    """
    Create the most minimal possible MasterMob AAF to avoid segfaults
    Use only built-in methods, no manual slot/reference creation
    """
    print(f"🛡️ Creating MINIMAL MasterMob AAF from: {wav_file_path}")
    
    try:
        with aaf2.open(output_aaf_path, 'w') as f:
            clip_name = os.path.splitext(os.path.basename(wav_file_path))[0]
            
            # Ultra-minimal approach: Just use import_audio_essence and stop
            # Don't add any additional mobs or modify the structure
            master_mob = f.create.MasterMob(f"{clip_name}.Exported.01")
            
            print(f"   📊 Created MasterMob: {master_mob.name}")
            
            # Import audio - this should create the minimal necessary structure
            try:
                master_mob.import_audio_essence(wav_file_path, edit_rate=24)
                print(f"   ✅ Audio imported successfully")
            except Exception as import_error:
                print(f"   ❌ Import failed: {import_error}")
                return None
            
            # DON'T add anything else - keep it absolutely minimal
            print(f"   🛡️ Using minimal structure to prevent segfault")
            
        print(f"✅ Minimal MasterMob AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating minimal AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_minimal_aaf(aaf_path):
    """Safely analyze the minimal AAF structure"""
    print(f"\n🔍 Analyzing minimal AAF: {aaf_path}")
    print("=" * 40)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
            
            print(f"\n🛡️ Minimal structure analysis complete")
            print(f"   This should be safe to import without segfaults")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test ultra-minimal approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MINIMAL_SAFE_AAF.aaf"
    
    result = create_minimal_master_aaf(wav_file, output_aaf)
    if result:
        analyze_minimal_aaf(result)
        print(f"\n🛡️ TEST THIS MINIMAL AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Should NOT cause segmentation fault")
        print(f"   May still be subclip, but should be safe to import")