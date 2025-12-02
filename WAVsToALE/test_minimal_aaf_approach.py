#!/usr/bin/env python3
"""
Minimal AAF approach - just SourceMob with embedded audio
No CompositionMob, no MasterMob - simplest possible structure
"""

import aaf2
import wave
import os

def create_minimal_aaf(wav_file_path, output_aaf_path):
    """
    Create the absolute minimal AAF structure
    Just SourceMob with embedded audio - nothing else
    """
    print(f"🔧 Creating Minimal AAF from: {wav_file_path}")
    
    # Read WAV properties
    try:
        with wave.open(wav_file_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration_seconds = n_frames / sample_rate
            print(f"   📊 WAV: {channels}ch, {sample_width*8}-bit, {sample_rate}Hz, {duration_seconds:.2f}s")
    except Exception as e:
        print(f"❌ Error reading WAV: {e}")
        return None
    
    try:
        with aaf2.open(output_aaf_path, 'w') as f:
            clip_name = os.path.splitext(os.path.basename(wav_file_path))[0]
            
            # Step 1: Create SourceMob directly (no intermediate MasterMob)
            source_mob = f.create.SourceMob(clip_name)
            print(f"   ✅ Created SourceMob: {source_mob.name}")
            
            # Step 2: Import audio directly into SourceMob
            source_mob.import_audio_essence(wav_file_path, edit_rate=48000)  # Use sample rate as edit rate
            print(f"   ✅ Imported audio essence directly into SourceMob")
            
            # That's it - no CompositionMob, no MasterMob
            # Just raw SourceMob with embedded audio
            
            print(f"   📊 Final structure:")
            for mob_obj in f.content.mobs:
                print(f"      {type(mob_obj).__name__}: {mob_obj.name}")
                
        print(f"✅ Minimal AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Minimal AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_minimal_aaf(aaf_path):
    """Analyze the minimal AAF structure"""
    print(f"\n🔍 Analyzing Minimal AAF: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                for i, slot in enumerate(mob.slots):
                    print(f"  Slot {i+1}: ID={slot.slot_id}, Name='{getattr(slot, 'name', '')}'")
                    
                    if hasattr(slot, 'segment') and slot.segment:
                        segment = slot.segment
                        segment_type = type(segment).__name__
                        print(f"    Segment: {segment_type}, Length: {segment.length}")
                        
                        if hasattr(segment, 'datadef') and segment.datadef:
                            datadef_name = getattr(segment.datadef, 'name', str(segment.datadef))
                            print(f"    DataDef: {datadef_name}")
            
            # Count mob types
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            comp_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'CompositionMob']
            master_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'MasterMob']
            
            print(f"\n📊 Summary:")
            print(f"   SourceMobs: {len(source_mobs)} (embedded audio)")
            print(f"   MasterMobs: {len(master_mobs)} (should be 0)")
            print(f"   CompositionMobs: {len(comp_mobs)} (should be 0)")
            
            print(f"\n💡 Absolute minimal structure - just embedded audio")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the minimal approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MINIMAL.aaf"
    
    result = create_minimal_aaf(wav_file, output_aaf)
    if result:
        analyze_minimal_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Absolute minimal structure")
        print(f"   Maybe Avid will treat this as raw media?")
    else:
        print(f"\n❌ Minimal approach failed")