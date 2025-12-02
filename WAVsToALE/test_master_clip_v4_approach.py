#!/usr/bin/env python3
"""
Test Master Clip approach v4 using proper aaf2 API
Based on working CompositionMob but trying to create pure MasterMob structure
"""

import aaf2
import wave
import os

def create_master_clip_aaf_v4(wav_file_path, output_aaf_path):
    """
    Create AAF for Master Clip import using proper aaf2 API
    Approach: Create MasterMob only, no CompositionMob
    """
    print(f"🔧 Creating Master Clip AAF v4 from: {wav_file_path}")
    
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
            edit_rate = 24  # Standard edit rate
            duration_frames = int(duration_seconds * edit_rate)
            
            # Step 1: Create ONLY MasterMob (no temp MasterMob)
            master_mob = f.create.MasterMob(f"{clip_name}_Master")
            master_mob.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Step 2: Find the SourceMob that was created
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created")
                return None
                
            source_mob = source_mobs[0]
            print(f"   ✅ Found SourceMob: {source_mob.name}")
            
            # Step 3: REMOVE the separate SourceMob - we want only MasterMob
            try:
                f.content.mobs.remove(source_mob)
                print(f"   ✅ Removed separate SourceMob")
            except:
                print(f"   ⚠️  Could not remove SourceMob")
            
            # Step 4: Make MasterMob self-contained
            # Clear existing slots and recreate them as self-referencing
            original_slots = list(master_mob.slots)  # Copy the slots
            master_mob.slots.clear()
            
            for channel in range(channels):
                # Create new timeline slot using proper aaf2 method
                slot = f.create.TimelineMobSlot()
                slot.name = f"{clip_name}_ch{channel+1}"
                slot.slot_id = channel + 1
                slot.edit_rate = edit_rate
                slot.origin = 0
                
                # Create source clip that references the MasterMob itself
                source_clip = f.create.SourceClip()
                source_clip.length = duration_frames
                source_clip.start = 0
                source_clip.datadef = f.dictionary.lookup_datadef('Sound')
                
                # SELF-REFERENCE: Point to MasterMob itself
                source_clip.mob = master_mob
                source_clip.slot_id = channel + 1
                
                slot.segment = source_clip
                master_mob.slots.append(slot)
                print(f"   ✅ Added self-referencing slot {channel+1}")
            
            # Step 5: Ensure only MasterMob exists
            print(f"   📊 Final mob count: {len(f.content.mobs)}")
            for mob in f.content.mobs:
                print(f"      {type(mob).__name__}: {mob.name}")
                
        print(f"✅ Master Clip AAF v4 created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Master Clip AAF v4: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_master_v4_aaf(aaf_path):
    """Analyze the Master Clip AAF v4 structure"""
    print(f"\n🔍 Analyzing Master Clip AAF v4: {aaf_path}")
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
                        print(f"    Segment: {type(segment).__name__}, Length: {segment.length}")
                        
                        if hasattr(segment, 'mob') and segment.mob:
                            ref_mob = segment.mob
                            ref_slot = getattr(segment, 'slot_id', '?')
                            
                            # Check for self-reference
                            if ref_mob == mob:
                                print(f"    ✅ SELF-REFERENCE: slot {ref_slot}")
                            else:
                                print(f"    References: {type(ref_mob).__name__} '{ref_mob.name}' slot {ref_slot}")
            
            # Count mob types
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            comp_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'CompositionMob']
            master_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'MasterMob']
            
            print(f"\n📊 Summary:")
            print(f"   SourceMobs: {len(source_mobs)} (should be 0)")
            print(f"   CompositionMobs: {len(comp_mobs)} (should be 0)")
            print(f"   MasterMobs: {len(master_mobs)} (should be 1)")
            
            if len(master_mobs) == 1 and len(source_mobs) == 0 and len(comp_mobs) == 0:
                print(f"\n🎯 SUCCESS! Pure MasterMob structure!")
                print(f"   This should import as Master Clip in Avid!")
            else:
                print(f"\n⚠️  Structure may not be optimal for Master Clip import")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the Master Clip v4 approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MASTER_CLIP_V4.aaf"
    
    result = create_master_clip_aaf_v4(wav_file, output_aaf)
    if result:
        analyze_master_v4_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Pure MasterMob with self-referencing structure")
        print(f"   NO CompositionMob, NO separate SourceMob")
        print(f"   Should import as MASTER CLIP!")
    else:
        print(f"\n❌ Master Clip v4 approach failed")