#!/usr/bin/env python3
"""
Test Master Clip approach using actual aaf2 API
Focus on: primary_mob header setting and self-referencing MasterMob
"""

import aaf2
import wave
import os

def create_master_clip_aaf_v3(wav_file_path, output_aaf_path):
    """
    Create AAF for Master Clip import using real aaf2 API
    Key approach:
    - Use import_audio_essence but modify structure
    - Set header properties for primary mob
    - Create self-referencing MasterMob
    """
    print(f"🔧 Creating Master Clip AAF v3 from: {wav_file_path}")
    
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
            
            # Step 1: Create MasterMob and import essence (this creates SourceMob)
            master_mob = f.create.MasterMob(f"{clip_name}_Master")
            master_mob.import_audio_essence(wav_file_path, edit_rate=sample_rate)
            print(f"   ✅ Created MasterMob with embedded essence: {master_mob.name}")
            
            # Step 2: Find the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if source_mobs:
                source_mob = source_mobs[0]
                print(f"   ✅ Found SourceMob: {source_mob.name}")
                
                # Step 3: Modify MasterMob to be self-referencing
                # Clear existing slots and create new self-referencing ones
                master_mob.slots.clear()
                
                for i in range(channels):
                    # Create timeline slot
                    timeline_slot = f.create.create_instance('TimelineMobSlot')
                    timeline_slot.slot_id = i + 1
                    timeline_slot.edit_rate = sample_rate
                    timeline_slot.name = f"Audio Ch {i+1}"
                    
                    # Create SourceClip that references MasterMob itself
                    source_clip = f.create.create_instance('SourceClip')
                    source_clip.length = n_frames  # Length in samples
                    source_clip.start = 0
                    source_clip.datadef = f.dictionary.lookup_datadef('Sound')
                    
                    # *** SELF-REFERENCE: Point to MasterMob itself ***
                    source_clip.mob = master_mob
                    source_clip.slot_id = i + 1
                    
                    timeline_slot.segment = source_clip
                    master_mob.slots.append(timeline_slot)
                    print(f"   ✅ Added self-referencing slot {i+1}")
            
            # Step 4: Try to set primary mob in header
            try:
                # Check what header properties exist
                header_props = f.header.properties
                print(f"   📋 Header has {len(header_props)} properties")
                
                # Try to set primary mob reference
                # Different ways to try this:
                if hasattr(f.header, 'primary_mob'):
                    f.header.primary_mob = master_mob
                    print(f"   ✅ Set primary_mob attribute")
                else:
                    # Try setting as property
                    try:
                        f.header['PrimaryMob'] = master_mob
                        print(f"   ✅ Set PrimaryMob property")
                    except:
                        try:
                            f.header['primary_mob'] = master_mob
                            print(f"   ✅ Set primary_mob property")
                        except:
                            print(f"   ⚠️  Could not set primary mob in header")
                            
            except Exception as header_error:
                print(f"   ⚠️  Header modification error: {header_error}")
            
            # Step 5: Remove the separate SourceMob (keep only MasterMob)
            try:
                if source_mobs:
                    for sm in source_mobs:
                        if sm in f.content.mobs:
                            f.content.mobs.remove(sm)
                    print(f"   ✅ Removed separate SourceMob")
            except Exception as remove_error:
                print(f"   ⚠️  Could not remove SourceMob: {remove_error}")
            
        print(f"✅ Master Clip AAF v3 created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Master Clip AAF v3: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_master_v3_aaf(aaf_path):
    """Analyze the Master Clip AAF v3 structure"""
    print(f"\n🔍 Analyzing Master Clip AAF v3: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            # Check header properties
            print(f"\n📋 Header Properties:")
            for prop in f.header.properties:
                print(f"  {prop}")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                # Check mob properties
                if hasattr(mob, 'mob_id'):
                    print(f"  Mob ID: {mob.mob_id}")
                
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
                print(f"\n🎯 PERFECT! Single MasterMob structure - should import as Master Clip!")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the Master Clip v3 approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MASTER_CLIP_V3.aaf"
    
    result = create_master_clip_aaf_v3(wav_file, output_aaf)
    if result:
        analyze_master_v3_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Single MasterMob with self-referencing structure")
        print(f"   Should import as MASTER CLIP (not subclip)")
    else:
        print(f"\n❌ Master Clip v3 approach failed")