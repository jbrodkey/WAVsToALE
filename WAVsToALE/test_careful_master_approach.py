#!/usr/bin/env python3
"""
Careful MasterMob approach - create SourceMob first, then MasterMob
Avoid segfaults by using proper AAF object lifecycle
"""

import aaf2
import wave
import os

def create_careful_master_aaf(wav_file_path, output_aaf_path):
    """
    Carefully create MasterMob AAF by:
    1. Creating SourceMob first (embedded audio)
    2. Creating MasterMob second (references SourceMob)
    3. Using proper AAF object lifecycle to avoid segfaults
    """
    print(f"🔧 Creating CAREFUL MasterMob AAF from: {wav_file_path}")
    
    # Read WAV properties first
    try:
        with wave.open(wav_file_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            duration_seconds = n_frames / sample_rate
    except Exception as e:
        print(f"❌ Error reading WAV: {e}")
        return None
    
    try:
        with aaf2.open(output_aaf_path, 'w') as f:
            clip_name = os.path.splitext(os.path.basename(wav_file_path))[0]
            edit_rate = 24
            duration_frames = int(duration_seconds * edit_rate)
            
            print(f"   📊 WAV: {channels}ch, {duration_seconds:.2f}s")
            print(f"   🎬 Timeline: {edit_rate}fps, {duration_frames} frames")
            
            # Step 1: Create SourceMob with embedded audio (safe)
            source_master = f.create.MasterMob(f"{clip_name}_source_temp")
            source_master.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            
            # Get the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created")
                return None
            
            source_mob = source_mobs[0]
            print(f"   ✅ Created SourceMob: {source_mob.name}")
            
            # Step 2: CAREFULLY create MasterMob
            # Create it but don't add complex references yet
            master_mob = f.create.MasterMob(f"{clip_name}.Exported.01")
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Step 3: Create simple slots - just ONE slot for safety
            # Start with mono to avoid complexity
            slot = f.create.TimelineMobSlot()
            slot.name = clip_name
            slot.slot_id = 1
            slot.edit_rate = edit_rate
            slot.origin = 0
            
            # Step 4: Create SourceClip carefully
            source_clip = f.create.SourceClip()
            source_clip.length = duration_frames
            source_clip.start = 0
            
            # Get Sound datadef
            try:
                sound_datadef = f.dictionary.lookup_datadef('Sound')
                source_clip.datadef = sound_datadef
                print(f"   ✅ Set Sound datadef")
            except Exception as dd_error:
                print(f"   ⚠️ Datadef error: {dd_error}")
            
            # Step 5: CAREFULLY set mob reference
            try:
                source_clip.mob = source_mob
                source_clip.slot_id = 1
                print(f"   ✅ Set mob reference carefully")
            except Exception as ref_error:
                print(f"   ❌ Reference error: {ref_error}")
                return None
            
            # Step 6: Add to slot and mob
            slot.segment = source_clip
            master_mob.slots.append(slot)
            
            # Step 7: Add MasterMob to content
            f.content.mobs.append(master_mob)
            
            print(f"   ✅ Added MasterMob to AAF")
            
        print(f"✅ Careful MasterMob AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating careful AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test careful approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_CAREFUL_MASTER_AAF.aaf"
    
    result = create_careful_master_aaf(wav_file, output_aaf)
    if result:
        print(f"\n🔧 TEST THIS CAREFUL AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Should have both SourceMob and MasterMob")
        print(f"   Should avoid segmentation fault")
        print(f"   Should import as master clip (not subclip)")
    else:
        print(f"\n❌ Careful approach also failed")
        print(f"   May need to use CompositionMob and work around subclip issue")