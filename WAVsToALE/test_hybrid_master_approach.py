#!/usr/bin/env python3
"""
Hybrid approach: Use our working CompositionMob but try to make it import as Master Clip
Key insights from the provided code:
1. Set primary_mob in header
2. Minimize separate SourceMobs
3. Focus on making the structure appear as a Master Clip to Avid
"""

import aaf2
import wave
import os

def create_hybrid_master_aaf(wav_file_path, output_aaf_path):
    """
    Hybrid approach: Working CompositionMob + Master Clip features
    """
    print(f"🔧 Creating Hybrid Master AAF from: {wav_file_path}")
    
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
            
            # Step 1: Create MasterMob with embedded audio (this creates SourceMob too)
            master_mob = f.create.MasterMob(f"{clip_name}_Master")
            master_mob.import_audio_essence(wav_file_path, edit_rate=edit_rate)
            print(f"   ✅ Created MasterMob: {master_mob.name}")
            
            # Find the created SourceMob
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            if not source_mobs:
                print("   ❌ No SourceMob created")
                return None
            
            source_mob = source_mobs[0]
            print(f"   ✅ Found SourceMob: {source_mob.name}")
            
            # Step 2: *** KEY INSIGHT *** Rename and repurpose the SourceMob
            # Instead of creating a separate CompositionMob, let's modify the SourceMob
            # to behave more like a Master Clip
            
            # Rename the SourceMob to indicate it's the primary clip
            source_mob.name = f"{clip_name}_MasterClip"
            
            # Step 3: Try to set header properties to indicate this is the primary clip
            try:
                # Attempt different ways to set primary mob
                header_props = list(f.header.properties)
                print(f"   📋 Header properties: {len(header_props)}")
                
                # Method 1: Try direct property setting
                try:
                    f.header['PrimaryMob'] = source_mob
                    print(f"   ✅ Set PrimaryMob property to SourceMob")
                except Exception as e1:
                    try:
                        # Method 2: Try different property name
                        f.header['primary_mob'] = source_mob
                        print(f"   ✅ Set primary_mob property to SourceMob")
                    except Exception as e2:
                        print(f"   ⚠️  Could not set primary mob: {e1}, {e2}")
            except Exception as header_error:
                print(f"   ⚠️  Header error: {header_error}")
            
            # Step 4: Remove the MasterMob since SourceMob has the essence
            try:
                f.content.mobs.remove(master_mob)
                print(f"   ✅ Removed MasterMob, keeping only SourceMob")
            except:
                print(f"   ⚠️  Could not remove MasterMob")
            
            # Step 5: Add metadata to the SourceMob to make it more "Master Clip"-like
            try:
                # Add comments that indicate this is a master clip
                if hasattr(source_mob, 'comments'):
                    comment = f.create.create_instance('TaggedValue')
                    comment.name = 'Type'
                    comment.value = 'MasterClip'
                    source_mob.comments.append(comment)
                    print(f"   ✅ Added MasterClip type comment")
            except Exception as comment_error:
                print(f"   ⚠️  Could not add comment: {comment_error}")
            
            print(f"   📊 Final structure:")
            for mob in f.content.mobs:
                print(f"      {type(mob).__name__}: {mob.name}")
                
        print(f"✅ Hybrid Master AAF created: {output_aaf_path}")
        return output_aaf_path
        
    except Exception as e:
        print(f"❌ Error creating Hybrid Master AAF: {e}")
        import traceback
        traceback.print_exc()
        return None

def analyze_hybrid_aaf(aaf_path):
    """Analyze the Hybrid AAF structure"""
    print(f"\n🔍 Analyzing Hybrid AAF: {aaf_path}")
    print("=" * 50)
    
    try:
        with aaf2.open(aaf_path, 'r') as f:
            print(f"Total mobs: {len(f.content.mobs)}")
            
            # Check header properties
            print(f"\n📋 Header Properties:")
            try:
                header_props = list(f.header.properties)
                for prop in header_props[:10]:  # Show first 10
                    print(f"  {prop}")
                if len(header_props) > 10:
                    print(f"  ... and {len(header_props)-10} more")
            except:
                print("  Could not read header properties")
            
            for mob in f.content.mobs:
                mob_type = type(mob).__name__
                print(f"\n{mob_type}: \"{mob.name}\" (slots: {len(mob.slots)})")
                
                # Check for comments
                if hasattr(mob, 'comments') and mob.comments:
                    print(f"  Comments: {len(mob.comments)}")
                    for comment in mob.comments:
                        if hasattr(comment, 'name') and hasattr(comment, 'value'):
                            print(f"    {comment.name}: {comment.value}")
                
                for i, slot in enumerate(mob.slots):
                    print(f"  Slot {i+1}: ID={slot.slot_id}, Name='{getattr(slot, 'name', '')}'")
                    
                    if hasattr(slot, 'segment') and slot.segment:
                        segment = slot.segment
                        print(f"    Segment: {type(segment).__name__}, Length: {segment.length}")
                        
                        if hasattr(segment, 'datadef') and segment.datadef:
                            datadef_name = getattr(segment.datadef, 'name', str(segment.datadef))
                            print(f"    DataDef: {datadef_name}")
            
            # Count mob types
            source_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'SourceMob']
            comp_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'CompositionMob']
            master_mobs = [mob for mob in f.content.mobs if type(mob).__name__ == 'MasterMob']
            
            print(f"\n📊 Summary:")
            print(f"   SourceMobs: {len(source_mobs)}")
            print(f"   CompositionMobs: {len(comp_mobs)}")
            print(f"   MasterMobs: {len(master_mobs)}")
            
            if len(source_mobs) == 1 and len(comp_mobs) == 0 and len(master_mobs) == 0:
                print(f"\n💡 Single SourceMob structure - might import as Master Clip!")
                print(f"   SourceMobs can sometimes be treated as Master Clips by Avid")
            
    except Exception as e:
        print(f"Error analyzing AAF: {e}")

if __name__ == "__main__":
    # Test the Hybrid approach
    wav_file = "/Users/jasonbrodkey/Documents/SFX/Test Source Files/wavTest/RockScrape 6040_75_2.wav"
    output_aaf = "/Users/jasonbrodkey/Desktop/TEST_HYBRID_MASTER.aaf"
    
    result = create_hybrid_master_aaf(wav_file, output_aaf)
    if result:
        analyze_hybrid_aaf(result)
        print(f"\n🎯 TEST THIS AAF IN AVID:")
        print(f"   File: {result}")
        print(f"   Single SourceMob with Master Clip hints")
        print(f"   May import as Master Clip instead of subclip")
    else:
        print(f"\n❌ Hybrid approach failed")