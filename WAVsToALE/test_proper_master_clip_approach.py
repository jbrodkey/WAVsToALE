#!/usr/bin/env python3
"""
Correct AAF structure: CompositionMob -> MasterMob -> SourceMob
This should create proper master clips that Avid recognizes
"""

import aaf2
import wave
import os

def create_proper_master_clip_aaf(wav_file_path, output_aaf_path):
    """
    Create AAF with proper 3-tier structure:
    CompositionMob (subclip) -> MasterMob (master clip) -> SourceMob (embedded audio)
    """
    print(f"🔧 Creating Proper Master Clip AAF from: {wav_file_path}")
    
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
            edit_rate = 24  # Standard film rate
            duration_frames = int(duration_seconds * edit_rate)
            
            print(f"   🎬 Timeline: {edit_rate}fps, {duration_frames} frames")
            
            # Step 1: Create MasterMob (this will also create SourceMob)
            master_mob = f.create.MasterMob(clip_name)
            master_mob.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Find the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created - audio import failed")
                return None
            
            source_mob = source_mobs[0]
            print(f"   ✅ Found SourceMob: {source_mob.name}")
            
            # Step 2: Create CompositionMob that references the MasterMob (not SourceMob!)
            comp_mob = f.create.CompositionMob(f"{clip_name}_subclip")
            print(f"   ✅ Created CompositionMob: {comp_mob.name}")
            
            # Step 3: Create timeline slot in CompositionMob that references MasterMob
            slot = f.create.TimelineMobSlot()
            slot.name = f"{clip_name}"
            slot.slot_id = 1
            slot.edit_rate = edit_rate
            slot.origin = 0
            
            # Create source clip that references the MasterMob (KEY CHANGE!)
            source_clip = f.create.SourceClip()
            source_clip.length = duration_frames
            source_clip.start = 0
            source_clip.datadef = f.dictionary.lookup_datadef('Sound')
            
            # CRITICAL: Reference the MasterMob, not the SourceMob
            source_clip.mob = master_mob
            source_clip.slot_id = 1  # Reference the MasterMob's slot
            
            slot.segment = source_clip
            comp_mob.slots.append(slot)
            print(f"   ✅ CompositionMob references MasterMob")
            
            # Step 4: Ensure MasterMob is in the content (should already be there from import_audio_essence)
            if master_mob not in f.content.mobs:
                f.content.mobs.append(master_mob)
                print(f"   ✅ Added MasterMob to content")
            else:
                print(f"   ✅ MasterMob already in content")
            
            # Step 5: Add CompositionMob to the AAF
            f.content.mobs.append(comp_mob)
            
            print(f"   📊 Final structure:")
            for mob_obj in f.content.mobs:
                print(f"      {type(mob_obj).__name__}: {mob_obj.name}")
                
        print(f"✅ Proper Master Clip AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Proper Master Clip AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_proper_master_aaf(aaf_path):
    """Analyze the 3-tier AAF structure"""
    print(f"\n🔍 Analyzing Proper Master Clip AAF: {aaf_path}")
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
                        
                        if hasattr(segment, 'mob') and segment.mob:
                            ref_mob = segment.mob
                            ref_slot = getattr(segment, 'slot_id', '?')
                            print(f"    References: {type(ref_mob).__name__} '{ref_mob.name}' slot {ref_slot}")
            
            # Count mob types
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            comp_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'CompositionMob']
            master_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'MasterMob']
            
            print(f"\n📊 Summary:")
            print(f"   SourceMobs: {len(source_mobs)} (embedded audio)")
            print(f"   MasterMobs: {len(master_mobs)} (master clips)")
            print(f"   CompositionMobs: {len(comp_mobs)} (subclips)")
            
            print(f"\n🎯 Proper 3-tier structure:")
            print(f"   CompositionMob -> MasterMob -> SourceMob")
            print(f"   This should create linked subclips with findable master clips!")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the proper 3-tier approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_PROPER_MASTER_CLIP.aaf"
    
    result = create_proper_master_clip_aaf(wav_file, output_aaf)
    if result:
        analyze_proper_master_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Should create LINKED subclips with findable master clips")
        print(f"   CompositionMob -> MasterMob -> SourceMob structure")
    else:
        print(f"\n❌ Proper Master Clip approach failed")