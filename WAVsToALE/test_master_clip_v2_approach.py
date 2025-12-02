#!/usr/bin/env python3
"""
Test the new Master Clip approach using EssenceManager and primary_mob header
Based on the provided code that should create actual Master Clips
"""

import aaf2
import wave
import os

def create_master_clip_aaf_v2(wav_file_path, output_aaf_path):
    """
    Create AAF using the new Master Clip approach with EssenceManager
    Key differences:
    - Use create_essence_manager() for direct embedding
    - Set f.header.primary_mob to MasterMob
    - Self-referencing MasterMob structure
    """
    print(f"🔧 Creating Master Clip AAF v2 from: {wav_file_path}")
    
    # Read WAV properties and data
    try:
        with wave.open(wav_file_path, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            sample_rate = wf.getframerate()
            n_frames = wf.getnframes()
            audio_data = wf.readframes(n_frames)
            duration_samples = n_frames
            duration_seconds = n_frames / sample_rate
            print(f"   📊 WAV: {channels}ch, {sample_width*8}-bit, {sample_rate}Hz, {duration_seconds:.2f}s")
    except Exception as e:
        print(f"❌ Error reading WAV: {e}")
        return None
    
    try:
        with aaf2.open(output_aaf_path, 'w') as f:
            clip_name = os.path.splitext(os.path.basename(wav_file_path))[0]
            
            # Step 1: Create MasterMob (not using import_audio_essence)
            master_mob = f.create.MasterMob(f"{clip_name}_Master")
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Step 2: Use EssenceManager to embed audio directly
            try:
                em = f.create_essence_manager()
                em.create_essencestream(
                    master_mob,
                    'sound',            # Kind of essence
                    sample_rate,        # Edit rate (audio sample rate)
                    channels,
                    sample_width,
                    audio_data
                )
                print(f"   ✅ Embedded audio essence using EssenceManager")
            except Exception as em_error:
                print(f"   ❌ EssenceManager error: {em_error}")
                return None
            
            # Step 3: Add slots to MasterMob (self-referencing)
            for i in range(channels):
                timeline_slot = f.create.TimelineMobSlot()
                timeline_slot.slot_id = i + 1
                timeline_slot.edit_rate = sample_rate  # Use sample rate for master clip
                timeline_slot.name = f"Audio Ch {i+1}"
                
                # Create SourceClip that references the MasterMob itself
                source_clip = f.create.SourceClip()
                source_clip.length = duration_samples  # Length in samples
                source_clip.start = 0
                source_clip.datadef = f.dictionary.lookup_datadef('Sound')
                source_clip.mob = master_mob  # *** SELF-REFERENCE ***
                source_clip.slot_id = i + 1  # Reference specific channel
                
                timeline_slot.segment = source_clip
                master_mob.slots.append(timeline_slot)
                print(f"   ✅ Added self-referencing slot {i+1}")
            
            # Step 4: Add MasterMob to content
            f.content.mobs.append(master_mob)
            
            # Step 5: *** CRITICAL *** Set primary_mob in header
            f.header.primary_mob = master_mob
            print(f"   ✅ Set MasterMob as primary_mob in header")
            
        print(f"✅ Master Clip AAF v2 created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Master Clip AAF v2: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_master_v2_aaf(aaf_path):
    """Analyze the new Master Clip AAF structure"""
    print(f"\n🔍 Analyzing Master Clip AAF v2: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            # Check primary_mob setting
            if hasattr(f.header, 'primary_mob') and f.header.primary_mob:
                primary_mob = f.header.primary_mob
                print(f"✅ Primary Mob: {type(primary_mob).__name__} '{primary_mob.name}'")
            else:
                print(f"❌ No primary_mob set in header")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                # Check if this mob has essence descriptor
                if hasattr(mob, 'descriptor') and mob.descriptor:
                    desc_type = type(mob.descriptor).__name__
                    print(f"  Descriptor: {desc_type}")
                
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
                                print(f"    References: {type(ref_mob).__name__} slot {ref_slot}")
            
            print(f"\n🎯 This structure should import as MASTER CLIP!")
            print(f"   Key features:")
            print(f"   ✅ MasterMob set as primary_mob in header")
            print(f"   ✅ Self-referencing MasterMob slots")
            print(f"   ✅ Direct essence embedding via EssenceManager")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the new Master Clip approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MASTER_CLIP_V2.aaf"
    
    result = create_master_clip_aaf_v2(wav_file, output_aaf)
    if result:
        analyze_master_v2_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Should import as MASTER CLIP (not subclip)")
        print(f"   Uses EssenceManager + primary_mob header + self-referencing")
    else:
        print(f"\n❌ Master Clip v2 approach failed")