###############################################################################
#
# $Id$ $Name$
#
# The contents of this file are subject to the AAF SDK Public Source
# License Agreement Version 2.0 (the "License"); You may not use this
# file except in compliance with the License.  The License is available
# in AAFSDKPSL.TXT, or you may obtain a copy of the License from the
# Advanced Media Workflow Association, Inc., or its successor.
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied.  See
# the License for the specific language governing rights and limitations
# under the License.  Refer to Section 3.3 of the License for proper use
# of this Exhibit.
#
# WARNING:  Please contact the Advanced Media Workflow Association,
# Inc., for more information about any additional licenses to
# intellectual property covering the AAF Standard that may be required
# to create and distribute AAF compliant products.
# (http://www.amwa.tv/policies).
#
# Copyright Notices:
# The Original Code of this file is Copyright 1998-2012, licensor of the
# Advanced Media Workflow Association.  All rights reserved.
#
# The Initial Developer of the Original Code of this file and the
# licensor of the Advanced Media Workflow Association is
# Avid Technology.
# All rights reserved.
#
###############################################################################

cmake_minimum_required(VERSION 3.10 FATAL_ERROR)

project(MakeSDK LANGUAGES CXX C)

add_subdirectory(aafiid)
add_subdirectory(aaflib)
add_subdirectory(expat)
add_subdirectory(libjpeg)
add_subdirectory(plugins)
add_subdirectory(src/com-api)
add_subdirectory(src/impl)
add_subdirectory(src/OM)

# Copy AAF.h, AAFTypes.h, AAF_i.c, and AAFPlugin.h from ref-api and com-api
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAF_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAF.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFTypes_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFTypes.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAF_i_refapi.c ${CMAKE_CURRENT_LIST_DIR}/include/AAF_i.c COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFPlugin_i_refapi.c ${CMAKE_CURRENT_LIST_DIR}/include/AAFPlugin_i.c COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFPrivate_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFPrivate.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFPrivate_i_refapi.c ${CMAKE_CURRENT_LIST_DIR}/include/AAFPrivate_i.c COPYONLY)

# Copy REFAPI files from subdirs to include/
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAF_comapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAF_comapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAF_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAF_refapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAFPlugin_comapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFPlugin_comapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFPlugin_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFPlugin_refapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAFPluginTypes_comapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFPluginTypes_comapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFPluginTypes_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFPluginTypes_refapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAFTypes_comapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFTypes_comapi.h COPYONLY)
configure_file(${CMAKE_CURRENT_LIST_DIR}/include/ref-api/AAFTypes_refapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAFTypes_refapi.h COPYONLY)

add_custom_target(MakeSDK ALL COMMENT "Building MakeSDK...")

add_custom_command(
    OUTPUT ${CMAKE_CURRENT_LIST_DIR}/include/AAF.h
    COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAF_comapi.h ${CMAKE_CURRENT_LIST_DIR}/include/AAF.h
    DEPENDS ${CMAKE_CURRENT_LIST_DIR}/include/com-api/AAF_comapi.h
    COMMENT "Copying AAF_comapi.h to AAF.h"
)

set(INCLUDES
    AAF.h
    AAF_i.c
    AAFAudioLabels.h
    AAFClassDefUIDs.h
    AAFCodecDefs.h
    AAFCOMPlatform.h
    AAFCOMPlatformTypes.h
    AAFContainerDefs.h
    AAFDataDefs.h
    AAFDefUIDs.h
    AAFEssenceFormats.h
    AAFExtEnum.h
    AAFFileKinds.h
    AAFFileMode.h
    AAFInterpolatorDefs.h
    AAFMetaDictionary_main.h
    AAFOperationCategories.h
    AAFOperationDefs.h
    AAFParameterDefs.h
    AAFPlatform.h
    AAFPluginDefs.h
    AAFPropertyDefs.h
    AAFPropertyIDs.h
    AAFResult.h
    AAFSmartPointer.h 
    AAFSmartPointer2.h
    AAFSmartPointerBase.h
    AAFStoredObjectIDs.h
    AAFTypeDefUIDs.h
)

set(REFAPI
    AAF_comapi.h
    AAF_refapi.h
    AAFPlugin_i.c
    AAFPlugin_comapi.h
    AAFPlugin_refapi.h
    AAFPluginTypes_comapi.h
    AAFPluginTypes_refapi.h
    AAFTypes_comapi.h
    AAFTypes_refapi.h
)

set(UTILITIES_INCLUDES
    CAAFBuiltinDefs.h
)

target_copy_files(MakeSDK
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${AAFSDK_SHARED_DIR}/include"
    "${INCLUDES}"
)

target_copy_files(MakeSDK
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${AAFSDK_SHARED_DIR}/include"
    "${REFAPI}"
)

target_copy_files(MakeSDK
    "${AAFSDK_ROOT}/Utilities/Include"
    "${AAFSDK_SHARED_DIR}/include"
    "${UTILITIES_INCLUDES}"
)

add_dependencies(MakeSDK
    AAFBasicInterpolators
    AAFIID
    AAFLIB
    AAFStandardCodecs
    comapi
    HeaderGen
)
