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

if(NOT DEFINED AAFSDK_ROOT)
    message(FATAL_ERROR "'AAFSDK_ROOT' must be set. Run a build from the top-level CMakeLists.txt script.")
endif()

# MSVC: ./AAFWinSDK/<vsXX>/Utilities/aafviewer/aaf2dot/<Win32|x64>/<Debug|Release>/
set(TARGET_DIR "${AAFSDK_TARGET_DIR}/Utilities/aafviewer/aaf2dot")

add_executable(aaf2dot
    aaf2dot.cpp
    AAFDotInstanceMapper.cpp
    AAFDotInstanceMapper.h
    AxBaseObjIterExt.cpp
    AxBaseObjIterExt.h
    aaf2dot_DotEdge.cpp
    DotEdge_aaf2dot.h
    aaf2dot_DotElement.cpp
    DotElement_aaf2dot.h
    aaf2dot_DotFactory.cpp
    DotFactory_aaf2dot.h
    aaf2dot_DotGraph.cpp
    DotGraph_aaf2dot.h
    aaf2dot_DotRecordNode.cpp
    DotRecordNode_aaf2dot.h
    aaf2dot_DotSubGraph.cpp
    DotSubGraph_aaf2dot.h
    aaf2dot_DotThingWithID.cpp
    DotThingWithID_aaf2dot.h
    InstanceMapperProfile.cpp
    InstanceMapperProfile.h
    aaf2dot_Logging.cpp
    Logging_aaf2dot.h
    MapperSettings.cpp
    MapperSettings.h
    aaf2dot_Utilities.cpp
    Utilities_aaf2dot.h
)

target_include_directories(aaf2dot PRIVATE
    ${AAFSDK_ROOT}/Utilities/aafviewer/src/aaf2dot
)

target_link_libraries(aaf2dot PRIVATE
    AAFIID
    AAFLIB
    axLib
)

set_target_properties(aaf2dot PROPERTIES
    VERSION ${AAFSDK_VERSION_STRING}
)

set_target_properties(aaf2dot PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${TARGET_DIR}
    RUNTIME_OUTPUT_DIRECTORY_DEBUG ${TARGET_DIR}
    RUNTIME_OUTPUT_DIRECTORY_RELEASE ${TARGET_DIR}
)
