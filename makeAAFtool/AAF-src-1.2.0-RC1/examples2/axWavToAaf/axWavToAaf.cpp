//=---------------------------------------------------------------------=
//
// axWavToAaf.cpp
//
// Simple example to wrap a WAV file in an AAF container.
//
//=---------------------------------------------------------------------=

#include <AxInit.h>
#include <AxFile.h>
#include <AxHeader.h>
#include <AxDictionary.h>
#include <AxContentStorage.h>
#include <AxMob.h>
#include <AxEssence.h>
#include <AxDefObject.h>
#include <AxUtil.h>
#include <AxMobSlot.h>
#include <AxComponent.h>
#include <AxIterator.h>

#include <AAF.h>
#include <AAFEssenceFormats.h>
#include <AAFStoredObjectIDs.h>
#include <AAFTypeDefUIDs.h>
#include <AAFDataDefs.h>
#include <AAFCodecDefs.h>
#include <AAFContainerDefs.h>
#include <AAFFileKinds.h>
#include <AAFDefUIDs.h>

#include <iostream>
#include <fstream>
#include <vector>
#include <cstdint>
#include <string>

void throwUsage()
{
    std::wcout << L"Usage: axWavToAaf-1.2.0 <input.wav> <output.aaf>" << std::endl;
    throw std::runtime_error("Invalid arguments");
}

