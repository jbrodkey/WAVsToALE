#!/usr/bin/env python3
"""
Pure documentation approach - exactly following pyaaf2 docs
Based on section 1.1.3 "Embedding Footage" example
"""

import aaf2
import wave
import os

def create_pure_master_mob_aaf(wav_file_path, output_aaf_path):
    """
    Create AAF exactly as shown in pyaaf2 documentation
    This should create a proper Master Clip
    """
    print(f"🔧 Creating Pure MasterMob AAF from: {wav_file_path}")
    
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
            edit_rate = 25  # Standard rate from docs
            
            # Step 1: Create MasterMob exactly as documentation shows
            mob = f.create.MasterMob(f"{clip_name}")
            print(f"   ✅ Created MasterMob: {mob.name}")
            
            # Step 2: Add the mob to the file (as per docs)
            f.content.mobs.append(mob)
            print(f"   ✅ Added MasterMob to file content")
            
            # Step 3: Import audio essence (as per docs)
            # This is the key - let the library handle everything
            mob.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            print(f"   ✅ Imported audio essence into MasterMob")
            
            # Step 4: DO NOT MODIFY ANYTHING ELSE
            # Let the library create whatever structure it needs
            
            print(f"   📊 Final structure:")
            for mob_obj in f.content.mobs:
                print(f"      {type(mob_obj).__name__}: {mob_obj.name}")
                
        print(f"✅ Pure MasterMob AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Pure MasterMob AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_pure_master_aaf(aaf_path):
    """Analyze the Pure MasterMob AAF structure"""
    print(f"\n🔍 Analyzing Pure MasterMob AAF: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                # Show mob ID and other properties
                if hasattr(mob, 'mob_id'):
                    print(f"  Mob ID: {mob.mob_id}")
                
                for i, slot in enumerate(mob.slots):
                    print(f"  Slot {i+1}: ID={slot.slot_id}, Name='{getattr(slot, 'name', '')}'")
                    
                    if hasattr(slot, 'segment') and slot.segment:
                        segment = slot.segment
                        print(f"    Segment: {type(segment).__name__}, Length: {segment.length}")
                        
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
            print(f"   SourceMobs: {len(source_mobs)}")
            print(f"   CompositionMobs: {len(comp_mobs)}")
            print(f"   MasterMobs: {len(master_mobs)}")
            
            print(f"\n💡 This follows the exact documentation pattern")
            print(f"   Should create proper Master Clip structure for Avid!")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the Pure Documentation approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_PURE_DOCUMENTATION.aaf"
    
    result = create_pure_master_mob_aaf(wav_file, output_aaf)
    if result:
        analyze_pure_master_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Created exactly as shown in pyaaf2 documentation")
        print(f"   Simple MasterMob with import_audio_essence")
        print(f"   This SHOULD import as Master Clip!")
    else:
        print(f"\n❌ Pure Documentation approach failed")