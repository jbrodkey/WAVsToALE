#!/usr/bin/env python3
"""
Corrected MasterMob approach for master clip import
Based on analysis of working Avid AAF structure
"""

import aaf2
import wave
import os

def create_master_clip_aaf(wav_file_path, output_aaf_path):
    """
    Create AAF using MasterMob approach for master clip import (not subclip)
    Addresses the console error by ensuring proper audio component structure
    """
    print(f"🔧 Creating MasterMob AAF (master clip) from: {wav_file_path}")
    
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
            
            # Step 1: Create SourceMob with embedded audio
            temp_mob = f.create.MasterMob(f"{clip_name}_temp")
            temp_mob.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            
            # Find the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created - audio import failed")
                return None
            
            source_mob = source_mobs[0]
            print(f"   ✅ Created SourceMob: {source_mob.name}")
            
            # Step 2: Create proper MasterMob that references the SourceMob
            master_mob = f.create.MasterMob(f"{clip_name}.Exported.01")
            
            # Create MasterMob slots that reference SourceMob (like working Avid AAF)
            for channel in range(channels):
                slot = f.create.TimelineMobSlot()
                slot.name = clip_name
                slot.slot_id = channel + 1
                slot.edit_rate = edit_rate
                slot.origin = 0
                
                # Create SourceClip that references the SourceMob
                source_clip = f.create.SourceClip()
                source_clip.length = duration_frames
                source_clip.start = 0
                source_clip.datadef = f.dictionary.lookup_datadef('Sound')
                source_clip.mob = source_mob
                source_clip.slot_id = 1  # Reference SourceMob slot 1
                
                slot.segment = source_clip
                master_mob.slots.append(slot)
                print(f"   ✅ Added channel {channel+1} to MasterMob")
            
            # Rename temp_mob to avoid confusion
            temp_mob.name = f"{clip_name}_temp"
            
            # Add the proper MasterMob
            f.content.mobs.append(master_mob)
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Verify structure
            print(f"   📊 Final structure:")
            print(f"     SourceMob slots: {len(source_mob.slots)}")
            print(f"     MasterMob slots: {len(master_mob.slots)}")
            for i, slot in enumerate(master_mob.slots):
                if hasattr(slot, 'segment') and slot.segment and hasattr(slot.segment, 'mob'):
                    ref_mob = slot.segment.mob
                    ref_slot = getattr(slot.segment, 'slot_id', '?')
                    print(f"       Slot {i+1}: refs {type(ref_mob).__name__} slot {ref_slot}")
            
        print(f"✅ MasterMob AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating MasterMob AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_master_clip_aaf(aaf_path):
    """Analyze the structure of our MasterMob AAF"""
    print(f"\n🔍 Analyzing MasterMob AAF: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            source_mobs = []
            master_mobs = []
            comp_mobs = []
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                if mob_type == 'SourceMob':
                    source_mobs.append(mob)
                elif mob_type == 'MasterMob':
                    master_mobs.append(mob)
                elif mob_type == 'CompositionMob':
                    comp_mobs.append(mob)
                
                for i, slot in enumerate(mob.slots):
                    print(f"  Slot {i+1}: ID={slot.slot_id}")
                    
                    if hasattr(slot, 'segment') and slot.segment:
                        segment = slot.segment
                        segment_type = type(segment).__name__
                        print(f"    Segment: {segment_type}")
                        
                        if hasattr(segment, 'datadef') and segment.datadef:
                            datadef_name = getattr(segment.datadef, 'name', str(segment.datadef))
                            print(f"    DataDef: {datadef_name}")
                        
                        if hasattr(segment, 'mob') and segment.mob:
                            ref_mob = segment.mob
                            ref_slot = getattr(segment, 'slot_id', '?')
                            print(f"    References: {type(ref_mob).__name__} \"{ref_mob.name}\" slot {ref_slot}")
            
            print(f"\n📊 Summary:")
            print(f"   SourceMobs: {len(source_mobs)} (embedded audio)")
            print(f"   MasterMobs: {len(master_mobs)} (master clips)")
            print(f"   CompositionMobs: {len(comp_mobs)} (should be 0 for master clips)")
            
            print(f"\n💡 This structure should create MASTER CLIPS (not subclips)")
            print(f"   and avoid the FindSourceCompositionForComponent error")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the corrected MasterMob approach for master clip import
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_MASTER_CLIP_AAF.aaf"
    
    result = create_master_clip_aaf(wav_file, output_aaf)
    if result:
        analyze_master_clip_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Should import as MASTER CLIP (not subclip)")
        print(f"   Should allow batch import and master clip access")
        print(f"   Should prevent the MultiChanAudioInfo console error")