int main(int argc, char* argv[])
{
    if (argc != 3) {
        throwUsage();
    }

    const char* wavFile = argv[1];
    const char* aafFile = argv[2];

    try {
        AxInit initObj;

        AxString aafFileName(AxStringUtil::mbtowc(aafFile));

        // Set up product identification
        aafProductIdentification_t productInfo;
        productInfo.companyName = L"Example";
        productInfo.productName = L"axWavToAaf";
        aafProductVersion_t version = {1, 2, 0, 0, kAAFVersionUnknown};
        productInfo.productVersion = &version;
        productInfo.productVersionString = L"1.2.0";
        productInfo.productID = UnitTestProductID;
        productInfo.platform = L"macOS";

        IAAFFileSP spIaafFile;
        CHECK_HRESULT( AAFFileOpenNewModify( aafFileName.c_str(), 0, &productInfo, &spIaafFile ) );

        AxFile axFile(spIaafFile);

        AxHeader axHeader(axFile.getHeader());
        AxDictionary axDictionary(axHeader.GetDictionary());
        AxContentStorage axContentStorage(axHeader.GetContentStorage());

        // Create a master mob
        AxDataDef axSoundDef(axDictionary.LookupDataDef(kAAFDataDef_Sound));
        AxMasterMob axMasterMob( AxCreateInstance<IAAFMasterMob>( axDictionary ) );
        axMasterMob.Initialize();
        axMasterMob.SetName(L"MasterMob");
        axHeader.AddMob( axMasterMob );

        // Read WAV file
        std::ifstream wavStream(wavFile, std::ios::binary | std::ios::ate);
        if (!wavStream) {
            throw std::runtime_error("Cannot open WAV file");
        }
        std::streamsize wavSize = wavStream.tellg();
        wavStream.seekg(0, std::ios::beg);
        std::vector<char> wavData(wavSize);
        if (!wavStream.read(wavData.data(), wavSize)) {
            throw std::runtime_error("Cannot read WAV file");
        }

        // Parse WAV header
        if (wavSize < 44 || std::string(wavData.data(), 4) != "RIFF" || std::string(wavData.data() + 8, 4) != "WAVE") {
            throw std::runtime_error("Invalid WAV file format");
        }

        // Find the fmt chunk
        size_t pos = 12;
        uint16_t audioFormat = 0;
        uint16_t numChannels = 0;
        uint32_t sampleRate = 0;
        uint32_t byteRate = 0;
        uint16_t blockAlign = 0;
        uint16_t bitsPerSample = 0;

        while (pos + 8 < wavSize) {
            std::string chunkId(wavData.data() + pos, 4);
            uint32_t chunkSize = *reinterpret_cast<uint32_t*>(wavData.data() + pos + 4);
            pos += 8;

            std::cout << "Found chunk: " << chunkId << " size: " << chunkSize << " at pos: " << (pos - 8) << std::endl;

            if (chunkId == "fmt ") {
                if (chunkSize >= 16) {
                    audioFormat = *reinterpret_cast<uint16_t*>(wavData.data() + pos);
                    numChannels = *reinterpret_cast<uint16_t*>(wavData.data() + pos + 2);
                    sampleRate = *reinterpret_cast<uint32_t*>(wavData.data() + pos + 4);
                    byteRate = *reinterpret_cast<uint32_t*>(wavData.data() + pos + 8);
                    blockAlign = *reinterpret_cast<uint16_t*>(wavData.data() + pos + 12);
                    bitsPerSample = *reinterpret_cast<uint16_t*>(wavData.data() + pos + 14);
                    std::cout << "Format: " << audioFormat << " channels: " << numChannels << " rate: " << sampleRate << " bits: " << bitsPerSample << std::endl;
                }
                pos += chunkSize;
            } else if (chunkId == "data") {
                // Found data chunk - this is the audio data
                const char* audioData = wavData.data() + pos;
                size_t audioDataSize = chunkSize;
                
                std::cout << "Data chunk found at pos " << pos << " with size " << audioDataSize << std::endl;
                
                // Create essence
                aafRational_t editRate = {static_cast<aafInt32>(sampleRate), 1};
                aafRational_t sampleRateRational = {static_cast<aafInt32>(sampleRate), 1};

                IAAFLocatorSP nullLocator;
                AxEssenceAccess axEssenceAccess(
                    axMasterMob.CreateEssence(
                        1,
                        axSoundDef,
                        kAAFCodecWAVE,
                        editRate,
                        sampleRateRational,
                        kAAFCompressionDisable,
                        nullLocator,
                        ContainerAAFXML));

                // Set the essence format specifiers
                AxEssenceFormat axEssenceFormat( axEssenceAccess.GetEmptyFileFormat() );
                aafUInt32 sampleBits = bitsPerSample;
                axEssenceFormat.AddFormatSpecifier( kAAFAudioSampleBits, sizeof(sampleBits), reinterpret_cast<aafUInt8*>(&sampleBits) );
                axEssenceAccess.PutFileFormat( axEssenceFormat );

                // Calculate number of samples
                aafUInt32 samplesPerFrame = numChannels * (bitsPerSample / 8);
                aafUInt32 numSamples = audioDataSize / samplesPerFrame;

                std::cout << "Writing " << numSamples << " samples (" << audioDataSize << " bytes)" << std::endl;

                // Write the audio data in chunks to avoid issues
                const size_t CHUNK_SIZE = 65536; // 64KB chunks
                size_t bytesWritten = 0;
                aafUInt32 samplesWritten = 0;
                
                while (bytesWritten < audioDataSize) {
                    size_t chunkBytes = std::min(CHUNK_SIZE, audioDataSize - bytesWritten);
                    aafUInt32 chunkSamples = chunkBytes / samplesPerFrame;
                    
                    AxEssenceAccess::WriteResult result = axEssenceAccess.WriteSamples(
                        chunkSamples, 
                        chunkBytes, 
                        reinterpret_cast<aafDataBuffer_t>(const_cast<char*>(audioData + bytesWritten))
                    );
                    
                    bytesWritten += result.bytesWritten;
                    samplesWritten += result.samplesWritten;
                    
                    std::cout << "Wrote " << result.samplesWritten << " samples (" << result.bytesWritten << " bytes), total: " << samplesWritten << "/" << numSamples << std::endl;
                    
                    if (result.samplesWritten == 0) {
                        std::cout << "Write failed or incomplete" << std::endl;
                        break;
                    }
                }

                // Set the length of the source clip
                AxMobSlot axMobSlot(axMasterMob.LookupSlot(1));
                AxSegment axSegment(axMobSlot.GetSegment());
                axSegment.SetLength(numSamples);

                std::cout << "Set component length to " << numSamples << " samples" << std::endl;

                // Complete the write
                axEssenceAccess.CompleteWrite();

                break; // Done processing
            } else {
                // Unknown chunk, skip it
                pos += chunkSize;
            }
        }

        // Save and close
        axFile.Save();
        axFile.Close();

        std::wcout << L"Successfully created AAF file: " << aafFileName << std::endl;

    } catch (const AxEx& ex) {
        std::wcout << L"AAF Error: " << ex.what() << std::endl;
        return 1;
    } catch (const std::exception& ex) {
        std::wcout << L"Error: " << AxStringUtil::mbtowc(ex.what()) << std::endl;
        return 1;
    }

    return 0;
}