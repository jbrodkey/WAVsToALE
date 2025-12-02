#!/usr/bin/env python3
"""
Ultra-simple mono CompositionMob approach for testing
If this works, stereo is the issue. If this fails, deeper problem exists.
"""

import aaf2
import wave
import os

def create_simple_mono_aaf(wav_file_path, output_aaf_path):
    """
    Create the simplest possible AAF - mono CompositionMob
    """
    print(f"🔧 Creating SIMPLE MONO AAF from: {wav_file_path}")
    
    try:
        with aaf2.open(output_aaf_path, 'w') as f:
            clip_name = os.path.splitext(os.path.basename(wav_file_path))[0]
            edit_rate = 24
            
            # Read duration
            with wave.open(wav_file_path, 'rb') as wf:
                n_frames = wf.getnframes()
                sample_rate = wf.getframerate()
                duration_seconds = n_frames / sample_rate
                duration_frames = int(duration_seconds * edit_rate)
            
            print(f"   📊 Duration: {duration_seconds:.2f}s, {duration_frames} frames")
            
            # Step 1: Create SourceMob with embedded audio
            temp_master = f.create.MasterMob(f"{clip_name}_temp")
            temp_master.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            
            # Find SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created")
                return None
            
            source_mob = source_mobs[0]
            print(f"   ✅ Created SourceMob: {source_mob.name}")
            
            # Step 2: Create CompositionMob with SINGLE slot only
            comp_mob = f.create.CompositionMob(f"{clip_name}_mono")
            
            # Single slot only - no loops, no complexity
            slot = f.create.TimelineMobSlot()
            slot.name = clip_name
            slot.slot_id = 1
            slot.edit_rate = edit_rate
            slot.origin = 0
            
            # Single source clip
            source_clip = f.create.SourceClip()
            source_clip.length = duration_frames
            source_clip.start = 0
            source_clip.datadef = f.dictionary.lookup_datadef('Sound')
            source_clip.mob = source_mob
            source_clip.slot_id = 1
            
            slot.segment = source_clip
            comp_mob.slots.append(slot)
            
            # Add to AAF
            f.content.mobs.append(comp_mob)
            
            print(f"   ✅ Created mono CompositionMob")
            
        print(f"✅ Simple mono AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating simple mono AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test ultra-simple mono approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_SIMPLE_MONO_AAF.aaf"
    
    result = create_simple_mono_aaf(wav_file, output_aaf)
    if result:
        print(f"\n🎯 TEST SIMPLE MONO AAF:")
        print(f"   File: {result}")
        print(f"   Single CompositionMob slot (mono)")
        print(f"   If this works: stereo handling is the issue")
        print(f"   If this fails: deeper aaf2 library problem")
    else:
        print(f"\n❌ Even simple mono failed")
        print(f"   Suggests fundamental aaf2 library issue")