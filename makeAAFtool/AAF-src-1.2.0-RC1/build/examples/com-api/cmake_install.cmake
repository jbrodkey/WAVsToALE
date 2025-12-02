# Install script for directory: /Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/examples/com-api

# Set the install prefix
if(NOT DEFINED CMAKE_INSTALL_PREFIX)
  set(CMAKE_INSTALL_PREFIX "/usr/local")
endif()
string(REGEX REPLACE "/$" "" CMAKE_INSTALL_PREFIX "${CMAKE_INSTALL_PREFIX}")

# Set the install configuration name.
if(NOT DEFINED CMAKE_INSTALL_CONFIG_NAME)
  if(BUILD_TYPE)
    string(REGEX REPLACE "^[^A-Za-z0-9_]+" ""
           CMAKE_INSTALL_CONFIG_NAME "${BUILD_TYPE}")
  else()
    set(CMAKE_INSTALL_CONFIG_NAME "")
  endif()
  message(STATUS "Install configuration: \"${CMAKE_INSTALL_CONFIG_NAME}\"")
endif()

# Set the component getting installed.
if(NOT CMAKE_INSTALL_COMPONENT)
  if(COMPONENT)
    message(STATUS "Install component: \"${COMPONENT}\"")
    set(CMAKE_INSTALL_COMPONENT "${COMPONENT}")
  else()
    set(CMAKE_INSTALL_COMPONENT)
  endif()
endif()

# Is this installation the result of a crosscompile?
if(NOT DEFINED CMAKE_CROSSCOMPILING)
  set(CMAKE_CROSSCOMPILING "FALSE")
endif()

# Set path to fallback-tool for dependency-resolution.
if(NOT DEFINED CMAKE_OBJDUMP)
  set(CMAKE_OBJDUMP "/usr/bin/objdump")
endif()

if(NOT CMAKE_INSTALL_LOCAL_ONLY)
  # Include the install script for each subdirectory.
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/comClientTest/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComCutsOnlyTest/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComEssenceDataTest/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComExtension/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComExtension/ComPersonnelExtension/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComPropDirectAccess/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ComPropDirectDump/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportAS05Effects/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportAudioExample/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportDV/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportJPEG/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportPCM/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportSimpleComposition/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ExportVC3/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ImportAudioExample/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ImportDV/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ImportJPEG/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ImportPCM/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/ImportVC3/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/InfoDumper/cmake_install.cmake")
  include("/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/MetadataExample/cmake_install.cmake")

endif()

string(REPLACE ";" "\n" CMAKE_INSTALL_MANIFEST_CONTENT
       "${CMAKE_INSTALL_MANIFEST_FILES}")
if(CMAKE_INSTALL_LOCAL_ONLY)
  file(WRITE "/Users/jasonbrodkey/Documents/SFX/pythonScripts/makeAAFtool/AAF-src-1.2.0-RC1/build/examples/com-api/install_local_manifest.txt"
     "${CMAKE_INSTALL_MANIFEST_CONTENT}")
endif()
